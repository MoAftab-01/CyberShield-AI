"""Bounded offline ingestion with pinned artifact approval and version history."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
from pathlib import Path
import re
import unicodedata
from typing import Protocol

from .models import EvidenceChunk, Section, SourceRecord
from .registry import SourceRegistry

LOGGER = logging.getLogger(__name__)
FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "evaluation" / "source_foundation"
MAX_ARTIFACT_BYTES = 512000


def digest(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def normalize(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected source text.")
    value = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n")).strip()
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise ValueError("Source text contains invalid control characters.")
    return value


def timestamp(value):
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise ValueError("Invalid source timestamp.") from None
    # NVD's documented API timestamps are UTC, including its offset-free examples.
    return parsed.replace(tzinfo=timezone.utc) if parsed.utcoffset() is None else parsed.astimezone(timezone.utc)


class SourceAdapter(Protocol):
    def parse(self, payload: dict) -> list[dict]: ...


class NvdAdapter:
    """NVD CVE API 2.0 JSON adapter; no HTTP client or fetch capability."""
    def parse(self, payload):
        if not isinstance(payload, dict) or not isinstance(payload.get("vulnerabilities"), list):
            raise ValueError("Expected an NVD CVE API 2.0 response.")
        if len(payload["vulnerabilities"]) > 100:
            raise ValueError("Offline batch exceeds the reviewed record limit.")
        result = []
        for wrapper in payload["vulnerabilities"]:
            record = wrapper.get("cve", {})
            identifier = record.get("id", "")
            if not isinstance(identifier, str) or not re.fullmatch(r"CVE-[0-9]{4}-[0-9]{4,}", identifier):
                raise ValueError("Invalid CVE identifier.")
            sections = []
            descriptions = record.get("descriptions", [])
            for description in descriptions:
                if description.get("lang") == "en" and normalize(description.get("value", "")):
                    sections.append(Section(heading="Description (en)", text=normalize(description["value"])))
                    break
            identifiers = [("cve", identifier)]
            metrics = record.get("metrics", {}).get("cvssMetricV31", [])
            # Prefer NVD's primary assessment; do not merge conflicting providers.
            metrics = sorted(metrics, key=lambda item: (item.get("source") != "nvd@nist.gov", item.get("type") != "Primary"))
            if metrics:
                cvss = metrics[0].get("cvssData", {})
                score = cvss.get("baseScore")
                severity = cvss.get("baseSeverity")
                if type(score) not in (int, float) or not 0 <= score <= 10 or severity not in {"NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
                    raise ValueError("Invalid CVSS v3.1 assessment.")
                sections.append(Section(heading="CVSS v3.1 assessment", text=f"{identifier} has CVSS v3.1 base score {score:g} ({severity})."))
                identifiers.extend((("cvss_version", "3.1"), ("severity", severity)))
            state = "withdrawn" if record.get("vulnStatus") == "Rejected" else "active"
            if not sections and state == "active":
                raise ValueError("An active record requires supporting content.")
            result.append(dict(record_id=identifier, title=identifier, document_type="CVE record",
                published_at=timestamp(record.get("published")), modified_at=timestamp(record.get("lastModified")),
                sections=tuple(sections), identifiers=tuple(identifiers), state=state))
        return result


class ReferenceFixtureAdapter:
    """Original synthetic references for offline evaluation, never official text."""
    def parse(self, payload):
        result = []
        if not isinstance(payload, dict) or not isinstance(payload.get("records"), list) or len(payload["records"]) > 100:
            raise ValueError("Expected a bounded synthetic reference batch.")
        for item in payload["records"]:
            result.append(dict(record_id=item["record_id"], title=item["title"], document_type="Synthetic reference",
                published_at=timestamp(item.get("published_at")), modified_at=timestamp(item["modified_at"]),
                sections=tuple(Section(heading=normalize(section["heading"]), text=normalize(section["text"])) for section in item["sections"]),
                identifiers=tuple(sorted(item.get("identifiers", {}).items())), state=item.get("state", "active")))
        return result


class Catalog:
    """In-memory catalog. Public admission needs operator-approved artifact hashes.

    A custom manifest is privileged application configuration, never upload data.
    There is no endpoint accepting manifests, trust flags, or public admission.
    """
    def __init__(self, manifest_path: Path | None = None):
        manifest = json.loads((manifest_path or FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8"))
        self._approved = {item["artifact_id"]: dict(item) for item in manifest["artifacts"]}
        if len(self._approved) != len(manifest["artifacts"]):
            raise ValueError("Duplicate artifact approval.")
        self.registry = SourceRegistry()
        self._records = {}
        self._current = {}
        self._chunks = {}

    def ingest_artifact(self, artifact_id: str, path: Path, *, retrieved_at: datetime):
        approval = self._approved.get(artifact_id)
        if approval is None:
            raise ValueError("Artifact is not approved for public ingestion.")
        with path.open("rb") as source:
            raw = source.read(MAX_ARTIFACT_BYTES + 1)
        if len(raw) > MAX_ARTIFACT_BYTES or sha256(raw).hexdigest() != approval["sha256"]:
            raise ValueError("Artifact integrity check failed.")
        definition = self.registry.get(approval["source_id"])
        adapters = {"nvd": NvdAdapter, "reference-fixture": ReferenceFixtureAdapter}
        if approval["adapter"] == "nvd" and definition.source_id != "nvd":
            raise ValueError("NVD adapter requires the registered NVD source.")
        if approval["adapter"] == "reference-fixture" and (definition.source_id != "fixture-reference" or approval["trust"] != "synthetic_fixture"):
            raise ValueError("Synthetic fixtures cannot claim official authority.")
        if approval["trust"] not in {"official_snapshot", "synthetic_fixture"}:
            raise ValueError("Invalid approved provenance class.")
        try:
            payload = json.loads(raw)
            adapter = adapters[approval["adapter"]]()
            parsed = adapter.parse(payload)
        except (KeyError, TypeError, AttributeError, json.JSONDecodeError):
            raise ValueError("Invalid source artifact structure.") from None
        records = []
        for item in parsed:
            canonical = f"https://nvd.nist.gov/vuln/detail/{item['record_id']}" if approval["trust"] == "official_snapshot" and definition.source_id == "nvd" else None
            records.append(self._record(source_id=definition.source_id, trust=approval["trust"], scope="public", owner_id=None,
                canonical_url=canonical, artifact_hash=approval["sha256"], retrieved_at=retrieved_at,
                licensing_notes=approval.get("licensing_notes", definition.licensing_notes), **item))
        # Validate the entire batch before changing catalog state.
        pending = dict(self._current)
        for record in records:
            self._check_update(record, pending)
            pending[record.document_id] = record
        # Chunk everything first: a failed splitter cannot partially admit a batch.
        prepared = [(record, self._chunk(record) if record.state == "active" else ()) for record in records]
        outcomes = [self._admit(record, chunks) for record, chunks in prepared]
        LOGGER.info("source_ingestion source_id=%s records=%d", definition.source_id, len(records))
        return tuple(outcomes)

    def ingest_private(self, *, record_id: str, title: str, text: str, owner_id: int, retrieved_at: datetime):
        if type(owner_id) is not int or owner_id <= 0:
            raise ValueError("A valid private owner is required.")
        return self._admit(self._record(source_id="private-upload", record_id=record_id, title=title,
            document_type="Private upload", trust="private_upload", scope="private", owner_id=owner_id,
            canonical_url=None, artifact_hash=digest(text), retrieved_at=retrieved_at,
            licensing_notes="Private user material; no public redistribution or trust promotion.",
            published_at=None, modified_at=retrieved_at, sections=(Section(heading="Private content", text=normalize(text)),), identifiers=(), state="active"))

    def _record(self, **values):
        for field in ("record_id", "title", "document_type"):
            values[field] = normalize(values[field])
        sections = values["sections"]
        values["document_id"] = "doc-" + digest([values["source_id"], values["record_id"], values["scope"], values["owner_id"]])
        values["content_hash"] = digest([(section.heading, section.text) for section in sections])
        values["version"] = "v-" + digest([values["title"], values["content_hash"], str(values["published_at"]), str(values["modified_at"]), values["state"], values["identifiers"], values["trust"], values["canonical_url"], values["document_type"], values["licensing_notes"]])
        return SourceRecord(**values)

    def _check_update(self, record, current):
        previous = current.get(record.document_id)
        if previous and previous.version != record.version:
            if previous.modified_at is None or record.modified_at is None or record.modified_at <= previous.modified_at:
                raise ValueError("Out-of-order or conflicting source version; operator review required.")

    def _admit(self, record, prepared_chunks=None):
        if getattr(self, "_read_only", False):
            raise ValueError("Historical source snapshots are read-only.")
        self._check_update(record, self._current)
        previous = self._current.get(record.document_id)
        if previous and previous.version == record.version:
            return previous
        chunks = prepared_chunks if prepared_chunks is not None else (self._chunk(record) if record.state == "active" else ())
        self._records[(record.document_id, record.version)] = record
        self._current[record.document_id] = record
        self._chunks.update({chunk.chunk_id: chunk for chunk in chunks})
        return record

    @staticmethod
    def _chunk(record):
        from langchain_core.documents import Document
        from app.rag.chunker import DocumentChunker
        chunks = []
        for section_number, section in enumerate(record.sections):
            pieces = DocumentChunker.chunk_documents([Document(page_content=section.text,
                metadata={"filename":record.document_id,"page":section_number})], chunk_size=600, chunk_overlap=100)
            for ordinal, piece in enumerate(pieces):
                text_hash = digest(piece.page_content)
                chunks.append(EvidenceChunk(chunk_id="chunk-"+digest([record.document_id, record.version, section_number, ordinal, text_hash]),
                    document_id=record.document_id, source_version=record.version, section=section.heading,
                    ordinal=len(chunks), excerpt=piece.page_content, text_hash=text_hash))
        return tuple(chunks)

    def snapshot(self, source_as_of: datetime):
        """Read-only view of the latest KNOWN source versions at a UTC cutoff.

        This is source-modification-time selection over reviewed snapshots,
        not a claim that our system possessed these records at that date.
        No history is inferred from a current record's publication date.
        """
        if not isinstance(source_as_of, datetime) or source_as_of.utcoffset() is None:
            raise ValueError("An explicit timezone-aware source cutoff is required.")
        view = object.__new__(Catalog)
        view.registry = self.registry
        view._approved = {}
        view._records = dict(self._records)
        view._chunks = dict(self._chunks)
        view._current = {}
        view._read_only = True
        for record in self._records.values():
            # Unknown modification times cannot establish historical applicability.
            if record.modified_at is None or record.modified_at > source_as_of:
                continue
            prior = view._current.get(record.document_id)
            if prior is None or prior.modified_at < record.modified_at:
                view._current[record.document_id] = record
        view._chunks = {key: chunk for key, chunk in view._chunks.items()
                        if chunk.document_id in view._current}
        return view

    def current_records(self):
        return tuple(self._current.values())

    def authorized_chunks(self, user_id):
        return tuple(chunk for chunk in self._chunks.values() if self.resolve(chunk.chunk_id, user_id) is not None)

    def resolve(self, chunk_id, user_id):
        chunk = self._chunks.get(chunk_id)
        if chunk is None:
            return None
        record = self._current[chunk.document_id]
        if record.state != "active" or record.version != chunk.source_version:
            return None
        if record.scope == "private" and (type(user_id) is not int or user_id <= 0 or record.owner_id != user_id):
            return None
        return record, chunk

    def documents(self, user_id):
        from langchain_core.documents import Document
        result = []
        for chunk in self.authorized_chunks(user_id):
            record, _ = self.resolve(chunk.chunk_id, user_id)
            metadata = dict(scope="knowledge_base" if record.scope == "public" else "user_upload",
                filename=record.document_id, page=chunk.ordinal, source_folder=record.source_id if record.scope == "public" else "uploads",
                chunk_id=chunk.chunk_id, document_id=record.document_id, source_id=record.source_id,
                source_version=record.version, content_hash=record.content_hash, text_hash=chunk.text_hash)
            if record.scope == "private":
                metadata["user_id"] = record.owner_id
            result.append(Document(page_content=chunk.excerpt, metadata=metadata))
        return tuple(result)

"""Bind shared retrieval to verified bundled bytes or the caller's upload.

No new index: the existing FAISS/BM25/RRF/MMR pipeline locates pages. Canonical
complete PDF blocks are read from their source bytes before quotation checking.
"""
from datetime import datetime, timezone
from functools import lru_cache
from hashlib import sha256
import json
from io import BytesIO
from pathlib import Path
import re
import zipfile

import fitz
from app.knowledge.ingestion import Catalog, normalize
from app.knowledge.models import Section
from app.knowledge.registry import SourceRegistry
from app.rag.loader import DASH_NORMALIZATION, SPACE_NORMALIZATION
from app.rag.retriever import HybridRetriever

BACKEND = Path(__file__).resolve().parents[2]
PUBLIC_ROOT = BACKEND / "knowledge_base"
SOURCE_MANIFEST = BACKEND / "knowledge_sources.json"
MAX_FILE_BYTES = 20 * 1024 * 1024


def empty_catalog():
    catalog = Catalog.__new__(Catalog)
    catalog.registry = SourceRegistry()
    catalog._approved, catalog._records, catalog._current, catalog._chunks = {}, {}, {}, {}
    return catalog


@lru_cache(maxsize=32)
def _checked_hash(path, modified, size, expected):
    if not 0 < size <= MAX_FILE_BYTES:
        raise ValueError("Source size is outside the reviewed bound.")
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    if digest.hexdigest() != expected:
        raise ValueError("Bundled source integrity mismatch.")
    return expected


def public_sources():
    raw = SOURCE_MANIFEST.read_bytes()
    if len(raw) > 32000:
        raise ValueError("Source manifest too large.")
    manifest = json.loads(raw)
    items = manifest["sources"]
    if manifest.get("format_version") != 1 or not isinstance(items, list) or len(items) > 16:
        raise ValueError("Invalid bundled source registry.")
    return items


def _public_source(filename):
    matches = [item for item in public_sources() if Path(item["path"]).name == filename]
    if len(matches) != 1:
        raise ValueError("Unapproved or ambiguous public source.")
    item = matches[0]
    path = (PUBLIC_ROOT / item["path"]).resolve(strict=True)
    if not path.is_relative_to(PUBLIC_ROOT.resolve()) or path.is_symlink():
        raise ValueError("Source outside approved root.")
    stat = path.stat()
    _checked_hash(str(path), stat.st_mtime_ns, stat.st_size, item["sha256"])
    return path, item


def _fold(text):
    return re.sub(r"\s+", " ", normalize(text)).strip()


def _source_page(path, page, public, expected_hash):
    with path.open("rb") as stream:
        raw = stream.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES or sha256(raw).hexdigest() != expected_hash:
        raise ValueError("Source bytes changed during admission.")
    if path.suffix.lower() == ".pdf":
        with fitz.open(stream=raw, filetype="pdf") as pdf:
            if not 0 <= page < len(pdf):
                raise ValueError("Invalid source page.")
            full = pdf[page].get_text()
            blocks = [block[4] for block in pdf[page].get_text("blocks") if block[6] == 0]
    else:
        if page != 0:
            raise ValueError("Invalid source page.")
        if path.suffix.lower() == ".txt":
            full = raw.decode("utf-8")
            if len(full) > 512000:
                raise ValueError("Upload text exceeds quotation bound.")
        elif path.suffix.lower() == ".docx":
            with zipfile.ZipFile(BytesIO(raw)) as archive:
                if sum(info.file_size for info in archive.infolist()) > 2_000_000:
                    raise ValueError("Expanded document exceeds quotation bound.")
            from docx import Document as WordDocument
            full = "\n".join(paragraph.text for paragraph in WordDocument(BytesIO(raw)).paragraphs)
        else:
            raise ValueError("Unsupported source type.")
        blocks = re.split(r"\n\s*\n|\n", full)
    if public:
        clean = lambda text: SPACE_NORMALIZATION.sub(" ", DASH_NORMALIZATION.sub("-", text))
        full, blocks = clean(full), [clean(block) for block in blocks]
    return full, [normalize(block) for block in blocks if 40 <= len(normalize(block)) <= 1900][:24]


def retrieve(question, actor):
    found, metrics = HybridRetriever.search_with_metrics(question, top_k=8, user_id=actor)
    catalog = empty_catalog()
    if not found:
        if "index" in str(metrics.get("reason", "")).lower():
            metrics = {**metrics, "status": "missing_index"}
        return catalog, (), metrics
    seen = set()
    for document in found:
        if not HybridRetriever._is_visible(document, actor):
            continue
        metadata = document.metadata
        filename, page = metadata.get("filename"), metadata.get("page")
        if not isinstance(filename, str) or Path(filename).name != filename or "/" in filename or "\\" in filename or type(page) is not int:
            continue
        public = HybridRetriever._scope_of(document) == "knowledge_base"
        try:
            if public:
                path, item = _public_source(filename)
                identity, source_id = item["sha256"], item["source_id"]
            else:
                if type(metadata.get("user_id")) is not int or metadata["user_id"] != actor:
                    continue
                from app.services.document_service import DocumentService
                upload_root = DocumentService.UPLOAD_DIR.resolve()
                raw_owner_root = upload_root / ("user_" + str(actor))
                if raw_owner_root.is_symlink():
                    continue
                owner_root = raw_owner_root.resolve()
                if not owner_root.is_relative_to(upload_root):
                    continue
                path = (owner_root / filename).resolve(strict=True)
                if not path.is_relative_to(owner_root) or path.is_symlink() or not 0 < path.stat().st_size <= MAX_FILE_BYTES:
                    continue
                identity = sha256(path.read_bytes()).hexdigest()
                item, source_id = {"title": filename, "canonical_url": None}, "private-upload"
            key = (identity, page, public)
            if key in seen:
                continue
            full, blocks = _source_page(path, page, public, identity)
            # Metadata alone never upgrades stale, fabricated, or foreign chunks.
            if _fold(document.page_content) not in _fold(full):
                continue
            seen.add(key)
            if not blocks:
                continue
            definition = catalog.registry.get(source_id) if public else None
            record = catalog._record(source_id=source_id, record_id=identity + ":page:" + str(page + 1),
                title=item["title"] + " (page " + str(page + 1) + ")", document_type="Bundled reference" if public else "Private upload",
                canonical_url=item["canonical_url"], published_at=None, modified_at=None,
                retrieved_at=datetime.now(timezone.utc), artifact_hash=identity,
                licensing_notes=definition.licensing_notes if public else "Private user material; no public trust promotion.",
                trust="official_snapshot" if public else "private_upload", scope="public" if public else "private",
                owner_id=None if public else actor, state="active", identifiers=(),
                sections=tuple(Section(heading="Page " + str(page + 1) + ", block " + str(i + 1), text=text) for i, text in enumerate(blocks)))
            catalog._admit(record, catalog._chunk(record, chunk_size=2000))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    documents = catalog.documents(actor)
    return catalog, documents, {**metrics, "source_candidates": len(documents)}


def availability():
    from app.rag.faiss_store import FAISSStore
    from app.rag.bm25_store import BM25Store
    items = public_sources()
    available = 0
    for item in items:
        try:
            _public_source(Path(item["path"]).name)
            available += 1
        except (OSError, ValueError):
            pass
    return {"bundled_sources_expected": len(items), "bundled_sources_available": available,
            "shared_index_available": all(path.is_file() for path in (FAISSStore.INDEX_PATH, FAISSStore.META_PATH, BM25Store.INDEX_PATH, BM25Store.DOCS_PATH))}

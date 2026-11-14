"""Explicit operator-approved local artifacts. Never import benchmark corpora."""
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from .ingestion import Catalog, MAX_ARTIFACT_BYTES

MAX_MANIFEST_BYTES = 64000
MAX_ARTIFACTS = 16
MAX_CHUNKS = 256
MAX_TEXT_CHARACTERS = 128000


def load_catalog(manifest_path):
    if manifest_path is None:
        return None
    path = Path(manifest_path).resolve(strict=True)
    with path.open("rb") as source:
        raw = source.read(MAX_MANIFEST_BYTES + 1)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError("Catalog manifest bound exceeded.")
    manifest = json.loads(raw)
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) > MAX_ARTIFACTS:
        raise ValueError("Catalog artifact bound exceeded.")
    catalog = Catalog(path)
    for item in artifacts:
        # Manifest ownership, paths, hashes and dates are privileged server data.
        filename = item["filename"]
        if not isinstance(filename, str) or not filename or Path(filename).is_absolute():
            raise ValueError("Artifact requires a relative filename.")
        artifact = (path.parent / filename).resolve(strict=True)
        if not artifact.is_relative_to(path.parent):
            raise ValueError("Artifact escapes the approved directory.")
        retrieved_at = datetime.fromisoformat(item["retrieved_at"].replace("Z", "+00:00"))
        if retrieved_at.utcoffset() is None:
            raise ValueError("Artifact retrieval time requires a timezone.")
        if item["adapter"] == "private-text":
            if item["source_id"] != "private-upload" or item["trust"] != "private_upload":
                raise ValueError("Invalid private source classification.")
            with artifact.open("rb") as source:
                content = source.read(MAX_ARTIFACT_BYTES + 1)
            if len(content) > MAX_ARTIFACT_BYTES or sha256(content).hexdigest() != item["sha256"]:
                raise ValueError("Private artifact integrity check failed.")
            catalog.ingest_private(record_id=item["record_id"], title=item["title"],
                text=content.decode("utf-8"), owner_id=item["owner_id"], retrieved_at=retrieved_at)
        else:
            catalog.ingest_artifact(item["artifact_id"], artifact, retrieved_at=retrieved_at)
    return catalog


def authorized_documents(catalog, actor):
    """Canonical authorization and legacy visibility rules both precede indexing."""
    from app.rag.retriever import HybridRetriever
    from .evidence import collect_evidence

    documents = catalog.documents(actor)
    if len(documents) > MAX_CHUNKS or sum(len(d.page_content) for d in documents) > MAX_TEXT_CHARACTERS:
        raise ValueError("Authorized corpus bound exceeded.")
    visible = tuple(d for d in documents if HybridRetriever._is_visible(d, actor))
    collect_evidence(catalog, visible, actor)
    return visible

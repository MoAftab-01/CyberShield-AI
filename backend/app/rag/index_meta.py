"""Index provenance stamping.

An index is only valid for the encoder and chunking configuration that built
it. Searching a hash-built FAISS index with a sentence-transformer query vector
does not fail loudly - it returns plausible-looking garbage, because the
dimensions line up (both are 384-d) while the vector spaces are unrelated.

That failure mode is exactly the kind that reaches production silently: a
deploy changes the embedding backend, the old index is still on disk, and every
answer quietly degrades. To prevent it, every build writes a stamp describing
the configuration that produced it, and startup rebuilds the index when the
stamp does not match the running configuration.
"""

import hashlib
import json
import os
from pathlib import Path

STAMP_PATH = Path("vector_db/index_meta.json")

#: Bumped when chunking or indexing logic changes in a way that invalidates
#: previously built indexes.
SCHEMA_VERSION = 3


def expected_stamp(vector_dimension: int, backend: str, model: str | None) -> dict:
    """Describe the configuration the running process would build."""

    from app.rag.chunker import DocumentChunker

    knowledge_base = Path("knowledge_base")
    source_inventory = []
    if knowledge_base.exists():
        for path in sorted(knowledge_base.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".pdf", ".txt", ".md"}:
                stat = path.stat()
                with path.open("rb") as source:
                    digest = hashlib.file_digest(source, "sha256").hexdigest()
                source_inventory.append(
                    {
                        "path": path.relative_to(knowledge_base).as_posix(),
                        "size": stat.st_size,
                        "sha256": digest,
                    }
                )

    return {
        "schema_version": SCHEMA_VERSION,
        "embedding_backend": backend,
        "embedding_model": model,
        "vector_dimension": vector_dimension,
        "chunk_size": DocumentChunker.chunk_size(),
        "chunk_overlap": DocumentChunker.chunk_overlap(),
        "deduplicate_chunks": os.getenv("RAG_DEDUPE_CHUNKS", "true").lower()
        not in {"0", "false", "no"},
        "knowledge_base_sources": source_inventory,
    }


def write_stamp(stamp: dict) -> None:
    STAMP_PATH.parent.mkdir(parents=True, exist_ok=True)
    STAMP_PATH.write_text(json.dumps(stamp, indent=2), encoding="utf-8")


def read_stamp() -> dict | None:
    if not STAMP_PATH.exists():
        return None
    try:
        return json.loads(STAMP_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def matches(expected: dict, stored: dict | None) -> bool:
    return stored is not None and stored == expected

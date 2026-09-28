"""Chunking for retrieval.

Chunk size is a retrieval parameter, not a formatting detail: too small and a
passage loses the context that makes it retrievable, too large and the
embedding is diluted across several topics. The original values (800/150) were
plausible but never measured.

Rather than assert that a different size is better, the size and overlap are
read from the environment so the evaluation harness can sweep them and the
result can be reported as a measurement. :meth:`DocumentChunker.sweep` runs
that comparison.

The defaults below are the outcome of that sweep over four settings
(``evaluation/retrieval_sweep.json``), measured with the dense arm so the
comparison isolates chunking from fusion:

===========  ========  ==========  ========  =========
size/overlap chunks    Recall@5    MRR       nDCG@5
===========  ========  ==========  ========  =========
600/100      4873      0.7222      0.5713    0.6082
800/150      3662      0.7222      0.5065    0.5600
1000/200     3041      0.6111      0.4352    0.4795
1200/250     2554      0.7222      0.4398    0.5103
===========  ========  ==========  ========  =========

600/100 is better or equal on all four metrics and 1000/200 is clearly worst,
so 800/150 was a middle-of-the-road default that the measurement did not
support. The cost is 33% more chunks, which is ~7MB of float32 vectors on a
512MB instance - small enough not to threaten the free tier. The 18-question
benchmark means the MRR margin is a question or two wide, so this is a
better-supported default rather than a decisive one; the environment variables
remain the escape hatch.
"""

import os

from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_CHUNK_SIZE = 600
DEFAULT_CHUNK_OVERLAP = 100

SEPARATORS = [
    "\n\n",
    "\n",
    ". ",
    " ",
    "",
]


class DocumentChunker:

    @staticmethod
    def chunk_size() -> int:
        return int(os.getenv("RAG_CHUNK_SIZE", DEFAULT_CHUNK_SIZE))

    @staticmethod
    def chunk_overlap() -> int:
        return int(os.getenv("RAG_CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP))

    @staticmethod
    def chunk_documents(
        documents,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        """Split documents into overlapping chunks with rich metadata."""

        chunk_size = chunk_size or DocumentChunker.chunk_size()
        chunk_overlap = (
            chunk_overlap
            if chunk_overlap is not None
            else DocumentChunker.chunk_overlap()
        )

        # A splitter with overlap >= size drops content silently.
        if chunk_overlap >= chunk_size:
            chunk_overlap = max(chunk_size // 5, 0)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=SEPARATORS,
        )

        chunks = splitter.split_documents(documents)

        for index, chunk in enumerate(chunks):
            metadata = dict(chunk.metadata)
            metadata["chunk_index"] = index
            metadata["chunk_id"] = (
                f"{metadata.get('filename', 'document')}:{index}"
            )
            metadata["chunk_size"] = len(chunk.page_content)
            # A cheap section hint: the first non-empty line of a chunk is
            # usually a heading in the standards documents that dominate the
            # knowledge base. It is surfaced in citations so a user can judge a
            # source without opening the PDF.
            metadata["section_hint"] = DocumentChunker._section_hint(
                chunk.page_content
            )
            chunk.metadata = metadata

        return chunks

    @staticmethod
    def _section_hint(text: str, limit: int = 90) -> str:
        for line in text.splitlines():
            stripped = line.strip()
            if 3 <= len(stripped) <= limit:
                return stripped
        return ""

    @staticmethod
    def sweep(documents, sizes, overlaps):
        """Chunk under several (size, overlap) settings for comparison.

        Used by the evaluation harness so a chunking claim is backed by a
        measurement over the labelled question set rather than by intuition.
        """

        return {
            (size, overlap): DocumentChunker.chunk_documents(
                documents,
                chunk_size=size,
                chunk_overlap=overlap,
            )
            for size, overlap in zip(sizes, overlaps)
        }

"""Request and response models for the CyberGPT endpoint.

The response gained fields rather than changing existing ones, so the current
frontend keeps working unchanged: ``answer``, ``sources``, ``conversation_id``
and ``retrieval_metrics`` still mean exactly what they meant before. The new
fields describe *how* the answer was produced, which the UI can use to show an
honest label ("from the knowledge base" vs "general knowledge") instead of
presenting every answer as if it came from a document.

``conversation_id`` became optional. It was required, but the general-knowledge
path returned ``None``, so asking the assistant a question the corpus did not
cover raised a response-validation error and surfaced as a 500. Every path now
persists a conversation, so it is populated in practice; the type no longer
claims a guarantee the code did not keep.
"""

from typing import Optional

from pydantic import BaseModel, Field


class CopilotRequest(BaseModel):

    question: str

    conversation_id: Optional[int] = None


class Source(BaseModel):

    filename: str

    page: int

    folder: Optional[str] = None


class RetrievalMetrics(BaseModel):

    status: str

    retrieved_count: int

    candidate_count: Optional[int] = None

    vector_candidates: Optional[int] = None

    lexical_candidates: Optional[int] = None

    fusion: Optional[str] = None

    top_score: Optional[float] = None

    top_term_coverage: Optional[float] = None

    relevance_floor: Optional[float] = None

    reason: Optional[str] = None

    # Added so the payload can be audited: an evaluation run must never
    # silently compare results produced under different configurations.
    embedding_backend: Optional[str] = None

    top_semantic_similarity: Optional[float] = None

    scope: Optional[str] = None

    excluded_by_scope: Optional[int] = None


class RoutingInfo(BaseModel):

    source: Optional[str] = None

    confidence: Optional[float] = None

    reason: Optional[str] = None


class CopilotResponse(BaseModel):

    answer: str

    sources: list[Source] = Field(default_factory=list)

    conversation_id: Optional[int] = None

    retrieval_metrics: RetrievalMetrics = Field(
        default_factory=lambda: RetrievalMetrics(
            status="unknown",
            retrieved_count=0,
        )
    )

    #: ``document`` | ``general_knowledge`` | ``tool`` | ``conversation``.
    answer_basis: Optional[str] = None

    #: ``document`` | ``related`` | ``irrelevant`` | ``not_applicable``.
    #: How well the retrieved passages matched, independent of which path
    #: answered.
    relevance: Optional[str] = None

    #: Set when a deterministic tool produced the answer, so the UI can label
    #: it (e.g. "Password Generator") rather than implying the model wrote it.
    tool_used: Optional[str] = None

    tool_ok: Optional[bool] = None

    #: Passages that were retrieved but did not support the answer. Offered as
    #: related reading, never cited.
    related_sources: list[Source] = Field(default_factory=list)

    suggestions: list[str] = Field(default_factory=list)

    intent: Optional[str] = None

    routing: Optional[RoutingInfo] = None

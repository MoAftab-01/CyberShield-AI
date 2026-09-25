from typing import Optional

from pydantic import BaseModel, Field


class CopilotRequest(BaseModel):

    question: str

    conversation_id: Optional[int] = None


class Source(BaseModel):

    filename: str

    page: int

    folder: str


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


class CopilotResponse(BaseModel):

    answer: str

    sources: list[Source]

    conversation_id: int
    retrieval_metrics: RetrievalMetrics = Field(
        default_factory=lambda: RetrievalMetrics(
            status="unknown",
            retrieved_count=0,
        )
    )
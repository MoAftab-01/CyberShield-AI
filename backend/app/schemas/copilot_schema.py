from typing import Optional

from pydantic import BaseModel


class CopilotRequest(BaseModel):

    question: str

    conversation_id: Optional[int] = None


class Source(BaseModel):

    filename: str

    page: int

    folder: str


class CopilotResponse(BaseModel):

    answer: str

    sources: list[Source]

    conversation_id: int
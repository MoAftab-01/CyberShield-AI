from datetime import datetime

from pydantic import BaseModel


class ConversationItem(BaseModel):

    id: int

    title: str

    created_at: datetime

    updated_at: datetime

    class Config:

        from_attributes = True


class ChatMessageResponse(BaseModel):

    role: str

    content: str

    created_at: datetime

    class Config:

        from_attributes = True


class ConversationResponse(BaseModel):

    id: int

    title: str

    messages: list[ChatMessageResponse]
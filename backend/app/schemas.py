from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str


class ResponseBlock(BaseModel):
    type: Literal['markdown', 'image', 'html', 'upload']
    content: str
    alt_text: Optional[str] = Field(None, alias='altText')

    class Config:
        populate_by_name = True


class ChatRequest(BaseModel):
    conversation_id: str = Field(..., alias='conversationId')
    space_key: str = Field(..., alias='spaceKey')
    space_title: str = Field(..., alias='spaceTitle')
    message: str
    history: Optional[List[ChatMessage]] = None

    class Config:
        populate_by_name = True


class ChatResponse(BaseModel):
    conversation_id: str = Field(..., alias='conversationId')
    outputs: List[ResponseBlock]
    timestamp: str

    class Config:
        populate_by_name = True


class HealthResponse(BaseModel):
    status: str = 'ok'

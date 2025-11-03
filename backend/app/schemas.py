from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str


class ResponseBlock(BaseModel):
    type: Literal['markdown', 'image', 'html', 'upload', 'queryButtons', 'pdf2p']
    content: str
    alt_text: Optional[str] = Field(None, alias='altText')
    buttons: Optional[List[Dict[str, str]]] = None
    interaction_completed: Optional[bool] = Field(None, alias='interactionCompleted')

    class Config:
        populate_by_name = True


class ResponseCard(BaseModel):
    card_type: Literal['user-assistant', 'assistant-only', 'system'] = Field(..., alias='cardType')
    user_text: Optional[str] = Field(None, alias='userText')
    assistant_blocks: List[ResponseBlock] = Field(default_factory=list, alias='assistantBlocks')
    metadata: Optional[Dict[str, object]] = None

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
    cards: List[ResponseCard]
    timestamp: str

    class Config:
        populate_by_name = True


class HealthResponse(BaseModel):
    status: str = 'ok'

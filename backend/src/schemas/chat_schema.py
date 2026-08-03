from pydantic import BaseModel
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

class MessageRead(BaseModel):
    id: UUID
    role: str
    content: str
    metadata_payload: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationRead(BaseModel):
    id: UUID
    title: Optional[str] = None
    is_shared: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationDetailRead(ConversationRead):
    messages: List[MessageRead] = []

class ShareRequest(BaseModel):
    is_shared: bool

class UserMemoryRead(BaseModel):
    id: UUID
    user_id: UUID
    fact: str
    created_at: datetime

    class Config:
        from_attributes = True

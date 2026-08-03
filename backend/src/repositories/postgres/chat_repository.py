from typing import Sequence, Optional
import uuid

from sqlalchemy import select, update, desc, delete
from sqlalchemy.orm import selectinload, Session

from src.models.chat_model import Conversation, Message, UserMemory, MessageRole

class ChatRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_conversation(self, user_id: uuid.UUID, title: Optional[str] = None) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: uuid.UUID, load_messages: bool = True) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        if load_messages:
            stmt = stmt.options(selectinload(Conversation.messages))
        result = self.session.execute(stmt)
        return result.scalars().first()

    def get_user_conversations(self, user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> Sequence[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        result = self.session.execute(stmt)
        return result.scalars().all()

    def add_message(
        self, 
        conversation_id: uuid.UUID, 
        role: MessageRole, 
        content: str, 
        metadata_payload: Optional[dict] = None
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_payload=metadata_payload
        )
        self.session.add(message)
        
        # Also update conversation updated_at
        stmt = update(Conversation).where(Conversation.id == conversation_id).values(updated_at=utcnow())
        self.session.execute(stmt)
        
        self.session.commit()
        self.session.refresh(message)
        return message

    def update_conversation_summary(self, conversation_id: uuid.UUID, summary: str, keywords: str) -> bool:
        stmt = update(Conversation).where(Conversation.id == conversation_id).values(summary=summary, keywords=keywords)
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount > 0

    def toggle_share(self, conversation_id: uuid.UUID, is_shared: bool) -> bool:
        stmt = update(Conversation).where(Conversation.id == conversation_id).values(is_shared=is_shared)
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount > 0

    def get_user_memories(self, user_id: uuid.UUID) -> Sequence[UserMemory]:
        stmt = select(UserMemory).where(UserMemory.user_id == user_id).order_by(desc(UserMemory.created_at))
        result = self.session.execute(stmt)
        return result.scalars().all()

    def add_user_memory(self, user_id: uuid.UUID, fact: str) -> UserMemory:
        memory = UserMemory(user_id=user_id, fact=fact)
        self.session.add(memory)
        self.session.commit()
        self.session.refresh(memory)
        return memory

    def delete_conversation(self, conversation_id: uuid.UUID) -> bool:
        stmt = delete(Conversation).where(Conversation.id == conversation_id)
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount > 0

    def clear_user_memories(self, user_id: uuid.UUID) -> bool:
        stmt = delete(UserMemory).where(UserMemory.user_id == user_id)
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount > 0

def utcnow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)

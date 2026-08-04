from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from src.infrastructure.database import get_db
from src.api.middleware.auth_middleware import get_current_user
from src.models.user_model import User
from src.repositories.postgres.chat_repository import ChatRepository
from src.schemas.chat_schema import ConversationRead, ConversationDetailRead, ShareRequest, UserMemoryRead
from src.schemas.response_schema import StandardResponse

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

def get_chat_repo(db: Session = Depends(get_db)):
    return ChatRepository(db)

@router.get("/conversations", response_model=StandardResponse[List[ConversationRead]])
async def get_conversations(
    limit: int = 50,
    offset: int = 0,
    repo: ChatRepository = Depends(get_chat_repo),
    user: User = Depends(get_current_user)
):
    """Get all conversations for the logged in user."""
    data = repo.get_user_conversations(user.id, limit=limit, offset=offset)
    return StandardResponse(status="success", message="Conversations retrieved", data=data)

@router.get("/conversations/{conversation_id}", response_model=StandardResponse[ConversationDetailRead])
async def get_conversation(
    conversation_id: UUID,
    repo: ChatRepository = Depends(get_chat_repo),
    user: User = Depends(get_current_user)
):
    """Get details and messages of a specific conversation."""
    conversation = repo.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if conversation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return StandardResponse(status="success", message="Conversation retrieved", data=conversation)

@router.patch("/conversations/{conversation_id}/share")
async def toggle_share(
    conversation_id: UUID,
    req: ShareRequest,
    repo: ChatRepository = Depends(get_chat_repo),
    user: User = Depends(get_current_user)
):
    """Toggle the public sharing status of a conversation."""
    conversation = repo.get_conversation(conversation_id, load_messages=False)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if conversation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    repo.toggle_share(conversation_id, req.is_shared)
    return StandardResponse(status="success", message="Share status updated", data={"is_shared": req.is_shared})

@router.get("/shared/{conversation_id}", response_model=StandardResponse[ConversationDetailRead])
async def get_shared_conversation(
    conversation_id: UUID,
    repo: ChatRepository = Depends(get_chat_repo),
    user: User = Depends(get_current_user) # Authentication required, but can be ANY user
):
    """View a shared conversation. User must be logged into KnowledgeOS."""
    conversation = repo.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    # If the user is the owner, they can see it even if it's not shared. Otherwise, it MUST be shared.
    if not conversation.is_shared and conversation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This conversation is private")
        
    return StandardResponse(status="success", message="Shared conversation retrieved", data=conversation)

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID,
    repo: ChatRepository = Depends(get_chat_repo),
    user: User = Depends(get_current_user)
):
    """Delete a specific conversation."""
    conversation = repo.get_conversation(conversation_id, load_messages=False)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if conversation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    repo.delete_conversation(conversation_id)

@router.delete("/memories", status_code=status.HTTP_204_NO_CONTENT)
def clear_user_memories(
    repo: ChatRepository = Depends(get_chat_repo),
    user: User = Depends(get_current_user)
):
    """Clear all extracted memories for the user."""
    repo.clear_user_memories(user.id)

@router.get("/memories", response_model=StandardResponse[list[UserMemoryRead]])
def get_user_memories(
    repo: ChatRepository = Depends(get_chat_repo),
    user: User = Depends(get_current_user)
):
    """Fetch all extracted memories for the user."""
    data = repo.get_user_memories(user.id)
    return StandardResponse(status="success", message="Memories retrieved", data=data)

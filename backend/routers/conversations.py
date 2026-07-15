from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.crud import (
    create_conversation,
    delete_conversation,
    get_conversation_for_user,
    get_conversations_for_user,
    get_conversation_messages_for_user,
)
from database.database import get_db
from database.models import Conversation, Message, User
from schemas import ConversationCreate, ConversationRead, MessageRead

router = APIRouter(prefix="/conversations", tags=["conversations"])


def serialize_conversation(conversation: Conversation) -> ConversationRead:
    return ConversationRead(
        id=str(conversation.id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def serialize_message(message: Message) -> MessageRead:
    return MessageRead(
        id=str(message.id),
        conversation_id=str(message.conversation_id),
        role=message.role,
        content=message.content,
        created_at=message.created_at,
    )


@router.get("/", response_model=list[ConversationRead])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[ConversationRead]:
    conversations = get_conversations_for_user(db, current_user.id)
    return [serialize_conversation(conversation) for conversation in conversations]


@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_new_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ConversationRead:
    title = payload.title.strip() if payload.title and payload.title.strip() else "New chat"
    conversation = create_conversation(db, current_user.id, title)
    return serialize_conversation(conversation)


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation_metadata(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ConversationRead:
    conversation = get_conversation_for_user(db, current_user.id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return serialize_conversation(conversation)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[MessageRead]:
    messages = get_conversation_messages_for_user(db, current_user.id, conversation_id)
    return [serialize_message(message) for message in messages]


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation_endpoint(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    conversation = get_conversation_for_user(db, current_user.id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    delete_conversation(db, conversation)

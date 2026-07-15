from __future__ import annotations

from datetime import datetime
from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session

from .models import Conversation, Message, User


def get_user_by_id(db: Session, user_id: str | UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, email: str, password_hash: str) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_conversation(db: Session, user_id: str | UUID, title: str = "New chat") -> Conversation:
    conversation = Conversation(
        user_id=user_id,
        title=title
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversations_for_user(db: Session, user_id: str | UUID) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
        .all()
    )


def get_conversation_for_user(
    db: Session,
    user_id: str | UUID,
    conversation_id: str | UUID
) -> Conversation | None:
    return (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        .first()
    )


def delete_conversation(db: Session, conversation: Conversation) -> None:
    db.delete(conversation)
    db.commit()


def save_message(
    db: Session,
    conversation: Conversation,
    role: str,
    content: str
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content
    )
    conversation.updated_at = datetime.utcnow()
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_conversation_messages_for_user(
    db: Session,
    user_id: str | UUID,
    conversation_id: str | UUID
) -> list[Message]:
    return (
        db.query(Message)
        .join(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Conversation.id == conversation_id
        )
        .order_by(Message.created_at.asc())
        .all()
    )


def build_history(messages: Iterable[Message]) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    pending_question: str | None = None

    for message in messages:
        if message.role == "user":
            pending_question = message.content
            continue

        if message.role == "assistant" and pending_question:
            history.append(
                {
                    "question": pending_question,
                    "answer": message.content
                }
            )
            pending_question = None

    return history

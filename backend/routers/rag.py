from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime

from auth.dependencies import get_current_user
from database.crud import (
    build_history,
    get_conversation_for_user,
    get_conversation_messages_for_user,
    save_message,
)
from database.database import get_db
from database.models import User
from schemas import AskRequest, AskResponse

router = APIRouter(tags=["rag"])


@router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AskResponse:
    rag_engine = getattr(request.app.state, "rag_engine", None)
    if rag_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not loaded"
        )

    conversation = get_conversation_for_user(db, current_user.id, payload.conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    messages = get_conversation_messages_for_user(db, current_user.id, payload.conversation_id)
    history = build_history(messages)
    result = rag_engine.ask(payload.question, history)

    save_message(db, conversation, "user", payload.question)
    save_message(db, conversation, "assistant", result["answer"])

    if conversation.title == "New chat":
        conversation.title = payload.question[:60]
        conversation.updated_at = datetime.utcnow()
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    return AskResponse(
        answer=result["answer"],
        sources=result["sources"],
        matched=result["matched"],
        standalone_question=result["standalone_question"],
        conversation_id=str(conversation.id),
    )

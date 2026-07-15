from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.hashing import hash_password, verify_password
from auth.jwt import create_access_token
from database.crud import create_user, get_user_by_email, get_user_by_username
from database.database import get_db
from database.models import User
from schemas import LoginRequest, RegisterRequest, TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def serialize_user(user: User) -> UserRead:
    return UserRead(
        id=str(user.id),
        username=user.username,
        email=user.email,
        created_at=user.created_at,
    )


def build_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        user=serialize_user(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing_user = get_user_by_email(db, payload.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    existing_username = get_user_by_username(db, payload.username)
    if existing_username is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )

    user = create_user(
        db,
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password)
    )
    return build_token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return build_token_response(user)

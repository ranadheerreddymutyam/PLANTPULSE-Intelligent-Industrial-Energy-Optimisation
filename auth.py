"""API Router for Authentication and User Roles (L7 Governance)."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import hashlib
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import User
from app.schemas.domain import UserSchema, UserLoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication & Governance"])

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=payload.username).first()
    if not user or user.hashed_password != hash_pw(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    return TokenResponse(
        access_token=f"mock-jwt-token-{user.username}",
        user=user
    )

@router.get("/users", response_model=List[UserSchema])
def list_demo_users(db: Session = Depends(get_db)):
    """Returns available seeded user accounts to easily switch roles in demonstration."""
    return db.query(User).all()

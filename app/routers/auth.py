import hashlib
import secrets
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.api_token import APIToken, TokenPermission

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class TokenCreate(BaseModel):
    name: str
    permissions: TokenPermission = TokenPermission.read
    expires_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    id: UUID
    name: str
    permissions: TokenPermission
    created_at: datetime
    expires_at: Optional[datetime] = None
    token: Optional[str] = None  # nur bei Erstellung zurückgegeben

    model_config = {"from_attributes": True}


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(token: str, db: Session) -> APIToken:
    token_hash = _hash_token(token)
    api_token = db.query(APIToken).filter(APIToken.token_hash == token_hash).first()
    if not api_token:
        raise HTTPException(status_code=401, detail="Ungültiger Token")
    if api_token.expires_at and api_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token abgelaufen")
    return api_token


@router.get("/tokens", response_model=List[TokenResponse])
def list_tokens(db: Session = Depends(get_db)):
    return db.query(APIToken).order_by(APIToken.created_at.desc()).all()


@router.post("/tokens", response_model=TokenResponse, status_code=201)
def create_token(data: TokenCreate, db: Session = Depends(get_db)):
    raw_token = secrets.token_urlsafe(32)
    token = APIToken(
        name=data.name,
        token_hash=_hash_token(raw_token),
        permissions=data.permissions,
        expires_at=data.expires_at,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    response = TokenResponse.model_validate(token)
    response.token = raw_token  # einmalig zurückgeben
    return response


@router.delete("/tokens/{token_id}", status_code=204)
def delete_token(token_id: UUID, db: Session = Depends(get_db)):
    token = db.query(APIToken).filter(APIToken.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token nicht gefunden")
    db.delete(token)
    db.commit()

# app/core/auth_helper.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.models.models import User

oauth2_scheme = HTTPBearer()  # expects Authorization: Bearer <token>

def get_token_from_header(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> str:
    return credentials.credentials

def get_current_user(token: str = Depends(get_token_from_header), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token geçersiz veya süresi dolmuş")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token içinde kullanıcı yok")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanıcı bulunamadı")
    return user

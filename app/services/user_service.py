# app/services/user_service.py
import secrets
from sqlalchemy.orm import Session
from app.models.models import User
from app.core.security import get_password_hash, verify_password


def create_user(db: Session, first_name: str, last_name: str, email: str, password: str):
    hashed_pw = get_password_hash(password)

    user = User(
        first_name=first_name, 
        last_name=last_name, 
        email=email, 
        hashed_password=hashed_pw
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_user_profile(db: Session, user: User, data: dict) -> User:
    """Kullanıcının profil bilgilerini (ad, soyad) günceller."""
    for key, value in data.items():
        if key in ("first_name", "last_name") and value is not None:
            setattr(user, key, value)
            
    db.commit()
    db.refresh(user)
    return user

def change_user_email(db: Session, user: User, new_email: str) -> User | None:
    """Kullanıcının e-postasını ve kullanıcı adını günceller."""
    existing_user = db.query(User).filter(User.email == new_email).first()
    if existing_user and existing_user.id != user.id:
        return None 

    user.email = new_email
    db.commit()
    db.refresh(user)
    return user

def change_user_password(db: Session, user: User, new_password: str) -> bool:
    """Kullanıcının şifresini günceller."""
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True

def delete_user(db: Session, user_id: int):
    """Kullanıcıyı ve (cascade sayesinde) tüm özetlerini siler."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def get_or_create_user_by_email(db: Session, email: str, first_name: str, last_name: str) -> User:
    """
    E-postaya göre kullanıcıyı getirir veya yoksa oluşturur (Google Auth için).
    """
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        if user.first_name != first_name or user.last_name != last_name:
            user.first_name = first_name
            user.last_name = last_name
            db.commit()
            db.refresh(user)
        return user

    random_password = secrets.token_hex(16)
    
    return create_user(db, first_name, last_name, email, random_password)
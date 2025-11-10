# app/schemas/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class OzetCreate(BaseModel):
    baslik: str
    orijinal_metin: str

class OzetUpdate(BaseModel):
    baslik: Optional[str] = None
    icon_name: Optional[str] = None
    is_pinned: Optional[bool] = None
    ozet_metin: Optional[str] = None
    etiketler: Optional[str] = None

class OzetOut(BaseModel):
    id: int
    baslik: str
    orijinal_metin: str
    ozet_metin: str
    etiketler: Optional[str]
    sahip_id: int
    icon_name: Optional[str]
    is_pinned: Optional[bool]
    class Config:
        orm_mode = True

class OzetListItem(BaseModel):
    id: int
    baslik: str
    ozet_metin: str
    etiketler: Optional[str]
    icon_name: Optional[str]
    is_pinned: Optional[bool]
    class Config:
        orm_mode = True

class UserPublic(BaseModel):
    """Şifre olmadan, dışarıya verilecek kullanıcı modeli"""
    id: int
    first_name: str
    last_name: str
    email: str
    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    """Kullanıcının güncelleyebileceği alanlar (Sadece Ad/Soyad)"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class PasswordChange(BaseModel):
    """Şifre değiştirme şeması"""
    current_password: str
    new_password: str

class EmailChange(BaseModel):
    """E-posta değiştirme şeması"""
    current_password: str
    new_email: str

class AccountDelete(BaseModel):
    """Hesap silme onayı şeması"""
    password: str

class GoogleToken(BaseModel):
    token: str

class EmailSchema(BaseModel):
    email: str

class PasswordResetSchema(BaseModel):
    token: str
    new_password: str
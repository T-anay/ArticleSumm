# app/routers/auth_router.py
import os
from email.message import EmailMessage
import smtplib
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.user_service import (
    create_user, 
    authenticate_user, 
    update_user_profile,
    change_user_email,
    change_user_password,
    delete_user,
    get_or_create_user_by_email
)
from app.core.security import (
    create_access_token, 
    verify_password,
    decode_access_token
)
from app.schemas.schemas import (
    UserCreate, 
    UserLogin, 
    Token, 
    UserPublic, 
    UserUpdate,
    PasswordChange,
    EmailChange,
    AccountDelete,
    GoogleToken,
    EmailSchema,          
    PasswordResetSchema   
)
from app.models.models import User
from app.core.auth_helper import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/kayit", response_model=dict)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi zaten kayıtlı."
        )
    try:
        user = create_user(
            db, 
            user_data.first_name, 
            user_data.last_name, 
            user_data.email, 
            user_data.password
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Kullanıcı oluşturulamadı: " + str(e))
    
    return {"message": f"Kullanıcı '{user.first_name} {user.last_name}' oluşturuldu."}


@router.post("/token", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz kimlik bilgileri")
    
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}  

@router.get("/users/me", response_model=UserPublic)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Giriş yapmış kullanıcının kendi bilgilerini döndürür."""
    return current_user

@router.put("/users/me", response_model=UserPublic)
def update_users_me(
    user_data: UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Sadece Ad/Soyad günceller."""
    updated_user = update_user_profile(
        db, 
        user=current_user, 
        data=user_data.dict(exclude_unset=True)
    )
    return updated_user

@router.post("/change-email", response_model=UserPublic)
def change_email(
    data: EmailChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """E-postayı değiştirmeden önce şifreyi doğrular."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mevcut şifre yanlış.")
    
    updated_user = change_user_email(db, current_user, data.new_email)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu e-posta adresi zaten kullanılıyor.")
    
    return updated_user

@router.post("/change-password", response_model=dict)
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Şifreyi değiştirmeden önce mevcut şifreyi doğrular."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mevcut şifre yanlış.")
    
    change_user_password(db, current_user, data.new_password)
    return {"message": "Şifre başarıyla değiştirildi."}

@router.post("/users/delete", response_model=dict)
def delete_account(
    data: AccountDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hesabı silmeden önce şifreyi doğrular."""
    if not verify_password(data.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Şifre yanlış.")
    
    deleted = delete_user(db, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
        
    return {"message": "Hesap başarıyla silindi."}

@router.post("/google-login", response_model=Token)
def google_login(data: GoogleToken, db: Session = Depends(get_db)):
    
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Client ID sunucuda ayarlanmamış.")
    
    try:
        idinfo = id_token.verify_oauth2_token(data.token, requests.Request(), GOOGLE_CLIENT_ID)
        
        email = idinfo['email']
        first_name = idinfo.get('given_name', 'Kullanıcı')
        last_name = idinfo.get('family_name', '')

        user = get_or_create_user_by_email(db, email, first_name, last_name)
        
        token_data = {"sub": user.email}
        access_token = create_access_token(data=token_data)
        
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Google token'ı geçersiz: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google girişi sırasında hata oluştu: {str(e)}")
    

@router.post("/forgot-password")
def forgot_password(data: EmailSchema, db: Session = Depends(get_db)):
    """
    Kullanıcı e-postasına şifre sıfırlama linki gönderir.
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        return {"message": "Eğer e-posta adresiniz sistemde kayıtlıysa, sıfırlama linki gönderildi."}

    reset_token = create_access_token(
        data={"sub": user.email, "type": "reset"},
        expires_minutes=30
    )
    
    try:
        MAIL_USERNAME = os.getenv("MAIL_USERNAME")
        MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
        MAIL_FROM = os.getenv("MAIL_FROM")
        MAIL_SERVER = os.getenv("MAIL_SERVER")

        if not all([MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM, MAIL_SERVER]):
            raise ValueError("E-posta sunucu bilgileri .env dosyasında eksik.")

        reset_link = f"http://localhost/reset-password.html?token={reset_token}" 
        
        msg = EmailMessage()
        msg.set_content(f"""
        Merhaba {user.first_name},

        ArticleSumm hesabınız için şifre sıfırlama talebinde bulundunuz.
        Yeni bir şifre belirlemek için aşağıdaki linke tıklayın (bu link 15 dakika geçerlidir):

        {reset_link}

        Eğer bu talebi siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz.
        """)
        msg['Subject'] = 'ArticleSumm - Şifre Sıfırlama Talebi'
        msg['From'] = MAIL_FROM
        msg['To'] = user.email

        with smtplib.SMTP(MAIL_SERVER, 587) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(msg)
            
    except Exception as e:
        print(f"E-posta gönderme hatası: {e}")
        raise HTTPException(status_code=500, detail="E-posta gönderilirken bir hata oluştu.")

    return {"message": "Eğer e-posta adresiniz sistemde kayıtlıysa, sıfırlama linki gönderildi."}


@router.post("/reset-password")
def reset_password(data: PasswordResetSchema, db: Session = Depends(get_db)):
    
    try:
        payload = decode_access_token(data.token)
        if not payload or payload.get("type") != "reset":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz veya süresi dolmuş token.")
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token içinde kullanıcı bilgisi yok.")

    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz veya süresi dolmuş token.")

    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
            
        change_user_password(db, user, data.new_password)
        
        return {"message": "Şifreniz başarıyla güncellendi. Giriş yapabilirsiniz."}

    except Exception as e:
        print(f"Şifre sıfırlama sırasında veritabanı hatası: {e}")
        raise HTTPException(status_code=500, detail="Şifre güncellenirken sunucuda bir hata oluştu.")
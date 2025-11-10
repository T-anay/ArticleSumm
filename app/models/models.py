# app/models/models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func , Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=True) 
    last_name = Column(String(50), nullable=True)  
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)   

    ozetler = relationship("Ozet", back_populates="kullanici", cascade="all, delete-orphan")

class Ozet(Base):
    __tablename__ = "ozetler"
    id = Column(Integer, primary_key=True, index=True)
    baslik = Column(String(255), nullable=False)
    orijinal_metin = Column(Text, nullable=False)
    ozet_metin = Column(Text, nullable=False)
    etiketler = Column(String(1000), nullable=True)
    sahip_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    tarih = Column(DateTime(timezone=True), server_default=func.now())

    icon_name = Column(String(50), nullable=True, default="fa-file-lines")
    is_pinned = Column(Boolean, nullable=True, default=False)

    kullanici = relationship("User", back_populates="ozetler")

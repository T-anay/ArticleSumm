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

    calismalar = relationship("Calisma", back_populates="kullanici", cascade="all, delete-orphan")
    ozetler = relationship("Ozet", back_populates="kullanici", cascade="all, delete-orphan")


class Calisma(Base):
    __tablename__ = "calismalar"
    id = Column(Integer, primary_key=True, index=True)
    baslik = Column(String(255), nullable=False)
    sahip_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_pinned = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    kullanici = relationship("User", back_populates="calismalar")
    ozetler = relationship("Ozet", back_populates="calisma", cascade="all, delete-orphan")

class Ozet(Base):
    __tablename__ = "ozetler"
    id = Column(Integer, primary_key=True, index=True)
    baslik = Column(String(255), nullable=False)
    orijinal_metin = Column(Text, nullable=False)
    ozet_metin = Column(Text, nullable=False)
    etiketler = Column(String(1000), nullable=True)
    sahip_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    calisma_id = Column(Integer, ForeignKey("calismalar.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    icon_name = Column(String(50), nullable=True, default="fa-file-lines")
    is_pinned = Column(Boolean, nullable=True, default=False)

    kullanici = relationship("User", back_populates="ozetler")
    calisma = relationship("Calisma", back_populates="ozetler")

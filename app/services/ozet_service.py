# app/services/ozet_service.py
from sqlalchemy.orm import Session
from app.models.models import Ozet
from app.services.ai_service import summarize_text_simple, extract_keywords_yake
from datetime import datetime

def create_ozet(db: Session, baslik: str, orijinal_metin: str, owner_id: int, max_chars: int = 1500, length_mode: str = "medium"):
    # AI servisine length_mode bilgisini de gönderiyoruz
    ozet_metin = summarize_text_simple(orijinal_metin, max_chars=max_chars, length_mode=length_mode)
    
    keywords = extract_keywords_yake(orijinal_metin)
    etiketler_str = ", ".join(keywords)
    
    # İkon seçimi (Basit mantık)
    icon = "fa-file-lines"
    if "bilim" in orijinal_metin.lower(): icon = "fa-flask"
    elif "finans" in orijinal_metin.lower(): icon = "fa-chart-pie"

    db_ozet = Ozet(
        baslik=baslik,
        orijinal_metin=orijinal_metin,
        ozet_metin=ozet_metin,
        etiketler=etiketler_str,
        owner_id=owner_id,
        icon_name=icon,
        created_at=datetime.utcnow()
    )
    db.add(db_ozet)
    db.commit()
    db.refresh(db_ozet)
    return db_ozet

def list_ozetler(db: Session, owner_id: int):
    return db.query(Ozet).filter(Ozet.owner_id == owner_id).order_by(Ozet.is_pinned.desc(), Ozet.created_at.desc()).all()

def get_ozet(db: Session, ozet_id: int, owner_id: int):
    return db.query(Ozet).filter(Ozet.id == ozet_id, Ozet.owner_id == owner_id).first()

def delete_ozet(db: Session, ozet_id: int, owner_id: int):
    ozet = db.query(Ozet).filter(Ozet.id == ozet_id, Ozet.owner_id == owner_id).first()
    if ozet:
        db.delete(ozet)
        db.commit()
        return True
    return False

def update_ozet(db: Session, ozet_id: int, owner_id: int, data: dict):
    ozet = db.query(Ozet).filter(Ozet.id == ozet_id, Ozet.owner_id == owner_id).first()
    if not ozet:
        return None
    for key, value in data.items():
        setattr(ozet, key, value)
    db.commit()
    db.refresh(ozet)
    return ozet

def delete_all_summaries(db: Session, owner_id: int):
    count = db.query(Ozet).filter(Ozet.owner_id == owner_id).delete()
    db.commit()
    return count
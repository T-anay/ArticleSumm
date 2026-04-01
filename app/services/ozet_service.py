# app/services/ozet_service.py
from sqlalchemy.orm import Session
from app.models.models import Ozet
from app.services.ai_service import summarize_with_embeddings, extract_keywords_yake
from datetime import datetime

def create_ozet(db: Session, baslik: str, orijinal_metin: str, owner_id: int, max_chars: int = 1500, length_mode: str = "medium", target_language: str = "en", source_language: str = "auto"):
    """
    Create a new summary with multilingual support.
    
    NEW V3.0 (MULTILINGUAL):
    - 50+ languages supported (Turkish, English, German, French, Spanish, Italian, etc.)
    - Auto language detection for source
    - Cross-lingual summarization (e.g., Turkish PDF → English summary)
    - Database context for better quality
    
    Args:
        db: Database session
        baslik: Document title
        orijinal_metin: Original document text
        owner_id: User ID
        max_chars: Maximum character limit (fallback)
        length_mode: 'short', 'medium', or 'long'
        target_language: Target language code (e.g., 'en', 'tr', 'de')
        source_language: Source language code or 'auto' for detection
    """
    # Multilingual summarization with database context
    ozet_metin = summarize_with_embeddings(
        orijinal_metin,
        owner_id=owner_id,
        title=baslik,
        length_mode=length_mode,
        max_chars=max_chars,
        target_language=target_language,
        source_language=source_language,
        db=db,  # Pass database session for context loading
        use_multilingual=True,  # Enable mBART-50
    )
    
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
        sahip_id=owner_id,
        icon_name=icon
    )
    db.add(db_ozet)
    db.commit()
    db.refresh(db_ozet)
    return db_ozet

def list_ozetler(db: Session, owner_id: int):
    return db.query(Ozet).filter(Ozet.sahip_id == owner_id).order_by(Ozet.is_pinned.desc(), Ozet.created_at.desc()).all()

def get_ozet(db: Session, ozet_id: int, owner_id: int):
    return db.query(Ozet).filter(Ozet.id == ozet_id, Ozet.sahip_id == owner_id).first()

def delete_ozet(db: Session, ozet_id: int, owner_id: int):
    ozet = db.query(Ozet).filter(Ozet.id == ozet_id, Ozet.sahip_id == owner_id).first()
    if ozet:
        db.delete(ozet)
        db.commit()
        return True
    return False

def update_ozet(db: Session, ozet_id: int, owner_id: int, data: dict):
    ozet = db.query(Ozet).filter(Ozet.id == ozet_id, Ozet.sahip_id == owner_id).first()
    if not ozet:
        return None
    for key, value in data.items():
        setattr(ozet, key, value)
    db.commit()
    db.refresh(ozet)
    return ozet

def delete_all_summaries(db: Session, owner_id: int):
    count = db.query(Ozet).filter(Ozet.sahip_id == owner_id).delete()
    db.commit()
    return count
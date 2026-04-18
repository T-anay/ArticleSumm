# app/services/ozet_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import Ozet, Calisma
from app.services.ai_service import summarize_with_embeddings, extract_keywords_yake
from datetime import datetime

DEFAULT_CALISMA_TITLE = "Genel Çalışma"


def get_or_create_default_calisma(db: Session, owner_id: int) -> Calisma:
    calisma = (
        db.query(Calisma)
        .filter(Calisma.sahip_id == owner_id, Calisma.baslik == DEFAULT_CALISMA_TITLE)
        .first()
    )
    if calisma:
        legacy_count = (
            db.query(Ozet)
            .filter(Ozet.sahip_id == owner_id, Ozet.calisma_id.is_(None))
            .update({Ozet.calisma_id: calisma.id})
        )
        if legacy_count:
            db.commit()
        return calisma

    calisma = Calisma(baslik=DEFAULT_CALISMA_TITLE, sahip_id=owner_id)
    db.add(calisma)
    db.commit()
    db.refresh(calisma)

    legacy_count = (
        db.query(Ozet)
        .filter(Ozet.sahip_id == owner_id, Ozet.calisma_id.is_(None))
        .update({Ozet.calisma_id: calisma.id})
    )
    if legacy_count:
        db.commit()

    return calisma


def create_calisma(db: Session, owner_id: int, baslik: str) -> Calisma:
    calisma = Calisma(baslik=baslik.strip() or DEFAULT_CALISMA_TITLE, sahip_id=owner_id, is_pinned=False)
    db.add(calisma)
    db.commit()
    db.refresh(calisma)
    return calisma


def list_calismalar(db: Session, owner_id: int):
    get_or_create_default_calisma(db, owner_id)

    latest_summary_times = dict(
        db.query(Ozet.calisma_id, func.max(Ozet.created_at))
        .filter(Ozet.sahip_id == owner_id)
        .group_by(Ozet.calisma_id)
        .all()
    )

    calismalar = (
        db.query(Calisma)
        .filter(Calisma.sahip_id == owner_id)
        .all()
    )

    def sort_key(item: Calisma):
        latest_summary = latest_summary_times.get(item.id) or item.created_at or datetime.min
        created_at = item.created_at or datetime.min
        return (1 if item.is_pinned else 0, latest_summary, created_at)

    return sorted(calismalar, key=sort_key, reverse=True)


def get_calisma(db: Session, calisma_id: int, owner_id: int):
    return db.query(Calisma).filter(Calisma.id == calisma_id, Calisma.sahip_id == owner_id).first()


def update_calisma(db: Session, calisma_id: int, owner_id: int, baslik: str | None = None, is_pinned: bool | None = None):
    calisma = get_calisma(db, calisma_id, owner_id)
    if not calisma:
        return None

    if baslik is not None:
        new_title = (baslik or "").strip()
        if not new_title:
            new_title = DEFAULT_CALISMA_TITLE
        calisma.baslik = new_title

    if is_pinned is not None:
        calisma.is_pinned = bool(is_pinned)

    db.commit()
    db.refresh(calisma)
    return calisma


def delete_calisma(db: Session, calisma_id: int, owner_id: int):
    calisma = get_calisma(db, calisma_id, owner_id)
    if not calisma:
        return None

    fallback = (
        db.query(Calisma)
        .filter(Calisma.sahip_id == owner_id, Calisma.id != calisma_id)
        .order_by(Calisma.created_at.desc())
        .first()
    )

    if fallback is None:
        fallback_title = "Yeni Çalışma" if calisma.baslik == DEFAULT_CALISMA_TITLE else DEFAULT_CALISMA_TITLE
        fallback = Calisma(baslik=fallback_title, sahip_id=owner_id)
        db.add(fallback)
        db.commit()
        db.refresh(fallback)

    db.query(Ozet).filter(Ozet.sahip_id == owner_id, Ozet.calisma_id == calisma_id).update({Ozet.calisma_id: fallback.id})
    db.delete(calisma)
    db.commit()
    return fallback


def create_ozet(db: Session, baslik: str, orijinal_metin: str, owner_id: int, max_chars: int = 1500, length_mode: str = "medium", target_language: str = "en", source_language: str = "auto", calisma_id: int | None = None):
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

    if calisma_id is not None:
        calisma = get_calisma(db, calisma_id, owner_id)
        if calisma is None:
            calisma_id = None

    if calisma_id is None:
        calisma_id = get_or_create_default_calisma(db, owner_id).id
    
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
        calisma_id=calisma_id,
        icon_name=icon
    )
    db.add(db_ozet)
    db.commit()
    db.refresh(db_ozet)
    return db_ozet

def list_ozetler(db: Session, owner_id: int):
    return db.query(Ozet).filter(Ozet.sahip_id == owner_id).order_by(Ozet.is_pinned.desc(), Ozet.created_at.desc()).all()


def list_ozetler_by_calisma(db: Session, owner_id: int, calisma_id: int):
    return (
        db.query(Ozet)
        .filter(Ozet.sahip_id == owner_id, Ozet.calisma_id == calisma_id)
        .order_by(Ozet.is_pinned.desc(), Ozet.created_at.desc())
        .all()
    )

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
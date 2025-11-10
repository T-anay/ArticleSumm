# app/services/ozet_service.py
from sqlalchemy.orm import Session
from app.models.models import Ozet
from app.services.ai_service import summarize_text_simple, extract_keywords_yake
from typing import List, Optional

def create_ozet(db: Session, baslik: str, orijinal_metin: str, sahip_id: int) -> Ozet:
    ozet_metin = summarize_text_simple(orijinal_metin)
    etiketler_list = extract_keywords_yake(orijinal_metin, max_keywords=6)
    etiketler = ", ".join(etiketler_list)
    
    new = Ozet(
        baslik=baslik, 
        orijinal_metin=orijinal_metin, 
        ozet_metin=ozet_metin, 
        etiketler=etiketler, 
        sahip_id=sahip_id,
        icon_name="fa-file-lines"
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def list_ozetler(db: Session, owner_id: int) -> List[Ozet]:
    return db.query(Ozet).filter(Ozet.sahip_id == owner_id).order_by(Ozet.is_pinned.desc(), Ozet.tarih.desc()).all()

def get_ozet(db: Session, ozet_id: int, owner_id: int) -> Optional[Ozet]:
    return db.query(Ozet).filter(Ozet.id == ozet_id, Ozet.sahip_id == owner_id).first()

def update_ozet(db: Session, ozet_id: int, owner_id: int, data: dict) -> Optional[Ozet]:
    ozet = db.query(Ozet).filter(Ozet.id == ozet_id, Ozet.sahip_id == owner_id).first()
    if not ozet:
        return None
    
    for key, value in data.items():
        if value is not None:
            setattr(ozet, key, value)
            
    db.commit()
    db.refresh(ozet)
    return ozet

def delete_ozet(db: Session, ozet_id: int, owner_id: int) -> bool:
    row = db.query(Ozet).filter(Ozet.id == ozet_id, Ozet.sahip_id == owner_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True

def delete_all_summaries(db: Session, owner_id: int) -> int:
    """Belirli bir kullanıcıya ait tüm özetleri siler."""
    
    ozetler_to_delete = db.query(Ozet).filter(Ozet.sahip_id == owner_id).all()
    
    count = len(ozetler_to_delete)
    
    if count == 0:
        db.commit() 
        return 0

    for ozet in ozetler_to_delete:
        db.delete(ozet)
        
    db.commit()
    return count
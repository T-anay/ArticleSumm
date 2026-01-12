# app/routers/ozet_router.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import OzetCreate, OzetOut, OzetListItem, OzetUpdate
from app.core.auth_helper import get_current_user
from app.services.ozet_service import create_ozet, list_ozetler, get_ozet, delete_ozet, update_ozet, delete_all_summaries
import fitz  
import io
import asyncio

router = APIRouter(prefix="/api/ozetler", tags=["Ozetler"])

@router.post("/pdf_yukle", response_model=OzetOut)
async def create_summary_from_pdf(
    baslik: str = Form(...),
    file: UploadFile = File(...),
    # Varsayılan: Mobil/Lay Summary (Orta)
    length_option: str = Form("medium"), 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları kabul edilmektedir.")
    
    orijinal_metin = ""
    try:
        pdf_data = await file.read()
        with fitz.open(stream=io.BytesIO(pdf_data)) as pdf_document:
            for page in pdf_document:
                orijinal_metin += page.get_text()
        
        if not orijinal_metin.strip():
            raise HTTPException(status_code=400, detail="PDF'den metin çıkarılamadı.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF işlenirken hata: {str(e)}")
    
    # --- AKADEMİK MANTIK KAPISI (LOGIC GATES) ---
    # Kaynak: Akademik Makale Uzunluğu Raporu
    kelime_sayisi = len(orijinal_metin.split())

    # Kural: Orijinal metin 1000 kelimeden azsa, "Uzun Özet" (Executive Summary)
    # oluşturmak AI halüsinasyonuna yol açar. Otomatik olarak "Orta"ya düşürülür.
    final_length_option = length_option
    if length_option == "long" and kelime_sayisi < 1000:
        final_length_option = "medium"

    # --- AYARLAR (SETTINGS) ---
    # Kaynak: UX ve Akademik Raporlar
    settings = {
        "short": {
            "mode": "abstract",
            "max_tokens": 120,      # ~40-50 kelime (The Glance)
            "hard_limit_chars": 600,
            "format_instruction": "inverted_pyramid" # Ters Piramit: En önemli bilgi en başta
        },
        "medium": {
            "mode": "lay_summary",
            "max_tokens": 750,      # ~250-300 kelime (The Scan)
            "hard_limit_chars": 2500,
            "format_instruction": "smart_brevity"   # Axios Tarzı: Bold girişler, maddeler
        },
        "long": {
            "mode": "executive",
            "max_tokens": 2000,     # ~1000+ kelime (The Study)
            "hard_limit_chars": 10000,
            "format_instruction": "hierarchical"    # H2, H3 Başlıklar, ToC uyumlu
        }
    }
    
    config = settings.get(final_length_option, settings["medium"])
    
    # Test Gecikmesi (Yükleme animasyonunu görmek için)
    await asyncio.sleep(3) 

    # Servise format bilgisini de gönderiyoruz (length_option parametresi ile)
    new = create_ozet(
        db, 
        baslik, 
        orijinal_metin, 
        current_user.id, 
        max_chars=config["hard_limit_chars"],
        length_mode=final_length_option # Servise hangi modda olduğunu bildir
    )
    return new

# ... (Diğer router fonksiyonları değişmedi: metin, get, delete vb.) ...
@router.post("/metin", response_model=OzetOut)
def create_summary_from_text(payload: OzetCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    new = create_ozet(db, payload.baslik, payload.orijinal_metin, current_user.id)
    return new

@router.get("/", response_model=list[OzetListItem])
def my_summaries(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    items = list_ozetler(db, current_user.id)
    return items

@router.delete("/all", response_model=dict)
def remove_all_summaries(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    count = delete_all_summaries(db, current_user.id)
    return {"message": f"{count} adet özet silindi."}

@router.get("/{ozet_id}", response_model=OzetOut)
def get_summary(ozet_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    item = get_ozet(db, ozet_id, current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Özet bulunamadı")
    return item

@router.put("/{ozet_id}", response_model=OzetOut)
def update_summary_details(ozet_id: int, payload: OzetUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    updated_ozet = update_ozet(db, ozet_id=ozet_id, owner_id=current_user.id, data=payload.dict(exclude_unset=True))
    if not updated_ozet:
        raise HTTPException(status_code=404, detail="Özet bulunamadı")
    return updated_ozet

@router.delete("/{ozet_id}", response_model=dict)
def remove_summary(ozet_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    ok = delete_ozet(db, ozet_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Özet bulunamadı")
    return {"message": "Silindi"}
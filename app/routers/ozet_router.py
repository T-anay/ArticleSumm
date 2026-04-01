# app/routers/ozet_router.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import OzetCreate, OzetOut, OzetListItem, OzetUpdate
from app.core.auth_helper import get_current_user
from app.services.ozet_service import create_ozet, list_ozetler, get_ozet, delete_ozet, update_ozet, delete_all_summaries
import io
import asyncio

try:
    import fitz
except ImportError:
    fitz = None

router = APIRouter(prefix="/api/ozetler", tags=["Ozetler"])

@router.post("/pdf_yukle", response_model=OzetOut)
async def create_summary_from_pdf(
    baslik: str = Form(...),
    file: UploadFile = File(...),
    length_option: str = Form("medium"),  # short | medium | long
    target_language: str = Form("en"),  # Target language code (en, tr, de, fr, es, it, etc.)
    source_language: str = Form("auto"),  # Source language code or 'auto' for detection
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    """
    Create summary from PDF file with MULTILINGUAL support.
    
    NEW V3.0 FEATURES:
    - ✅ 50+ languages supported (Turkish, English, German, French, Spanish, etc.)
    - ✅ Auto language detection
    - ✅ Cross-lingual summarization (e.g., Turkish PDF → English summary)
    - ✅ Author information removed
    
    Supported Languages:
        - English (en), Turkish (tr), German (de), French (fr), Spanish (es)
        - Italian (it), Russian (ru), Arabic (ar), Japanese (ja), Korean (ko)
        - Chinese (zh), Dutch (nl), Portuguese (pt), Hindi (hi)
        - And 35+ more languages
    
    Length Modes:
        - short: 30-60 words (article topic, mobile-friendly)
        - medium: 10% of original text
        - long: 25% of original text
    
    Examples:
        - Turkish PDF + target='en' → English summary
        - English PDF + target='tr' → Turkish summary
        - German PDF + target='fr' → French summary
        - source='auto' → Auto-detects PDF language
    """
    if fitz is None:
        raise HTTPException(
            status_code=503,
            detail="PDF ozeti su anda kullanilamiyor. Sunucuda PyMuPDF paketi eksik."
        )

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    
    orijinal_metin = ""
    try:
        pdf_data = await file.read()
        with fitz.open(stream=io.BytesIO(pdf_data)) as pdf_document:
            for page in pdf_document:
                orijinal_metin += page.get_text()
        
        if not orijinal_metin.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    # --- ACADEMIC LOGIC GATES ---
    # Source: Academic Article Length Report
    kelime_sayisi = len(orijinal_metin.split())

    # Rule: If original text < 1000 words, "long" summary may cause AI hallucination.
    # Automatically downgrade to "medium".
    final_length_option = length_option
    if length_option == "long" and kelime_sayisi < 1000:
        final_length_option = "medium"

    # --- LENGTH SETTINGS ---
    # NEW TARGETS (aligned with academic standards):
    # Short: 30-60 words (article topic, mobile-friendly)
    # Medium: 10% of original text
    # Long: 25% of original text
    settings = {
        "short": {
            "mode": "abstract",
            "target_words": "30-60",       # What the article is about
            "hard_limit_chars": 500,       # Mobile-friendly
            "format_instruction": "inverted_pyramid"  # Most important info first
        },
        "medium": {
            "mode": "lay_summary",
            "target_words": "10%",         # 10% of original text
            "hard_limit_chars": 3000,
            "format_instruction": "smart_brevity"  # Clear, concise
        },
        "long": {
            "mode": "executive",
            "target_words": "25%",         # 25% of original text
            "hard_limit_chars": 15000,
            "format_instruction": "hierarchical"  # Structured with sections
        }
    }
    
    config = settings.get(final_length_option, settings["medium"])
    
    # Test Gecikmesi (Yükleme animasyonunu görmek için)
    await asyncio.sleep(3) 

    # Multilingual summarization
    new = create_ozet(
        db, 
        baslik, 
        orijinal_metin, 
        current_user.id, 
        max_chars=config["hard_limit_chars"],
        length_mode=final_length_option,
        target_language=target_language,  # Target language code (e.g., 'en', 'tr', 'de')
        source_language=source_language   # Source language code or 'auto'
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
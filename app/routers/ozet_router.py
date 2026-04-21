# app/routers/ozet_router.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import OzetCreate, OzetOut, OzetListItem, OzetUpdate, CalismaCreate, CalismaUpdate, CalismaOut
from app.core.auth_helper import get_current_user
from app.services.ozet_service import create_ozet, list_ozetler, list_ozetler_by_calisma, get_ozet, delete_ozet, update_ozet, delete_all_summaries, create_calisma, list_calismalar, get_calisma, update_calisma, delete_calisma
import io
import html
import re
import textwrap
import unicodedata

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
    calisma_id: int | None = Form(None),
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
    
    # Multilingual summarization
    new = create_ozet(
        db, 
        baslik, 
        orijinal_metin, 
        current_user.id, 
        max_chars=config["hard_limit_chars"],
        length_mode=final_length_option,
        target_language=target_language,  # Target language code (e.g., 'en', 'tr', 'de')
        source_language=source_language,   # Source language code or 'auto'
        calisma_id=calisma_id,
    )
    return new

# ... (Diğer router fonksiyonları değişmedi: metin, get, delete vb.) ...
@router.post("/metin", response_model=OzetOut)
def create_summary_from_text(payload: OzetCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    new = create_ozet(
        db,
        payload.baslik,
        payload.orijinal_metin,
        current_user.id,
        length_mode=payload.length_option,
        target_language=payload.target_language,
        source_language=payload.source_language,
        calisma_id=payload.calisma_id,
    )
    return new

@router.get("/", response_model=list[OzetListItem])
def my_summaries(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    items = list_ozetler(db, current_user.id)
    return items


@router.get("/calismalar", response_model=list[CalismaOut])
def my_calismalar(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    items = list_calismalar(db, current_user.id)
    return items


@router.post("/calismalar", response_model=CalismaOut)
def add_calisma(payload: CalismaCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return create_calisma(db, current_user.id, payload.baslik)


@router.put("/calismalar/{calisma_id}", response_model=CalismaOut)
def rename_calisma(calisma_id: int, payload: CalismaUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    updated = update_calisma(db, calisma_id, current_user.id, payload.baslik, payload.is_pinned)
    if not updated:
        raise HTTPException(status_code=404, detail="Çalışma bulunamadı")
    return updated


@router.delete("/calismalar/{calisma_id}", response_model=dict)
def remove_calisma(calisma_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    fallback = delete_calisma(db, calisma_id, current_user.id)
    if not fallback:
        raise HTTPException(status_code=404, detail="Çalışma bulunamadı")
    return {
        "message": "Çalışma silindi.",
        "fallback_calisma_id": fallback.id,
        "fallback_calisma_baslik": fallback.baslik,
    }


@router.get("/calismalar/{calisma_id}/ozetler", response_model=list[OzetListItem])
def calisma_ozetleri(calisma_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    calisma = get_calisma(db, calisma_id, current_user.id)
    if not calisma:
        raise HTTPException(status_code=404, detail="Çalışma bulunamadı")
    return list_ozetler_by_calisma(db, current_user.id, calisma_id)


def _html_to_plain_text(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _safe_pdf_text(value: str) -> str:
    raw = str(value or "")
    normalized = unicodedata.normalize("NFKD", raw)
    # Built-in PDF fonts cannot render many Unicode glyphs reliably.
    latin_safe = normalized.encode("latin-1", "ignore").decode("latin-1")
    return latin_safe or " "


def _build_pdf_bytes(summary) -> bytes:
    if fitz is None:
        raise HTTPException(status_code=503, detail="PDF indirme için PyMuPDF paketi sunucuda yok.")

    page_width = 595
    page_height = 842
    margin = 48
    document = fitz.open()

    def new_page():
        return document.new_page(width=page_width, height=page_height)

    def wrap_lines(text_value: str, width: int):
        lines: list[str] = []
        for paragraph in text_value.split("\n"):
            stripped = paragraph.strip()
            if not stripped:
                lines.append("")
                continue
            wrapped = textwrap.wrap(stripped, width=width, break_long_words=False, replace_whitespace=False)
            lines.extend(wrapped or [""])
        return lines

    def write_lines(page, lines, font_size=11, font_name="helv", spacing=1.35, color=(0, 0, 0), start_y=margin):
        y = start_y
        current_page = page
        for line in lines:
            if y > page_height - margin:
                current_page = new_page()
                y = margin
            safe_line = _safe_pdf_text(line)
            current_page.insert_text((margin, y), safe_line, fontsize=font_size, fontname=font_name, color=color)
            y += int(font_size * spacing)
        return current_page, y

    page = new_page()
    y = margin

    title = summary.baslik or "Başlıksız Özet"
    page, y = write_lines(page, wrap_lines(title, 48), font_size=18, font_name="helv", spacing=1.25, start_y=y)
    y += 6

    workspace_title = getattr(getattr(summary, "calisma", None), "baslik", "Genel Çalışma")
    meta_lines = [
        f"Çalışma: {workspace_title}",
    ]
    tags = [tag.strip() for tag in (summary.etiketler or "").split(",") if tag.strip()]
    if tags:
        meta_lines.append("Etiketler: " + ", ".join(tags))

    page, y = write_lines(page, meta_lines, font_size=10, font_name="helv", spacing=1.25, color=(0.4, 0.4, 0.4), start_y=y)
    y += 8

    plain_text = _html_to_plain_text(summary.ozet_metin or "")
    for paragraph in plain_text.split("\n\n"):
        if not paragraph.strip():
            y += 8
            continue

        wrapped_lines = wrap_lines(paragraph, 90)
        page, y = write_lines(page, wrapped_lines, font_size=11, font_name="helv", spacing=1.4, start_y=y)
        y += 5

    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


@router.get("/{ozet_id}/pdf")
def download_summary_pdf(ozet_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    summary = get_ozet(db, ozet_id, current_user.id)
    if not summary:
        raise HTTPException(status_code=404, detail="Özet bulunamadı")

    try:
        pdf_bytes = _build_pdf_bytes(summary)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF oluşturulamadı: {exc}") from exc

    filename = f"ozet-{summary.id}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)

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
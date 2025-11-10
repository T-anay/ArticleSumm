# app/routers/ozet_router.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import OzetCreate, OzetOut, OzetListItem, OzetUpdate
from app.core.auth_helper import get_current_user
from app.services.ozet_service import create_ozet, list_ozetler, get_ozet, delete_ozet, update_ozet ,delete_all_summaries
import fitz  
import io

router = APIRouter(prefix="/api/ozetler", tags=["Ozetler"])

@router.post("/pdf_yukle", response_model=OzetOut)
async def create_summary_from_pdf(
    baslik: str = Form(...),
    file: UploadFile = File(...), 
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
            raise HTTPException(status_code=400, detail="PDF dosyasından metin çıkarılamadı (belki sadece resim içeriyor).")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF işlenirken hata oluştu: {str(e)}")

    new = create_ozet(db, baslik, orijinal_metin, current_user.id)
    return new


@router.post("/metin", response_model=OzetOut)
def create_summary_from_text(payload: OzetCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    new = create_ozet(db, payload.baslik, payload.orijinal_metin, current_user.id)
    return new


@router.get("/", response_model=list[OzetListItem])
def my_summaries(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    items = list_ozetler(db, current_user.id)
    return items


@router.delete("/all", response_model=dict)
def remove_all_summaries(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    count = delete_all_summaries(db, current_user.id)
    return {"message": f"{count} adet özet başarıyla silindi."}


@router.get("/{ozet_id}", response_model=OzetOut)
def get_summary(ozet_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    item = get_ozet(db, ozet_id, current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Özet bulunamadı")
    return item

@router.put("/{ozet_id}", response_model=OzetOut)
def update_summary_details(
    ozet_id: int,
    payload: OzetUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    updated_ozet = update_ozet(
        db,
        ozet_id=ozet_id,
        owner_id=current_user.id,
        data=payload.dict(exclude_unset=True)
    )
    if not updated_ozet:
        raise HTTPException(status_code=404, detail="Özet bulunamadı veya güncelleme yetkiniz yok")
    return updated_ozet


@router.delete("/{ozet_id}", response_model=dict)
def remove_summary(ozet_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    ok = delete_ozet(db, ozet_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Özet bulunamadı veya silme yetkiniz yok")
    return {"message": "Silindi"}


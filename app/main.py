from fastapi import FastAPI
from app.db.database import Base, engine, DB_SCHEMA
from app.routers import auth_router, ozet_router
from sqlalchemy import text

try:
    with engine.connect() as connection:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))
        connection.commit()
    print(f"'{DB_SCHEMA}' şeması başarıyla kontrol edildi/oluşturuldu.")
except Exception as e:
    print(f"HATA: '{DB_SCHEMA}' şeması oluşturulamadı. Detay: {e}")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ArticleSumm")

app.include_router(auth_router.router)
app.include_router(ozet_router.router)

@app.get("/health")
def health():
    return {"status": "ok"}

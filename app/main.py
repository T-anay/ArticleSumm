from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine, DB_SCHEMA, DB_IS_SQLITE
from app.routers import auth_router, ozet_router
from sqlalchemy import inspect, text
from dotenv import load_dotenv
import os

# Load environment variables from mounted .env and override stale container env values
load_dotenv(encoding='utf-8', override=True)

if not DB_IS_SQLITE:
    try:
        with engine.connect() as connection:
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))
            connection.commit()
        print(f"'{DB_SCHEMA}' şeması başarıyla kontrol edildi/oluşturuldu.")
    except Exception as e:
        print(f"HATA: '{DB_SCHEMA}' şeması oluşturulamadı. Detay: {e}")
else:
    print("[DB] SQLite fallback aktif. Şema oluşturma atlandı.")

Base.metadata.create_all(bind=engine)

def ensure_workspace_columns():
    inspector = inspect(engine)
    schema = None if DB_IS_SQLITE else DB_SCHEMA

    def ensure_columns(table_name: str, columns_to_add: list[tuple[str, str]]) -> None:
        columns = {column["name"] for column in inspector.get_columns(table_name, schema=schema)}
        full_table_name = f"{DB_SCHEMA}.{table_name}" if not DB_IS_SQLITE else table_name
        statements: list[str] = []

        for column_name, sql_fragment in columns_to_add:
            if column_name not in columns:
                statements.append(f"ALTER TABLE {full_table_name} ADD COLUMN {sql_fragment}")

        if statements:
            with engine.begin() as connection:
                for statement in statements:
                    connection.execute(text(statement))

    ensure_columns(
        "ozetler",
        [
            (
                "created_at",
                "created_at TIMESTAMPTZ DEFAULT NOW()"
                if not DB_IS_SQLITE
                else "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ),
            ("calisma_id", "calisma_id INTEGER"),
            ("icon_name", "icon_name VARCHAR(50) DEFAULT 'fa-file-lines'"),
            ("is_pinned", "is_pinned BOOLEAN DEFAULT FALSE"),
        ],
    )

    ensure_columns(
        "calismalar",
        [
            (
                "created_at",
                "created_at TIMESTAMPTZ DEFAULT NOW()"
                if not DB_IS_SQLITE
                else "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            )
            ,("is_pinned", "is_pinned BOOLEAN DEFAULT FALSE")
        ],
    )


ensure_workspace_columns()

app = FastAPI(title="ArticleSumm")

# CORS ayarları
frontend_origins_raw = os.getenv("FRONTEND_ORIGINS", "")
frontend_origins = [origin.strip() for origin in frontend_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "null",
        *frontend_origins,
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(ozet_router.router)

@app.get("/health")
def health():
    return {"status": "ok"}

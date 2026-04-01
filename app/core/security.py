# app/core/security.py
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import base64
import hashlib
import hmac
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
PBKDF2_ITERATIONS = 600_000
PBKDF2_SCHEME = "pbkdf2_sha256"

SECRET_KEY = os.getenv("SECRET_KEY", "COK_GIZLI_PAROLA")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def _pbkdf2_hash(password: str, salt: bytes | None = None) -> str:
    salt_bytes = salt or os.urandom(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        PBKDF2_ITERATIONS,
    )
    salt_b64 = base64.b64encode(salt_bytes).decode("ascii")
    hash_b64 = base64.b64encode(derived_key).decode("ascii")
    return f"{PBKDF2_SCHEME}${PBKDF2_ITERATIONS}${salt_b64}${hash_b64}"


def _verify_pbkdf2(password: str, hashed_password: str) -> bool:
    try:
        scheme, iterations, salt_b64, hash_b64 = hashed_password.split("$", 3)
        if scheme != PBKDF2_SCHEME:
            return False

        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            base64.b64decode(salt_b64.encode("ascii")),
            int(iterations),
        )
        expected_hash = base64.b64decode(hash_b64.encode("ascii"))
        return hmac.compare_digest(derived_key, expected_hash)
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    return _pbkdf2_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith(f"{PBKDF2_SCHEME}$"):
        return _verify_pbkdf2(plain_password, hashed_password)

    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

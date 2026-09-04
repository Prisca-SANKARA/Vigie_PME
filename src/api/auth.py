import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db.models import Client
from db.session import get_db

# En dev, valeur par défaut fournie pour ne pas bloquer le démarrage local ;
# en production, SECRET_KEY doit impérativement venir d'une variable
# d'environnement/secret manager, jamais être codée en dur.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me-32-bytes-minimum")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
PASSWORD_RESET_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(client_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(client_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_client(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Client:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou expirés",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        client_id = int(payload.get("sub"))
    except (jwt.PyJWTError, TypeError, ValueError) as exc:
        raise credentials_error from exc

    client = db.get(Client, client_id)
    if client is None:
        raise credentials_error
    return client


def generate_reset_token() -> tuple[str, datetime]:
    """Retourne (token, date d'expiration). Le token est à usage unique."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    return token, expires_at


def is_expired(expires_at: datetime) -> bool:
    """Compare une date d'expiration à "maintenant", en gérant le fait que
    SQLite renvoie des datetime naïfs alors que PostgreSQL (prod cible)
    renvoie des datetime avec fuseau — sans ça, la comparaison lève une
    TypeError selon la base utilisée."""
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc)

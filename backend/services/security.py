"""
security.py
-----------
Gestion sécurisée des mots de passe et tokens JWT.
Utilise bcrypt directement (sans passlib) pour éviter les incompatibilités.
"""
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 heures


# ============================================================
# HASHAGE DES MOTS DE PASSE (bcrypt natif)
# ============================================================

def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt."""
    # bcrypt exige des bytes, on encode en UTF-8
    pwd_bytes = password.encode('utf-8')
    # salt généré automatiquement, 12 rounds 
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe en clair contre un hash bcrypt."""
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


# ============================================================
# JWT TOKENS
# ============================================================

def create_access_token(data: dict) -> str:
    """Crée un token JWT avec une date d'expiration."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Décode et valide un token JWT. Retourne None si invalide/expiré."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
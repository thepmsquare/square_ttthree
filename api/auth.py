import hmac
import hashlib
import base64
import time
import json
import secrets
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from api.config import SECRET_KEY, auto_logger
from api.database import get_db
from api.models import Player

# use header for authentication
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

@auto_logger()
def get_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    # pbkdf2_hmac with sha256
    db_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    )
    return f"{salt}:{db_hash.hex()}"

@auto_logger()
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, expected_hash_hex = hashed_password.split(":")
        db_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            plain_password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        )
        return hmac.compare_digest(db_hash.hex(), expected_hash_hex)
    except Exception:
        return False

@auto_logger()
def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = time.time() + 86400  # 1 day expiration
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip("=")
    
    sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode('utf-8').rstrip("=")
    
    return f"{payload_b64}.{sig_b64}"

@auto_logger()
def verify_access_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts
        
        # verify signature first
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip("=")
        
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None
            
        # pad and decode payload
        padded_payload_b64 = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(padded_payload_b64.encode('utf-8')).decode('utf-8')
        payload = json.loads(payload_json)
        
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None

@auto_logger()
async def get_current_player(
    token: str = Depends(api_key_header), 
    db: AsyncSession = Depends(get_db)
) -> Player:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate credentials",
    )
    if not token:
        raise credentials_exception
        
    # extract token value if prefixed with Bearer
    if token.startswith("Bearer "):
        token = token[7:]
        
    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception
        
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
        
    result = await db.execute(select(Player).where(Player.username == username))
    player = result.scalars().first()
    if player is None:
        raise credentials_exception
        
    return player

import hashlib
import hmac
import json
import base64
import time
from typing import Optional, Dict, Any
from backend.config import SECRET_KEY

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hashes password using PBKDF2 with SHA-256 and a cryptographically secure salt."""
    if salt is None:
        import secrets
        salt = secrets.token_hex(16)
    iterations = 100_000
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, iterations)
    return f"{salt}${iterations}${key.hex()}"

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verifies a plain password against the stored salt$iterations$hash."""
    try:
        parts = password_hash.split('$')
        if len(parts) != 3:
            return False
        salt, iterations_str, expected_hash = parts
        iterations = int(iterations_str)
        key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), iterations)
        return hmac.compare_digest(key.hex(), expected_hash)
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta_seconds: int = 86400) -> str:
    """Generates a secure HMAC-SHA256 signed JSON web token."""
    payload = data.copy()
    payload["exp"] = int(time.time()) + expires_delta_seconds
    payload_str = json.dumps(payload, sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode('utf-8')).decode('utf-8').rstrip('=')
    
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        payload_b64.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates token signature and expiry."""
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts
        
        # Verify signature
        expected_sig = hmac.new(
            SECRET_KEY.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Pad base64 if needed
        sig_padding = '=' * (4 - len(sig_b64) % 4) if len(sig_b64) % 4 else ''
        actual_sig = base64.urlsafe_b64decode(sig_b64 + sig_padding)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        payload_padding = '=' * (4 - len(payload_b64) % 4) if len(payload_b64) % 4 else ''
        payload_json = base64.urlsafe_b64decode(payload_b64 + payload_padding).decode('utf-8')
        payload = json.loads(payload_json)
        
        if payload.get("exp", 0) < time.time():
            return None  # Token expired
        
        return payload
    except Exception:
        return None

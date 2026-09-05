from typing import List, Optional
from fastapi import Header, HTTPException, status, Depends
from backend.auth.security import decode_access_token
from backend.database.db import get_db

ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_CASHIER = "cashier"

ROLE_HIERARCHY = {
    ROLE_ADMIN: [ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER],
    ROLE_MANAGER: [ROLE_MANAGER, ROLE_CASHIER],
    ROLE_CASHIER: [ROLE_CASHIER]
}

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency that extracts and validates user from Authorization: Bearer <token>."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required"
        )
    
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'"
        )
    
    token = parts[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )
    
    user_id = payload.get("sub")
    conn = get_db()
    try:
        cur = conn.execute("SELECT id, username, full_name, role FROM users WHERE id = ?", (user_id,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return dict(user)
    finally:
        conn.close()

def require_roles(allowed_roles: List[str]):
    """Returns a dependency function verifying user has one of allowed_roles."""
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles and user_role != ROLE_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

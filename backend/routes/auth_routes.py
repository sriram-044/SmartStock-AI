from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from backend.database.db import get_db, transaction
from backend.auth.security import verify_password, hash_password, create_access_token
from backend.auth.roles import get_current_user, require_roles, ROLE_ADMIN

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role: str

@router.post("/login")
def login(req: LoginRequest):
    """Authenticates user and returns signed access token and role."""
    conn = get_db()
    try:
        cur = conn.execute("SELECT * FROM users WHERE username = ?", (req.username.strip(),))
        user = cur.fetchone()
        if not user or not verify_password(req.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        token = create_access_token({"sub": user["id"], "username": user["username"], "role": user["role"]})
        
        # Get shop settings
        s_cur = conn.execute("SELECT * FROM settings LIMIT 1")
        settings_row = s_cur.fetchone()
        shop_info = dict(settings_row) if settings_row else {}

        return {
            "access_token": token,
            "token_type": "Bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user["role"]
            },
            "shop": shop_info
        }
    finally:
        conn.close()

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Returns currently authenticated user profile."""
    return current_user

@router.post("/register")
def register(req: RegisterRequest, current_user: dict = Depends(require_roles([ROLE_ADMIN]))):
    """Admin-only: Registers a new cashier, manager, or admin user."""
    if req.role not in ['admin', 'manager', 'cashier']:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin', 'manager', or 'cashier'")
        
    with transaction() as conn:
        cur = conn.execute("SELECT id FROM users WHERE username = ?", (req.username.strip(),))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail=f"Username '{req.username}' already exists")
            
        pwd_hash = hash_password(req.password)
        conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (req.username.strip(), pwd_hash, req.full_name, req.role)
        )
    return {"message": f"User '{req.username}' created successfully as '{req.role}'"}

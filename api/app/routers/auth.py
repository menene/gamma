from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Autenticacion"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    name: str


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id, email, name, password_hash, is_active FROM public.users WHERE email = :email"),
        {"email": body.email},
    ).fetchone()

    if not row or not verify_password(body.password, row.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")

    if not row.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario desactivado")

    token = create_token(row.id, row.email)
    return {"token": token, "user": {"id": row.id, "email": row.email, "name": row.name}}


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registro deshabilitado")
    existing = db.execute(
        text("SELECT id FROM public.users WHERE email = :email"),
        {"email": body.email},
    ).fetchone()

    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya esta registrado")

    result = db.execute(
        text("""
            INSERT INTO public.users (email, name, password_hash)
            VALUES (:email, :name, :password_hash)
            RETURNING id
        """),
        {"email": body.email, "name": body.name, "password_hash": hash_password(body.password)},
    )
    db.commit()
    user_id = result.fetchone().id

    token = create_token(user_id, body.email)
    return {"token": token, "user": {"id": user_id, "email": body.email, "name": body.name}}


@router.get("/me", response_model=UserResponse)
def me(user: dict = Depends(get_current_user)):
    return user

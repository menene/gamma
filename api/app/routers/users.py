"""
Administracion de cuentas de usuario.

Todas las rutas exigen privilegios de administrador. Las bajas son logicas: la
fila se marca con deleted_at y nunca se elimina, porque las solicitudes,
conversaciones y decisiones sobre duplicados referencian al usuario que las
creo y el historial perderia trazabilidad.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import hash_password, require_admin
from app.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/users",
    tags=["Usuarios"],
    dependencies=[Depends(require_admin)],
)


# ── Esquemas ──────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    admin: bool
    is_active: bool
    created_at: str | None = None
    deleted_at: str | None = None


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=200)
    admin: bool = False
    is_active: bool = True


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=200)
    admin: bool | None = None
    is_active: bool | None = None


class MessageResponse(BaseModel):
    message: str


# ── Reglas de proteccion ──────────────────────────────────────

def _count_admins(db: Session, excluding: int | None = None) -> int:
    """Administradores vigentes y habilitados, opcionalmente excluyendo a uno."""
    return db.execute(text("""
        SELECT count(*) FROM public.users
         WHERE admin AND is_active AND deleted_at IS NULL
           AND (CAST(:excluding AS bigint) IS NULL OR id <> CAST(:excluding AS bigint))
    """), {"excluding": excluding}).scalar_one()


def _get_or_404(db: Session, user_id: int):
    row = db.execute(text("""
        SELECT id, email, name, admin, is_active, created_at, deleted_at
          FROM public.users WHERE id = :id
    """), {"id": user_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return row


def _row_to_out(r) -> UserOut:
    return UserOut(
        id=r.id, email=r.email, name=r.name,
        admin=bool(r.admin), is_active=bool(r.is_active),
        created_at=r.created_at.isoformat() if r.created_at else None,
        deleted_at=r.deleted_at.isoformat() if r.deleted_at else None,
    )


# ── Endpoints ─────────────────────────────────────────────────

@router.get("", response_model=list[UserOut])
def list_users(include_deleted: bool = False, db: Session = Depends(get_db)):
    """Cuentas registradas. Las dadas de baja se omiten salvo que se pidan."""
    rows = db.execute(text(f"""
        SELECT id, email, name, admin, is_active, created_at, deleted_at
          FROM public.users
         {'' if include_deleted else 'WHERE deleted_at IS NULL'}
         ORDER BY deleted_at NULLS FIRST, name
    """)).fetchall()
    return [_row_to_out(r) for r in rows]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    """Da de alta una cuenta. El correo debe ser unico entre las vigentes."""
    existe = db.execute(text(
        "SELECT 1 FROM public.users WHERE email = :e AND deleted_at IS NULL"
    ), {"e": body.email}).fetchone()
    if existe:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")

    row = db.execute(text("""
        INSERT INTO public.users (email, name, password_hash, admin, is_active)
        VALUES (:email, :name, :hash, :admin, :is_active)
        RETURNING id, email, name, admin, is_active, created_at, deleted_at
    """), {
        "email": body.email, "name": body.name,
        "hash": hash_password(body.password),
        "admin": body.admin, "is_active": body.is_active,
    }).fetchone()
    db.commit()
    logger.info("Cuenta creada: %s (admin=%s)", body.email, body.admin)
    return _row_to_out(row)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_admin),
):
    """
    Modifica una cuenta.

    Dos resguardos impiden que un administrador se deje fuera del sistema:
    no puede retirarse a si mismo el rol, ni desactivar su propia cuenta.
    Tampoco se admite retirar el rol al ultimo administrador que queda.
    """
    actual = _get_or_404(db, user_id)
    if actual.deleted_at is not None:
        raise HTTPException(status_code=409, detail="La cuenta esta dada de baja; restaurela primero")

    propio = actor["id"] == user_id

    if body.admin is False and actual.admin:
        if propio:
            raise HTTPException(status_code=409, detail="No puede retirarse a si mismo el rol de administrador")
        if _count_admins(db, excluding=user_id) == 0:
            raise HTTPException(status_code=409, detail="Debe quedar al menos un administrador activo")

    if body.is_active is False and actual.is_active:
        if propio:
            raise HTTPException(status_code=409, detail="No puede desactivar su propia cuenta")
        if actual.admin and _count_admins(db, excluding=user_id) == 0:
            raise HTTPException(status_code=409, detail="Debe quedar al menos un administrador activo")

    if body.email and body.email != actual.email:
        choca = db.execute(text(
            "SELECT 1 FROM public.users WHERE email = :e AND deleted_at IS NULL AND id <> :id"
        ), {"e": body.email, "id": user_id}).fetchone()
        if choca:
            raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")

    sets, params = [], {"id": user_id}
    for campo in ("email", "name", "admin", "is_active"):
        valor = getattr(body, campo)
        if valor is not None:
            sets.append(f"{campo} = :{campo}")
            params[campo] = valor
    if body.password:
        sets.append("password_hash = :hash")
        params["hash"] = hash_password(body.password)

    if not sets:
        return _row_to_out(actual)

    row = db.execute(text(f"""
        UPDATE public.users SET {', '.join(sets)}
         WHERE id = :id
        RETURNING id, email, name, admin, is_active, created_at, deleted_at
    """), params).fetchone()
    db.commit()
    logger.info("Cuenta %s modificada por el usuario %s", user_id, actor["id"])
    return _row_to_out(row)


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    actor: dict = Depends(require_admin),
):
    """
    Da de baja una cuenta sin borrar la fila.

    El correo queda liberado para volver a usarse, porque la unicidad solo
    aplica entre cuentas vigentes.
    """
    actual = _get_or_404(db, user_id)
    if actual.deleted_at is not None:
        raise HTTPException(status_code=409, detail="La cuenta ya estaba dada de baja")
    if actor["id"] == user_id:
        raise HTTPException(status_code=409, detail="No puede darse de baja a si mismo")
    if actual.admin and _count_admins(db, excluding=user_id) == 0:
        raise HTTPException(status_code=409, detail="Debe quedar al menos un administrador activo")

    db.execute(text("UPDATE public.users SET deleted_at = now() WHERE id = :id"), {"id": user_id})
    db.commit()
    logger.info("Cuenta %s dada de baja por el usuario %s", user_id, actor["id"])
    return MessageResponse(message=f"Cuenta de {actual.name} dada de baja")


@router.post("/{user_id}/restore", response_model=UserOut)
def restore_user(user_id: int, db: Session = Depends(get_db)):
    """Reactiva una cuenta dada de baja, si su correo sigue libre."""
    actual = _get_or_404(db, user_id)
    if actual.deleted_at is None:
        raise HTTPException(status_code=409, detail="La cuenta no esta dada de baja")

    ocupado = db.execute(text(
        "SELECT 1 FROM public.users WHERE email = :e AND deleted_at IS NULL"
    ), {"e": actual.email}).fetchone()
    if ocupado:
        raise HTTPException(
            status_code=409,
            detail="Otra cuenta vigente ya usa ese correo; cambielo antes de restaurar",
        )

    row = db.execute(text("""
        UPDATE public.users SET deleted_at = NULL WHERE id = :id
        RETURNING id, email, name, admin, is_active, created_at, deleted_at
    """), {"id": user_id}).fetchone()
    db.commit()
    logger.info("Cuenta %s restaurada", user_id)
    return _row_to_out(row)

"""
Descarga de los manuales del proyecto.

Los PDF viven en docs/manuales/ y se montan de solo lectura en el contenedor.
No se sirven como archivos estaticos porque el acceso depende del rol: publicar
el archivo bajo una ruta fija lo dejaria al alcance de cualquiera que conociera
la direccion, que es justo lo que se quiere evitar con el manual tecnico y el
de instalacion.
"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/manuales", tags=["Manuales"])

# Directorio montado desde docs/manuales. Se resuelve por variable de entorno
# para no atar el codigo a la disposicion del repositorio.
MANUALES_DIR = os.environ.get("MANUALES_DIR", "/app/manuales")


class Manual(BaseModel):
    slug: str
    titulo: str
    descripcion: str
    solo_admin: bool
    disponible: bool
    size_bytes: int | None = None


# El nombre de carpeta lleva tilde: se declara explicito para no depender de la
# normalizacion unicode del sistema de archivos.
CATALOGO = [
    {
        "slug": "usuario",
        "titulo": "Manual de usuario",
        "descripcion": "El alta de materiales paso a paso, la exportacion a SAP y las preguntas frecuentes.",
        "solo_admin": False,
        "ruta": ("usuario", "manual_usuario.pdf"),
    },
    {
        "slug": "tecnico",
        "titulo": "Manual tecnico",
        "descripcion": "Las secciones de administracion: usuarios, reentrenamiento del modelo y documentacion del sistema.",
        "solo_admin": True,
        "ruta": ("técnico", "manual_tecnico.pdf"),
    },
    {
        "slug": "instalacion",
        "titulo": "Manual de instalacion",
        "descripcion": "Puesta en marcha, actualizacion, respaldos y resolucion de problemas de los contenedores.",
        "solo_admin": True,
        "ruta": ("instalacion", "manual_instalacion.pdf"),
    },
]


def _ruta_absoluta(entrada: dict) -> str:
    return os.path.join(MANUALES_DIR, *entrada["ruta"])


@router.get("", response_model=list[Manual])
def list_manuales(user: dict = Depends(get_current_user)):
    """
    Manuales que el usuario puede descargar.

    Los restringidos ni siquiera se listan a quien no tiene el rol: no tiene
    sentido mostrar una descarga que despues seria rechazada.
    """
    es_admin = bool(user.get("admin"))
    salida: list[Manual] = []

    for entrada in CATALOGO:
        if entrada["solo_admin"] and not es_admin:
            continue
        ruta = _ruta_absoluta(entrada)
        existe = os.path.isfile(ruta)
        salida.append(Manual(
            slug=entrada["slug"],
            titulo=entrada["titulo"],
            descripcion=entrada["descripcion"],
            solo_admin=entrada["solo_admin"],
            disponible=existe,
            size_bytes=os.path.getsize(ruta) if existe else None,
        ))

    return salida


@router.get("/{slug}")
def download_manual(slug: str, user: dict = Depends(get_current_user)):
    """Entrega el PDF, verificando el rol del lado del servidor."""
    entrada = next((m for m in CATALOGO if m["slug"] == slug), None)
    if not entrada:
        raise HTTPException(status_code=404, detail="Manual no encontrado")

    if entrada["solo_admin"] and not user.get("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de administrador",
        )

    ruta = _ruta_absoluta(entrada)
    if not os.path.isfile(ruta):
        raise HTTPException(
            status_code=404,
            detail="El manual todavia no se ha compilado",
        )

    return FileResponse(
        ruta,
        media_type="application/pdf",
        filename=f"GAMMA - {entrada['titulo']}.pdf",
    )

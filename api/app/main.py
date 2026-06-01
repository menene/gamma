from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, chat, etl, duplicates, model

app = FastAPI(
    title="GAMMA API",
    description="Gobierno Automatizado del Maestro de Materiales",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    openapi_tags=[
        {"name": "Autenticacion", "description": "Login, registro y sesion"},
        {"name": "Sistema", "description": "Health check y estado general"},
        {"name": "Chat", "description": "Conversaciones del asistente GAMMA"},
        {"name": "ETL", "description": "Carga de datos desde archivos Excel"},
        {"name": "Duplicados", "description": "Busqueda de duplicados por similitud"},
        {"name": "Modelo", "description": "Categorizacion de materiales con ML"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(etl.router)
app.include_router(duplicates.router)
app.include_router(model.router)


@app.get("/api/health", tags=["Sistema"])
def health():
    return {"status": "ok"}

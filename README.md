# GAMMA: Gobierno Automatizado del Maestro de MAteriales

Plataforma que automatiza el gobierno de datos del maestro de materiales de SAP:
valida duplicados, clasifica la categoría del material y genera la descripción
estandarizada (texto breve), con confirmación humana antes de escribir y
exportación a Excel para carga masiva en SAP. Incluye una capa analítica con
arquitectura medallón y un dashboard de monetización por ahorro de horas-hombre.

Todo corre en Docker. Una landing page sirve como portal documental del proyecto
(presentación, alcance técnico, stack, laboratorio Jupyter y documentación del API).

> Documento de construcción dirigido a Claude Code. Describe qué construir,
> cómo organizarlo y con qué contrato. Donde diga *stub*, se implementa una
> versión mínima funcional con la interfaz definida, no la lógica final.

---

## 1. Alcance

### Dentro de alcance
- API REST (FastAPI) con tres servicios: validación de duplicados, categorización y generación de descripción.
- Flujo de solicitud con confirmación humana y persistencia en base de datos.
- Exportación a Excel para carga masiva en SAP.
- Base de datos PostgreSQL con arquitectura medallón (bronze / silver / gold) más esquema operacional.
- Landing page documental con secciones y embeds (Jupyter Lab y docs del API).
- Servicio de laboratorio (Jupyter Lab) para experimentación.
- Orquestación completa con Docker Compose.

### Fuera de alcance (de esta construcción)
- El modelo de categorización es una **caja negra** desarrollada por otra persona del equipo. Aquí solo se construye el **servicio que lo expone** con un contrato fijo y un *stub* de predicción.
- El dashboard de Power BI no se construye con código; se conecta externamente al esquema `gold`. Aquí solo se garantizan las tablas/vistas que consume.
- El etiquetado del maestro (asignación de categorías de referencia) se asume disponible como insumo.

---

## 2. Arquitectura

Dos planos sobre la misma instancia de PostgreSQL.

**Plano operacional (creación del material):**
`Chatbot/Frontend` → `API REST` → { `Duplicados`, `Categorización`, `Descripción` } → `Confirmación humana` → `Staging` → `Exportador Excel` → `SAP`.

**Plano analítico:**
`Staging + logs` → `Bronze` → `Silver` → `Gold` → `Power BI`. `Silver` alimenta además los datasets de entrenamiento y prueba del modelo.

El API es agnóstico al frontend: el chatbot es un cliente más; cualquier cliente puede consumir los mismos endpoints.

---

## 3. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Orquestación | Docker + Docker Compose |
| Base de datos | PostgreSQL 16 (extensión `pg_trgm` para similitud difusa en duplicados) |
| API / Backend | Python 3.12, FastAPI, Uvicorn, SQLAlchemy, Pydantic v2, psycopg |
| Servicio de modelo | Python 3.12, FastAPI (caja negra con contrato `/predict`) |
| LLM | API externa (Gemini o equivalente) vía SDK/HTTP, para la generación de descripción |
| Exportación | pandas, openpyxl |
| Laboratorio | Jupyter Lab (imagen `jupyter/scipy-notebook` o equivalente) |
| Frontend / landing | Vite + React + Tailwind, servido por Nginx en producción |
| Analítica | Power BI (externo, conectado al esquema `gold`) |

---

## 4. Estructura del repositorio

```
.
├── docker-compose.yml
├── .env.example
├── README.md
├── db/
│   └── init/
│       ├── 00_extensions.sql
│       ├── 01_schemas.sql
│       ├── 02_staging.sql
│       ├── 03_bronze.sql
│       ├── 04_silver.sql
│       └── 05_gold.sql
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── core/            # config, settings (.env)
│       ├── db/              # engine, session, queries
│       ├── schemas/         # modelos Pydantic (request/response)
│       ├── services/        # duplicados, categorizacion, descripcion, export
│       └── routers/         # materials, duplicates, export, health
├── model/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       └── main.py          # expone POST /predict (stub)
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/                 # landing page con secciones y embeds
├── lab/
│   ├── Dockerfile
│   └── notebooks/           # notebooks de experimentación
└── exporter/                # opcional; si se separa del API
```

---

## 5. Servicios y puertos

| Servicio | Contenedor | Puerto host | Descripción |
|---|---|---|---|
| `db` | postgres:16 | 5432 | PostgreSQL con esquemas medallón + staging |
| `api` | FastAPI | 8000 | API REST; docs en `/docs` y `/redoc` |
| `model` | FastAPI | 8001 | Servicio de categorización (caja negra, stub) |
| `lab` | Jupyter Lab | 8888 | Laboratorio embebido en la landing |
| `frontend` | Nginx | 8080 | Landing page documental |

Power BI no es un contenedor: se conecta al puerto 5432 contra el esquema `gold`.

---

## 6. Base de datos (esquema medallón)

Convención: `snake_case`, todo en minúsculas, timestamps en UTC. Cuatro esquemas:
`staging` (operacional), `bronze`, `silver`, `gold`.

### `staging` — operacional
```sql
-- staging.solicitudes: ciclo de vida de cada alta de material
CREATE TABLE staging.solicitudes (
    id              BIGSERIAL PRIMARY KEY,
    nombre          TEXT NOT NULL,            -- nombre captado por el chatbot
    texto_largo     TEXT,                     -- descripción completa
    especificaciones JSONB,                   -- material, dimensiones, unidades, etc.
    texto_breve     TEXT,                     -- propuesto por el servicio de descripción
    categoria       TEXT,                     -- propuesta por el modelo
    confianza       NUMERIC(5,4),             -- confianza de la categorización
    duplicados      JSONB,                    -- candidatos detectados
    estado          TEXT NOT NULL DEFAULT 'propuesta'
                    CHECK (estado IN ('propuesta','confirmado','exportado','descartado')),
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    confirmado_en   TIMESTAMPTZ,
    exportado_en    TIMESTAMPTZ,
    duracion_seg    NUMERIC                   -- tiempo de proceso del sistema
);
```

### `bronze` — datos crudos y trazabilidad
```sql
-- bronze.maestro_raw: maestro de materiales tal cual se ingesta
CREATE TABLE bronze.maestro_raw (
    material     TEXT,
    descripcion  TEXT,
    ingerido_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- bronze.prediccion_logs: cada predicción y la decisión del usuario (clave para KPIs)
CREATE TABLE bronze.prediccion_logs (
    id             BIGSERIAL PRIMARY KEY,
    solicitud_id   BIGINT,
    tipo           TEXT,        -- 'duplicado' | 'categoria' | 'descripcion'
    salida_modelo  JSONB,       -- lo que devolvió el servicio
    confianza      NUMERIC(5,4),
    decision_usuario JSONB,     -- lo que el usuario aceptó/corrigió
    registrado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### `silver` — normalizado y datasets
```sql
-- silver.maestro: maestro normalizado; sobre esta tabla corre el query de duplicados
CREATE TABLE silver.maestro (
    material     TEXT PRIMARY KEY,
    descripcion  TEXT NOT NULL,
    categoria    TEXT,                 -- etiqueta de referencia (insumo)
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- índice trigram para similitud difusa en la detección de duplicados
CREATE INDEX idx_maestro_desc_trgm ON silver.maestro
    USING gin (descripcion gin_trgm_ops);

-- silver.solicitudes: solicitudes limpias con tiempos calculados
CREATE TABLE silver.solicitudes (
    id            BIGINT PRIMARY KEY,
    categoria     TEXT,
    confianza     NUMERIC(5,4),
    auto_resuelto BOOLEAN,            -- confianza >= umbral
    correccion    BOOLEAN,           -- el usuario cambió la propuesta
    duracion_seg  NUMERIC,
    confirmado_en TIMESTAMPTZ
);

-- silver.dataset_train / silver.dataset_test: para el modelo (split estratificado)
CREATE TABLE silver.dataset_train (descripcion TEXT, categoria TEXT);
CREATE TABLE silver.dataset_test  (descripcion TEXT, categoria TEXT);
```

### `gold` — agregados para Power BI
```sql
-- Parámetros de monetización (línea base manual y tarifa)
CREATE TABLE gold.parametros (
    clave  TEXT PRIMARY KEY,
    valor  NUMERIC
);
-- Sembrar: t_manual_seg (tiempo manual por material) y tarifa_hora (costo Q/h)
INSERT INTO gold.parametros (clave, valor) VALUES
    ('t_manual_seg', 0),   -- definir con medición real del proceso manual
    ('tarifa_hora', 0);    -- costo por hora-hombre del operador

-- Indicadores de tiempos
CREATE OR REPLACE VIEW gold.kpi_tiempos AS
SELECT
    date_trunc('week', confirmado_en) AS semana,
    count(*)                          AS materiales,
    avg(duracion_seg)                 AS prom_seg_sistema,
    avg(CASE WHEN auto_resuelto THEN 1 ELSE 0 END) AS tasa_auto
FROM silver.solicitudes
WHERE confirmado_en IS NOT NULL
GROUP BY 1;

-- Indicadores de calidad
CREATE OR REPLACE VIEW gold.kpi_calidad AS
SELECT
    date_trunc('week', confirmado_en) AS semana,
    avg(CASE WHEN correccion THEN 0 ELSE 1 END) AS exactitud_categoria,
    avg(confianza)                              AS confianza_prom
FROM silver.solicitudes
WHERE confirmado_en IS NOT NULL
GROUP BY 1;

-- Monetización por ahorro de horas-hombre
CREATE OR REPLACE VIEW gold.monetizacion AS
WITH p AS (
    SELECT
        max(valor) FILTER (WHERE clave='t_manual_seg') AS t_manual,
        max(valor) FILTER (WHERE clave='tarifa_hora')  AS tarifa
    FROM gold.parametros
)
SELECT
    date_trunc('week', s.confirmado_en) AS semana,
    count(*) AS materiales,
    sum(greatest(p.t_manual - s.duracion_seg, 0)) / 3600.0       AS horas_ahorradas,
    (sum(greatest(p.t_manual - s.duracion_seg, 0)) / 3600.0) * p.tarifa AS ahorro_q
FROM silver.solicitudes s CROSS JOIN p
WHERE s.confirmado_en IS NOT NULL
GROUP BY 1, p.t_manual, p.tarifa;
```

> La monetización depende de `t_manual_seg` (línea base del proceso manual) y de
> registrar `duracion_seg` y `confirmado_en` en cada solicitud. Sin esos datos
> el indicador no se puede calcular.

---

## 7. Contrato del API

Base: `/api`. Documentación automática en `/docs` (Swagger) y `/redoc`.

### Salud
```
GET /api/health  ->  { "status": "ok" }
```

### Crear solicitud (ejecuta los tres servicios y devuelve propuesta)
```
POST /api/materials/requests
Body:
{
  "nombre": "rodamiento de bolas 6204",
  "texto_largo": "RODAMIENTO RIGIDO DE BOLAS 6204 2RS ACERO 20x47x14 MM SKF",
  "especificaciones": { "material": "acero", "dimensiones": "20x47x14 mm" }
}
Respuesta 201:
{
  "id": 123,
  "duplicados": [
    { "material": "21030045", "descripcion": "RODAMIENTO 6204 2RS", "score": 0.82 }
  ],
  "categoria": { "valor": "RODAMIENTOS", "confianza": 0.93, "auto_resuelto": true,
                 "top_k": [["RODAMIENTOS",0.93],["TRANSMISION",0.04]] },
  "texto_breve": "RODAMIENTO;ACERO;6204;2RS;20X47X14MM;SKF",
  "estado": "propuesta"
}
```

### Confirmar (escribe definitivo en staging; permite edición del usuario)
```
POST /api/materials/requests/{id}/confirm
Body (campos opcionales, sobreescriben la propuesta):
{ "categoria": "RODAMIENTOS", "texto_breve": "RODAMIENTO;ACERO;6204;2RS;20X47X14MM;SKF" }
Respuesta 200: { "id": 123, "estado": "confirmado" }
```

### Endpoints individuales (reutilizables por cualquier cliente)
```
POST /api/materials/validate    Body: { "descripcion": "..." }  -> { "candidatos": [...] }
POST /api/materials/categorize  Body: { "descripcion": "..." }  -> { "valor": "...", "confianza": .., "top_k": [...] }
POST /api/materials/describe    Body: { "texto_largo": "..." }  -> { "texto_breve": "...", "faltantes": [...] }
```

### Listado y exportación
```
GET  /api/materials/requests?estado=confirmado   -> [ ... ]
GET  /api/export/excel                            -> archivo .xlsx (confirmados no exportados),
                                                     marca esos registros como 'exportado'
```

### Lógica interna
- **validate**: query a `silver.maestro` combinando igualdad e `ILIKE` con similitud `pg_trgm` (`similarity(descripcion, :q) > umbral`), ordenado por score; devuelve top-N candidatos.
- **categorize**: llama a `POST http://model:8001/predict`; aplica umbral de confianza para marcar `auto_resuelto`; registra en `bronze.prediccion_logs`.
- **describe**: llama al LLM externo con un prompt que aplica el estándar (palabra clave inicial, máx. 40 caracteres, abreviaturas de material, separadores `;`, sin texto de relleno); si falta una especificación clave la reporta en `faltantes` en lugar de inventarla.
- Cada `POST /requests` debe registrar `creado_en`; `confirm` registra `confirmado_en` y calcula `duracion_seg`.

---

## 8. Servicio del modelo (caja negra)

`model/app/main.py` expone el contrato que el equipo de modelado debe respetar.
De momento es un *stub* que devuelve una categoría fija con confianza simulada.

```
POST /predict
Body:     { "descripcion": "texto del material" }
Respuesta: { "categoria": "RODAMIENTOS", "confianza": 0.93,
             "top_k": [["RODAMIENTOS",0.93],["TRANSMISION",0.04]] }
```

El API nunca conoce el modelo interno: solo este contrato. Cambiar el modelo
(red neuronal, baseline clásico, lo que gane) no debe requerir cambios en el API.

---

## 9. Landing page (portal documental)

SPA en Vite + React + Tailwind, servida por Nginx. Una sola página con navegación
por secciones (ancla) más rutas dedicadas para los embeds. Diseño limpio, claro
sobre fondo blanco. Secciones:

1. **Presentación** — qué resuelve el proyecto y el flujo de extremo a extremo (incluir el diagrama de arquitectura como imagen).
2. **Alcance técnico** — dentro/fuera de alcance, los dos planos (operacional y analítico), el ciclo de vida de una solicitud.
3. **Stack tecnológico** — tabla del stack y justificación breve de cada elección.
4. **Laboratorio** — Jupyter Lab embebido vía `<iframe src="http://localhost:8888">` (o proxy `/lab`).
5. **Documentación del API** — Swagger embebido vía `<iframe src="http://localhost:8000/docs">` y enlace a `/redoc`.
6. **Documentación** — sección que centraliza la información documental del proyecto (decisiones de diseño, esquema de datos, contrato del API, guía de despliegue).

Nginx debe servir el build estático y, opcionalmente, hacer de *reverse proxy*
de `/api`, `/lab` y `/model` para evitar problemas de CORS y puertos cruzados.

---

## 10. Docker Compose

`docker-compose.yml` orquesta los cinco servicios en una red interna. Esquema:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    ports: ["5432:5432"]
    volumes:
      - dbdata:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d   # se ejecuta solo en volumen vacío
  api:
    build: ./api
    env_file: .env
    depends_on: [db, model]
    ports: ["8000:8000"]
  model:
    build: ./model
    ports: ["8001:8001"]
  lab:
    build: ./lab
    volumes: ["./lab/notebooks:/home/jovyan/work"]
    ports: ["8888:8888"]
  frontend:
    build: ./frontend
    depends_on: [api, lab]
    ports: ["8080:80"]
volumes:
  dbdata:
```

> Los scripts de `db/init` solo corren cuando el volumen está vacío. Si cambia el
> esquema, recrear con `docker compose down -v` antes de `up`.

---

## 11. Variables de entorno (`.env.example`)

```
DB_USER=gamma
DB_PASSWORD=cambia_esto
DB_NAME=gamma
DB_HOST=db
DB_PORT=5432

MODEL_SERVICE_URL=http://model:8001
CONFIANZA_UMBRAL=0.80
DUPLICADO_UMBRAL=0.45

LLM_API_KEY=
LLM_MODEL=
```

---

## 12. Puesta en marcha

```bash
cp .env.example .env          # completar credenciales y llaves
docker compose up --build
```

- Landing page: http://localhost:8080
- API + Swagger: http://localhost:8000/docs
- Jupyter Lab: http://localhost:8888
- PostgreSQL: localhost:5432 (Power BI se conecta aquí, esquema `gold`)

---

## 13. Hoja de ruta de implementación (orden sugerido para Claude Code)

1. Esqueleto del repo y `docker-compose.yml` con los cinco servicios levantando.
2. `db/init`: extensiones, esquemas y tablas/vistas (sección 6).
3. Servicio `model` con el *stub* `/predict` (sección 8).
4. API: configuración, conexión a BD, `/health`, y los tres servicios (`validate`, `categorize`, `describe`).
5. API: ciclo de solicitud (`POST /requests`, `confirm`) con registro de tiempos y logs en `bronze`.
6. API: exportación a Excel (`/export/excel`).
7. Job/proceso que promueve datos de `staging` → `bronze` → `silver` y refresca lo necesario para `gold`.
8. Frontend: landing con las seis secciones y los embeds de Jupyter y Swagger.
9. Notebooks base en `lab/` para experimentación con datasets de `silver`.
10. Verificación de extremo a extremo: solicitud desde el frontend → confirmación → exportación → vistas `gold` con datos.

---

## 14. Criterios de aceptación

- `docker compose up` levanta todos los servicios sin intervención manual.
- Una solicitud completa puede crearse, confirmarse y exportarse a un `.xlsx` válido.
- `validate` detecta duplicados evidentes del maestro; `categorize` responde con confianza y umbral; `describe` respeta el límite de 40 caracteres y el formato.
- Las vistas de `gold` devuelven datos y `gold.monetizacion` calcula el ahorro en quetzales una vez sembrados los parámetros.
- La landing page muestra las seis secciones con los embeds funcionando.

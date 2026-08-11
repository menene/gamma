# GAMMA — Pendientes técnicos

Trabajo identificado pero no incluido en el alcance de la primera fase del proyecto
(documentado en el capítulo de Alcance como evolución técnica prevista).

---

## 1. Endpoint de reentrenamiento del modelo de clasificación

**Estado:** pendiente
**Prioridad:** alta — es la única vía para que el modelo mejore con el uso
**Registrado:** 11 de agosto de 2026

### Problema

El modelo se despliega hoy como un artefacto estático:
`api/app/model/model_artifact_v1.joblib`, cargado una sola vez al arrancar el
proceso (`api/app/routers/model.py`, función `_get_artifact()`).

Esto significa que las correcciones que los gestores hacen sobre las sugerencias
del modelo —registradas en `silver.requests.corrected` y en la categoría final
confirmada— **no se aprovechan**. Se está acumulando señal de entrenamiento de
alta calidad, etiquetada por expertos y sin costo de anotación, que actualmente
no se usa.

### Solución propuesta

Un endpoint `POST /api/model/retrain` que ejecute un pipeline de reentrenamiento
con versionado del artefacto.

**Pasos del pipeline:**

1. **Archivar el modelo vigente.**
   Mover `model_artifact_v1.joblib` a un directorio de versiones
   (`api/app/model/archive/model_artifact_<version>_<timestamp>.joblib`).
   Nunca sobreescribir sin respaldo: si el modelo nuevo resulta peor, hay que
   poder revertir.

2. **Construir el dataset de entrenamiento.**
   Unir el maestro histórico (`silver.materials`) con las solicitudes
   confirmadas (`silver.requests` con `status = 'confirmed'`), usando la
   categoría final que quedó registrada —no la que el modelo sugirió—. Aplicar
   el mismo filtro de clases con representación mínima que se usó en el
   entrenamiento original.

3. **Reproducir el preprocesamiento.**
   Reutilizar `preprocess_text()` de `api/app/routers/model.py`. Es crítico que
   el preprocesamiento de entrenamiento y el de inferencia sean idénticos; hoy
   lo son porque la función está duplicada del notebook, y conviene extraerla a
   un módulo compartido para que no puedan divergir.

4. **Entrenar y evaluar.**
   Pipeline ganador actual: `TfidfVectorizer(analyzer='char_wb',
   ngram_range=(2,5), max_features=50000, sublinear_tf=True)` +
   `CalibratedClassifierCV(LinearSVC(C=1.0), cv=3)`.
   Evaluar sobre partición estratificada de prueba y registrar accuracy,
   F1 macro, F1 weighted y top-3.

5. **Compuerta de calidad.**
   Promover el modelo nuevo **solo si** iguala o supera al vigente en las
   métricas registradas. Si no, conservar el anterior y reportar el intento.
   Sin esta compuerta, un reentrenamiento con datos sesgados puede degradar
   el sistema en silencio.

6. **Reentrenar sobre el total y publicar.**
   Una vez aprobada la compuerta, reentrenar con el 100% de los datos, generar
   el nuevo `.joblib` con su metadata (métricas, número de clases, número de
   muestras, fecha) y recargar el artefacto en memoria sin reiniciar el
   servicio (invalidar `_artifact`).

7. **Registrar la ejecución.**
   Dejar traza en una tabla de auditoría: fecha, usuario que lo disparó,
   tamaño del dataset, métricas obtenidas, decisión de la compuerta y ruta del
   artefacto archivado.

### Consideraciones

- **Control de acceso:** restringir a usuarios administradores. Es una
  operación costosa y con impacto directo en producción.
- **Ejecución asíncrona:** el entrenamiento del modelo ganador toma ~63 s sobre
  39,571 materiales, demasiado para una petición HTTP síncrona. Conviene
  ejecutarlo en segundo plano y exponer el estado por otro endpoint.
- **Riesgo de realimentación:** si el modelo se reentrena con sus propias
  sugerencias aceptadas sin revisión, refuerza sus propios sesgos. Considerar
  entrenar únicamente con los casos que el gestor **corrigió** o confirmó de
  forma explícita, y ponderarlos frente al histórico.

### Archivos involucrados

| Archivo | Cambio |
|---|---|
| `api/app/routers/model.py` | Nuevo endpoint; extraer `preprocess_text()` a módulo compartido |
| `api/app/services/` | Nuevo módulo con el pipeline de reentrenamiento |
| `db/migrations/` | Tabla de auditoría de reentrenamientos |
| `api/app/model/archive/` | Directorio de versiones archivadas |
| `frontend/src/pages/` | Vista de administración para disparar y monitorear |

---

## 2. Extensión del modelo a las demás unidades de negocio

**Estado:** pendiente, fuera del alcance del proyecto de graduación
**Depende de:** validación completa en la unidad piloto

El modelo actual se entrenó y validó sobre el catálogo de una sola unidad de
negocio. Una vez confirmado su desempeño en producción, la extensión al resto de
la corporación requiere decidir si se entrena un modelo por unidad o un modelo
único sobre el catálogo consolidado, y evaluar si las taxonomías internas de las
distintas unidades son compatibles entre sí.

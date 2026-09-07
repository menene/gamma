# GAMMA — Lo que construimos, el experimento y el modelo ganador

---

## 1. Lo que construimos

GAMMA (Gobierno Automatizado del Maestro de Materiales) es una plataforma de asistencia inteligente que interviene en el flujo de creación individual de materiales sobre SAP de una unidad de negocio del sector energético con operación en Centroamérica y el Caribe. No escribe en SAP ni sustituye al gestor: lo asiste en el momento exacto de la decisión y conserva la validación humana antes del registro.

El punto de partida fue un catálogo de 45,397 materiales distribuidos en trece tipos, con hasta 1,538 categorías posibles, donde cada solicitud de creación permanecía en promedio 3.3 horas dentro del rol del gestor y donde no existía ningún mecanismo automatizado que indicara si un material ya existía o qué categoría le correspondía.

### El diagrama de arquitectura

Se presenta el diagrama publicado en la propia plataforma, en la sección **Arquitectura** (`/arquitectura`). El diagrama se lee de arriba hacia abajo y muestra tres planos superpuestos:

- **Plano de acceso (arriba).** El frontend en Vue 3 —login, chatbot, ETL y exportador— entra por Nginx, que actúa como proxy inverso y donde se resuelve la autenticación con JWT. Ninguna petición llega a los servicios internos sin pasar por ahí.
- **Plano de servicios (centro).** El API REST en FastAPI orquesta el flujo y se ramifica en los tres módulos analíticos: **Duplicados** (`pg_trgm` sobre PostgreSQL), **Categorización** (el modelo de aprendizaje automático) y **Normalización** (que consume Gemini como servicio externo por API). Los tres convergen en el nodo de **Confirmación humana**, que es el punto donde el gestor valida y sin el cual nada avanza.
- **Plano de datos (abajo).** El bloque punteado que agrupa a PostgreSQL 16 con las tres capas del medallón —bronze, silver y gold— sobre una sola instancia.

Es el mismo diagrama que la plataforma expone a sus usuarios, no una versión hecha para la presentación: la documentación de arquitectura vive dentro del propio sistema.

### La plataforma

Cuatro servicios orquestados con Docker Compose en una red interna:

- **Base de datos** — PostgreSQL 16 con la extensión `pg_trgm` habilitada. Sostiene el repositorio medallón y el motor de similitud difusa.
- **API** — FastAPI sobre Python 3.12, con SQLAlchemy y Pydantic v2. Concentra la lógica de negocio, la autenticación, la ingesta y la inferencia del modelo de clasificación.
- **Laboratorio** — un Jupyter Lab montado dentro del mismo despliegue, protegido con token, para la experimentación analítica sobre los mismos datos que consume la plataforma.
- **Frontend** — aplicación de página única en Vue 3 con Vite, Tailwind y shadcn, servida por Nginx, que además actúa como proxy inverso hacia los demás servicios.

Con la única excepción del servicio de modelo de lenguaje, que opera bajo esquema de pago por uso, la totalidad de la infraestructura es software de código abierto.

---

### La arquitectura medallón

El repositorio de datos se implementó siguiendo una **arquitectura medallón de tres capas sobre una sola instancia de PostgreSQL**. La idea de fondo es que el dato no se transforma en el mismo lugar donde se consulta: cada capa tiene una responsabilidad distinta, y el paso de una a otra es lo que hace que el sistema sea auditable.

#### Bronze — ingesta y trazabilidad

Bronze es la capa de llegada y la memoria del sistema. Cumple dos funciones.

La primera es **recibir los datos crudos**: los archivos exportados desde SAP entran tal cual se importan, con su marca de tiempo de ingesta. No se corrige nada en esta capa. Si un archivo llega con columnas repetidas, con valores compuestos de código y descripción, o con filas defectuosas, así queda registrado.

La segunda es **registrar todo lo que el sistema hace**. Bronze almacena:

- `ingestion_logs` — una fila por archivo importado, con el nombre del archivo, el número de filas procesadas, el estado resultante (`success`, `partial`, `failed`), el mensaje de error si lo hubo y el tiempo transcurrido.
- `prediction_logs` — una fila por cada predicción del sistema, tipificada según el módulo que la produjo (duplicados, descripción o categorización), con la entrada, la salida, la confianza, el tiempo transcurrido y la decisión que el usuario tomó sobre ella.
- `duplicate_logs` — cada decisión sobre duplicados: si el gestor aceptó o rechazó, cuál fue el material seleccionado, el conjunto completo de candidatos que se le presentó y cuánto tardó en decidir.
- `llm_logs` — cada interacción con el modelo de lenguaje: la instrucción de sistema, el mensaje del usuario, la longitud del historial, la respuesta cruda, la respuesta interpretada, el consumo de tokens y la latencia.
- `app_errors` — los errores de aplicación, con su origen y detalle.

Esa separación es la que permite afirmar que **la trazabilidad no fue un añadido posterior sino una propiedad estructural**: cualquier registro del maestro puede auditarse hasta el archivo del que provino, y cualquier sugerencia que el sistema hizo puede reconstruirse con la entrada que la produjo y la decisión que recibió.

#### Silver — la capa operacional

Silver es donde el dato ya está limpio, normalizado y relacionado, y es **la única capa sobre la que el API lee y escribe en operación**.

Aquí ocurre el trabajo de transformación:

- **Mapeo de esquema.** Se aplica un mapeo explícito entre los encabezados originales de la exportación de SAP y los campos del modelo de datos. Se resuelven los casos en que la exportación repite un mismo nombre de columna, y se extraen los códigos de aquellos campos que llegan como valores compuestos de código y descripción separados por un guion.
- **Resolución de llaves foráneas.** Durante la carga, cada material se vincula con su clase y su unidad de medida, y cada clase con su tipo de material y su código UNSPSC. El resultado es que los trece archivos dispersos quedan consolidados en un modelo relacional único.
- **Carga idempotente.** La ingesta opera por `UPSERT`, de modo que reprocesar un archivo actualiza en lugar de duplicar.
- **Indexación para similitud.** Sobre la columna de texto breve del maestro se construye un índice invertido de trigramas. Es lo que hace viable la detección de duplicados: sin ese índice, comparar una descripción contra decenas de miles de registros exigiría un recorrido completo de la tabla en cada solicitud.

Silver contiene los catálogos de referencia (`material_types`, `classes`, `units_of_measure`, `unspsc`), el maestro de materiales (`materials`), las conversaciones del chatbot, las solicitudes de alta con su ciclo de vida completo (`requests`), los conjuntos de entrenamiento y prueba, y el registro de versiones del modelo.

#### Gold — la capa de indicadores

Gold **no almacena datos**: son vistas calculadas en tiempo real sobre silver. Esa decisión importa porque significa que el tablero nunca puede desincronizarse de la operación —no hay un proceso de refresco que pueda fallar y dejar cifras viejas—.

Las vistas agregan por semana:

- `kpi_processing_time` — tiempos de procesamiento, desglosados por módulo (LLM, duplicados, predicción) más el tiempo de revisión del usuario, y la tasa de resolución automática.
- `kpi_quality` — la calidad de las predicciones: tasa de acierto derivada de las correcciones del gestor, confianza promedio, coincidencias con material existente y número de correcciones.
- `kpi_step_breakdown` — el desglose de tiempo por etapa del proceso.
- `kpi_duplicates` — duplicados presentados frente a duplicados aceptados.
- `kpi_savings` — el ahorro estimado en horas y en quetzales.
- `requests_users`, `kpi_requests_by_user`, `materials_by_type` — la actividad por gestor y la distribución por tipo de material.

Dos detalles de diseño de esta capa:

**El cálculo del ahorro está parametrizado.** Existe una tabla `gold.parameters` que almacena el tiempo de referencia del proceso manual y el costo por hora del gestor. El indicador se recalcula ante un cambio de supuestos sin modificar la definición de la vista, lo que evita tener que reescribir SQL cada vez que la organización revisa sus costos.

**Todas las vistas excluyen sistemáticamente la actividad de las cuentas administrativas.** Esta exclusión es deliberada: el tráfico generado durante el desarrollo, las pruebas y las demostraciones contaminaría las mediciones de tiempo y de calidad si se agregara junto al uso productivo del equipo de gestores.

#### Por qué un motor relacional

La elección de PostgreSQL en lugar de una plataforma distribuida responde al volumen: un catálogo de decenas de miles de registros no justifica la complejidad operativa de un entorno de procesamiento distribuido. Y permite además **resolver la detección de duplicados dentro del mismo motor**, sin necesidad de un servicio de búsqueda externo. La medición en producción lo confirmó: 1.78 segundos promedio por búsqueda difusa sobre el maestro completo.

---

### El API: cómo se democratizó el modelo

El API es la pieza que convierte un experimento en una herramienta, y vale la pena detenerse en por qué se implementó así.

**El problema que resuelve.** Un modelo entrenado es un archivo serializado. En esa forma solo puede usarlo alguien que tenga Python instalado, las mismas versiones de las bibliotecas con que se entrenó, una copia del artefacto y —crítico— la misma función de preprocesamiento de texto. Es decir: solo el equipo que lo construyó. Un modelo en ese estado no es una herramienta de la organización, es un activo de sus autores.

Exponerlo detrás de un **endpoint HTTP** (`/api/model/predict`) cambia eso por completo. El modelo pasa a ser un servicio que cualquier cliente puede consumir enviando una descripción y recibiendo una categoría, su confianza y las alternativas. El gestor lo usa desde el chatbot sin saber que existe; el frontend lo consume desde el navegador; cualquier sistema futuro de la organización puede integrarlo sin instalar nada ni conocer scikit-learn. **Esa fue la mejor forma de democratizar el modelo**: no distribuir el artefacto, sino publicar la capacidad.

**Lo que el API garantiza además de la disponibilidad:**

- **Consistencia del preprocesamiento.** El API importa exactamente la misma función de normalización de texto que se usó en el entrenamiento. Es la única forma de asegurar que nadie consulte el modelo con texto preparado de otra manera —un error que degrada el desempeño de forma silenciosa, sin producir ningún error visible—.
- **Una sola versión vigente para todos.** Todos los consumidores hablan con el mismo artefacto. No existe la posibilidad de que dos personas obtengan predicciones distintas porque tienen copias diferentes del modelo.
- **Control de acceso.** Todas las rutas del API, salvo la de salud, exigen token JWT. El modelo no queda expuesto ni al uso anónimo ni fuera de la sesión de un usuario identificado.
- **Registro automático.** Cada predicción queda registrada en bronze con su entrada, su salida, su confianza y su latencia. La instrumentación no depende de que quien consume el modelo se acuerde de registrar nada.
- **Orquestación.** El API no solo sirve el modelo: coordina el flujo completo —normalización, duplicados, categorización—, escribe en silver y registra en bronze. El modelo es una pieza dentro de una secuencia, no un servicio suelto.

**Por qué la inferencia va dentro del API y no en un servicio aparte.** El artefacto se carga en memoria una sola vez al arrancar el proceso y se reutiliza en cada predicción. Se elimina la latencia de red entre servicios y la complejidad operativa de un componente adicional, a cambio de acoplar el ciclo de vida del modelo al del API. La medición en producción confirmó que era la decisión correcta: la clasificación consume 0.09 segundos, el 1.5 % del tiempo de máquina de una solicitud. No había nada que ganar separándola.

El API expone además su propia documentación interactiva, integrada en el frontend, de modo que la interfaz del modelo es autodescriptiva para quien quiera consumirla.

---

### Los tres módulos analíticos

**Normalización de descripciones mediante modelo de lenguaje.** Se resolvió con un LLM consumido por interfaz de programación en lugar de un motor de reglas y diccionarios de abreviatura, porque un diccionario exigiría mantenimiento manual permanente conforme aparecen materiales de familias nuevas. Se configuró con temperatura baja, para privilegiar la consistencia sobre la variedad en la redacción, y con respuesta forzada en formato JSON, de manera que su salida se consuma programáticamente sin análisis sintáctico frágil. La instrucción de sistema codifica cuatro elementos: las reglas de la convención corporativa de nomenclatura basada en ISO 8000 —límite de cuarenta caracteres, estructura de tipo y subtipo seguida de atributos, mayúsculas, ausencia de tildes y abreviaturas estándar—; un conjunto de ejemplos tomados del propio maestro que operan como demostraciones en contexto; el catálogo de tipos de material vigente, inyectado dinámicamente desde la base de datos; y un protocolo de comportamiento ante información incompleta.

Ese último elemento fue una decisión de diseño deliberada: el modelo tiene instruido **no inventar especificaciones ausentes**. Cuando la descripción que recibe es insuficiente, en lugar de completar con valores plausibles devuelve una lista estructurada de los campos que faltan. Se definieron además reglas de dominio explícitas, como la obligatoriedad del material de fabricación para materiales físicos y la restricción de solicitar marca y modelo únicamente cuando se trata de repuestos o componentes en los que la marca es indispensable. El diseño busca que el modelo **falle por omisión y no por invención**, que es el modo de falla aceptable en un proceso de gobierno de datos.

**Detección de duplicados por similitud difusa.** Consulta ejecutada directamente sobre el maestro normalizado, aprovechando `pg_trgm` y el índice de trigramas. Calcula el coeficiente de similitud entre la descripción propuesta y cada descripción del catálogo, retiene las que superan un umbral configurable y devuelve las diez coincidencias de mayor puntaje.

El umbral se estableció en un valor deliberadamente permisivo, bajo el criterio de que en una herramienta de asistencia el costo de un falso positivo —que el gestor descarte una sugerencia irrelevante— es sustancialmente menor que el de un falso negativo, que se materializa en un duplicado creado y en el costo recurrente de arrastrarlo en el catálogo.

Cuando la consulta arroja coincidencias, estas no se presentan como lista cruda: se devuelven al modelo de lenguaje, que las expone en el contexto de la conversación señalando las diferencias relevantes entre el material propuesto y los candidatos. La decisión del gestor —aceptar uno de los materiales existentes o sostener que el suyo es distinto— se registra explícitamente, junto con el conjunto de candidatos que se le presentó y el tiempo que tomó decidir.

**Clasificación de categoría.** El clasificador supervisado entrenado sobre el histórico del catálogo, que es el objeto de las secciones 2, 3 y 4.

### Ciclo de vida de una solicitud

Una solicitud se crea en estado **pendiente** en el momento en que el modelo de lenguaje produce una propuesta de descripción normalizada. A partir de ahí puede **confirmarse**, cuando el gestor valida descripción y categoría; **descartarse**, cuando no procede; o **cerrarse como coincidencia** con un material existente, cuando la revisión de duplicados determina que ya está en el catálogo. Las confirmadas transitan finalmente a **exportada** una vez incluidas en el archivo de entrega.

Ese último estado materializa el punto de contacto con SAP: las solicitudes validadas se consolidan en un archivo de hoja de cálculo con la descripción normalizada, la descripción extendida, el tipo de material, la clase asignada y las marcas de tiempo del proceso. Ese archivo es el insumo con el que el material se registra en el ERP. La plataforma no escribe en SAP en ningún momento, y esa separación es deliberada: constituye el mecanismo de supervisión humana sobre el que se diseñó la solución.

### Instrumentación

La medición del efecto no se resolvió de forma retrospectiva sino instrumentando el sistema desde su diseño, de modo que cada solicitud dejara registro de su propio recorrido. Cada una almacena marcas de tiempo diferenciadas para su creación, la finalización de la normalización, la finalización de la búsqueda de duplicados, la decisión sobre los duplicados presentados, la finalización de la predicción de categoría, y su confirmación, descarte o exportación. Esta granularidad permite separar dos magnitudes que de otro modo quedarían confundidas: **el tiempo que consume la máquina y el tiempo que consume la deliberación del gestor**.

Se registra asimismo la calidad de la sugerencia: cuando la clase que el gestor selecciona difiere de la que el modelo propuso, la solicitud queda marcada como corregida, lo que permite estimar la exactitud del modelo en operación real sobre datos que no formaron parte de su evaluación. Se registra también si la sugerencia superó el umbral de confianza y la confianza efectivamente obtenida.

### Reentrenamiento

Se dejó implementado un pipeline de reentrenamiento operable desde la plataforma, con versionado de artefactos y posibilidad de revertir a una versión anterior sin reiniciar el servicio.

---

## 2. El experimento

### Construcción del conjunto de modelado

Sobre el maestro consolidado se aplicaron dos criterios de exclusión: se descartaron los materiales sin categoría asignada en la fuente, por no poder emplearse ni para entrenar ni para evaluar, y las clases representadas por menos de tres ejemplos, por resultar insuficientes para permitir simultáneamente el entrenamiento y la evaluación de una misma categoría.

| Etapa | Materiales | Clases | Criterio aplicado |
|---|---:|---:|---|
| Maestro exportado | 45,397 | — | Trece archivos por tipo de material |
| Con clase asignada | 40,029 | 1,529 | Se descartan 5,368 sin categoría en la fuente |
| Conjunto de modelado | 39,571 | 1,234 | Se descartan clases con menos de tres ejemplos |
| — Entrenamiento | 31,656 | 1,234 | 80 % |
| — Prueba | 7,915 | 1,234 | 20 % |

### Preprocesamiento de texto

Se definió una función de normalización que convierte el texto a mayúsculas, descompone y elimina los signos diacríticos, sustituye por espacios los separadores propios de la convención de nomenclatura, descarta los caracteres que no son alfanuméricos ni punto o guion, y colapsa los espacios redundantes. La transformación conserva las dimensiones, fracciones y designaciones técnicas, que son precisamente los elementos discriminantes en una descripción de material.

Una consideración crítica de diseño es que **esa función es la misma en el entrenamiento y en la inferencia**. Un modelo entrenado sobre texto preprocesado de una forma y consultado con texto preprocesado de otra degrada su desempeño de manera silenciosa, sin producir ningún error visible.

### Diseño de la evaluación

La selección del algoritmo se resolvió mediante una **competencia entre siete configuraciones**, evaluadas todas sobre la misma partición de datos y con las mismas métricas. Las siete cubren cuatro familias de enfoque distintas:

- **Modelos lineales sobre representaciones dispersas** — regresión logística y máquina de vectores de soporte lineal, cada una sobre dos representaciones vectoriales: TF-IDF de palabras y TF-IDF de n-gramas de carácter.
- **Métodos de ensamble** — bosque aleatorio y potenciación de gradiente sobre árboles (XGBoost).
- **Clasificador de subpalabras** — fastText, que aprende sus propios embeddings de subpalabras sin depender de una vectorización externa.
- **Arquitectura contextual** — un transformador multilingüe preentrenado sometido a ajuste fino.

Se privilegió la representación por n-gramas de carácter sobre la de palabras completas por la densidad de abreviaturas, fracciones y designaciones alfanuméricas del catálogo.

**La máquina de vectores de soporte se envolvió en un procedimiento de calibración con validación cruzada.** Esta decisión no fue accesoria: sin estimaciones de probabilidad la plataforma no puede aplicar un umbral de confianza, y sin umbral no puede distinguir las sugerencias que presenta como resueltas de las que somete a revisión explícita del gestor.

La comparación se realizó sobre exactitud global, ambos promedios de F1, exactitud sobre las tres primeras sugerencias **y tiempo de entrenamiento**. Este último se incorporó como criterio de selección, no como dato accesorio, porque un modelo que exige horas de cómputo para reentrenarse resulta inviable de mantener en la operación.

Para determinar el punto de operación del sistema se caracterizó adicionalmente el compromiso entre exactitud y cobertura a distintos umbrales de confianza, siguiendo el planteamiento de clasificación con opción de rechazo.

La configuración ganadora se reentrenó sobre la totalidad del conjunto para su despliegue, por lo que las métricas reportadas corresponden a la partición retenida y no al artefacto en producción.

---

## 3. Resultados de la competencia

Siete configuraciones evaluadas sobre la partición de prueba de 7,915 materiales y 1,234 clases.

| Configuración | Exactitud | F1 macro | F1 pond. | Top-3 | Tiempo (s) |
|---|---:|---:|---:|---:|---:|
| **LinearSVC + TF-IDF carácter** | **0.8208** | **0.7072** | 0.8041 | 0.9176 | **54.1** |
| Random Forest + TF-IDF palabra | 0.8133 | 0.7029 | 0.8014 | 0.9063 | 46.0 |
| Reg. logística + TF-IDF palabra | 0.8095 | 0.6689 | 0.7949 | 0.9135 | 28.9 |
| Reg. logística + TF-IDF carácter | 0.8080 | 0.6423 | 0.7886 | 0.9248 | 1,071.9 |
| Transformer (MiniLM multilingüe) | 0.7995 | 0.5654 | 0.7692 | 0.8953 | 3,268.7 |
| XGBoost + TF-IDF carácter | 0.7949 | 0.6398 | 0.7817 | 0.8941 | 13,318.4 |
| fastText | 0.7780 | 0.6275 | 0.7648 | 0.8865 | 42.8 |

La configuración de máquina de vectores de soporte lineal sobre TF-IDF de carácter obtuvo el mejor resultado, con una **exactitud de 0.8208** y una **exactitud sobre las tres primeras sugerencias de 0.9176**, y fue la seleccionada para el despliegue.

### La configuración más simple resultó también la mejor

El resultado más relevante de la competencia es que la configuración más simple ganó, y por un margen consistente. La máquina de vectores de soporte lineal sobre una representación de caracteres superó tanto a los métodos de ensamble como a las arquitecturas basadas en aprendizaje profundo.

La diferencia en costo computacional refuerza esa conclusión:

- **XGBoost** consumió 3 horas y 42 minutos de entrenamiento para terminar sexto de siete, 2.6 puntos porcentuales por debajo del ganador, que se entrenó en menos de un minuto.
- **La regresión logística sobre n-gramas de carácter** tardó casi veinte veces más que el ganador, para un resultado también inferior.
- **El transformador multilingüe** requirió sesenta veces el tiempo del ganador —sobre unidad de procesamiento gráfico, mientras que el ganador se entrena sobre procesador convencional— sin lograr superarlo.

En un sistema concebido para reentrenarse periódicamente conforme el catálogo crece, esa diferencia deja de ser un detalle de laboratorio: **un modelo que exige horas de cómputo para actualizarse es un modelo que en la práctica no se actualiza**, y ninguno de los modelos más costosos ofreció a cambio una mejora de exactitud que lo justificara.

El hallazgo es consistente con la naturaleza del problema. Las descripciones del maestro son textos cortos, altamente estructurados y con vocabulario técnico acotado; no contienen la ambigüedad sintáctica ni las dependencias de largo alcance que justifican modelos de mayor capacidad. Un clasificador lineal sobre una representación de caracteres captura precisamente el tipo de regularidad que este texto exhibe.

---

## 4. El modelo ganador en detalle

**Máquina de vectores de soporte lineal sobre TF-IDF de n-gramas de carácter, con calibración de probabilidades.**

### Qué hace el modelo

El modelo recibe **una descripción de material en texto libre** y devuelve **la clase del catálogo corporativo a la que ese material pertenece**, junto con la probabilidad de esa asignación y las alternativas más probables. Discrimina entre **1,234 categorías**.

No entiende el material: no sabe qué es un tornillo. Lo que aprendió, a partir de 31,656 ejemplos históricos, es **qué patrones de caracteres aparecen en las descripciones de cada clase**. Un texto nuevo se resuelve buscando a qué patrón conocido se parece más.

El modelo está implementado como un **pipeline de scikit-learn** de dos etapas —vectorización y clasificación— serializado como un único artefacto. Eso importa: el pipeline garantiza que la vectorización aplicada a una consulta sea exactamente la misma que se aplicó durante el entrenamiento, porque el vectorizador ajustado viaja dentro del artefacto y no se reconstruye.

### Etapa 1 — La vectorización

El texto no se puede alimentar a un clasificador; hay que convertirlo en un vector numérico. Esta es la etapa que más define el desempeño del modelo, y la configuración es la siguiente:

```
TfidfVectorizer(
    analyzer      = 'char_wb',
    ngram_range   = (2, 5),
    max_features  = 50000,
    sublinear_tf  = True,
    strip_accents = 'unicode',
)
```

**`analyzer='char_wb'` — n-gramas de carácter delimitados por palabra.** En lugar de dividir el texto en palabras, se divide en secuencias de caracteres consecutivos. El sufijo `_wb` (*word boundary*) significa que las secuencias **no cruzan de una palabra a la siguiente**: cada palabra se rellena con espacios en sus extremos y los n-gramas se extraen dentro de ese límite. Así el modelo captura prefijos y sufijos —que son informativos— sin generar fragmentos espurios entre el final de una palabra y el inicio de otra.

**`ngram_range=(2,5)` — de dos a cinco caracteres.** Cada descripción genera todos sus fragmentos de longitud 2, 3, 4 y 5. Para la palabra `TORNILLO` se producen fragmentos como `TO`, `OR`, `RN`, `NI`, … y también `TOR`, `ORNI`, `RNILL`, `NILLO`, además de los que incluyen el espacio delimitador. Una sola descripción de cuarenta caracteres produce del orden de un centenar de fragmentos.

**Por qué caracteres y no palabras.** Esta es la decisión clave y responde directamente a cómo está escrito el catálogo:

- **Absorbe las variantes de abreviatura.** `TORNILLO`, `TORNILO` y `TORN` comparten la mayoría de sus n-gramas de carácter. Para un vectorizador de palabras son tres tokens distintos y sin relación; para uno de caracteres son tres textos muy parecidos. Dado que el catálogo se escribió a lo largo de años por distintos gestores contra un límite de cuarenta caracteres, esa tolerancia no es un lujo sino un requisito.
- **Captura designaciones alfanuméricas y fracciones.** Medidas como `1/2"`, `3/4`, `M12` o `2X4` son ruido para un tokenizador de palabras y señal fuerte para uno de caracteres.
- **Tolera errores de digitación** sin necesidad de un diccionario de correcciones.
- **No requiere vocabulario cerrado.** Un material de una familia nueva, con una palabra que nunca apareció en el entrenamiento, **igual produce n-gramas conocidos**. Un vectorizador de palabras lo representaría como un vector vacío; uno de caracteres todavía tiene de dónde inferir.

**`sublinear_tf=True` — ponderación logarítmica de la frecuencia.** En lugar de contar cuántas veces aparece cada fragmento, se aplica `1 + log(tf)`. Que un fragmento aparezca cinco veces no lo hace cinco veces más importante que si apareciera una. En descripciones tan cortas, esto evita que una repetición accidental domine el vector.

**El componente IDF —frecuencia inversa de documento—** pondera cada fragmento por lo raro que es en el conjunto completo. Los n-gramas que aparecen en casi todas las descripciones aportan poca información y se les baja el peso; los que aparecen solo en unas pocas clases son los que discriminan, y se les sube. Es el mecanismo que hace que el modelo se fije en lo distintivo de cada material y no en lo que todos comparten.

**`max_features=50000` — vocabulario acotado.** Se conservan los cincuenta mil fragmentos más frecuentes del corpus. Los demás se descartan. Acota el tamaño del modelo y evita que fragmentos que aparecen una sola vez en todo el catálogo generen ruido.

**Normalización L2.** Cada vector resultante se escala a longitud unitaria, de modo que una descripción larga y una corta se comparen por su *composición* y no por su *tamaño*.

**El resultado** es un vector disperso de 50,000 dimensiones por descripción, en el que la enorme mayoría de las posiciones vale cero y las pocas no nulas indican qué fragmentos de texto contiene y cuánto pesa cada uno.

### Etapa 2 — El clasificador lineal

Sobre esa representación opera una **máquina de vectores de soporte lineal** (`LinearSVC`, `C=1.0`).

**Qué hace.** Una SVM lineal busca, dentro del espacio de 50,000 dimensiones, el **hiperplano que separa una clase de las demás dejando el mayor margen posible** entre ambos lados. "Mayor margen" significa que no busca cualquier frontera que separe los ejemplos de entrenamiento, sino la que queda lo más lejos posible de los ejemplos de ambos grupos — que es lo que le da capacidad de generalizar a textos nuevos.

**Cómo maneja 1,234 clases.** Con una estrategia *uno-contra-el-resto*: se entrena un separador por clase —¿es esto un `TORNILLO` o no lo es?— y se obtienen 1,234 fronteras. Ante una descripción nueva, cada separador emite una puntuación y gana la clase cuya frontera la deja más adentro de su lado.

**Por qué un modelo lineal es suficiente aquí.** En espacios de muy alta dimensionalidad como este, las clases tienden a ser **linealmente separables**: hay tantas direcciones disponibles que casi siempre existe un hiperplano que separa. Añadir capacidad no lineal no compra separabilidad que ya se tiene, y sí compra sobreajuste y costo de entrenamiento. Esto es exactamente lo que la competencia mostró empíricamente.

### Etapa 3 — La calibración de probabilidades

Una SVM no produce probabilidades: produce **distancias con signo al hiperplano**. Un valor de 2.4 significa "cae bien adentro del lado positivo", pero no significa "84 % de probabilidad". Y sin probabilidades, la plataforma no puede aplicar ningún umbral.

Por eso el clasificador se envuelve en `CalibratedClassifierCV` con **validación cruzada de tres particiones**. El procedimiento entrena el modelo sobre una parte de los datos, observa qué distancias produce sobre la parte que no vio, y **ajusta una función que traduce distancia en probabilidad** de modo que las probabilidades resultantes sean fieles: que del conjunto de casos a los que el modelo asigna 0.9, aproximadamente el 90 % sea efectivamente correcto.

Se configuró con `ensemble=False`, lo que hace que la calibración conserve un único estimador base en lugar de una copia por partición. Reduce varias veces el tamaño del artefacto sin afectar la calidad de las probabilidades.

El número de particiones se ajusta automáticamente a lo que el conjunto soporte: la calibración exige al menos tantos ejemplos por clase como particiones, y una clase que llega al mínimo de tres ejemplos aporta solo dos al entrenamiento. Antes que descartar esas clases —lo que dejaría materiales que el modelo nunca podría predecir— se reduce el número de particiones.

**Sin esta etapa no existiría el punto de operación de la sección siguiente.** La calibración es lo que convierte un clasificador en un sistema capaz de decir "de esto estoy seguro, de esto no".

### Etapa 4 — La predicción

En operación, una consulta recorre esta secuencia:

1. La descripción entra al endpoint del API.
2. Se le aplica **la misma función de preprocesamiento** usada en el entrenamiento.
3. El vectorizador ajustado —el que viaja dentro del artefacto— la convierte en su vector disperso.
4. El clasificador calibrado devuelve **un vector de 1,234 probabilidades**, una por clase.
5. Se ordenan y se toman las cinco más altas; se devuelven **las tres primeras** al gestor, cada una con su código de clase y su confianza.
6. Un codificador de etiquetas traduce los índices internos del modelo a los códigos de clase reales del catálogo corporativo.
7. La predicción, su confianza y su latencia quedan registradas en bronze.

Todo esto ocurre en **0.09 segundos**.

### Ficha técnica

| | |
|---|---|
| Representación | TF-IDF de caracteres, `char_wb`, n-gramas de 2 a 5, 50,000 rasgos, ponderación logarítmica, normalización L2 |
| Clasificador | `LinearSVC` (C=1.0), uno-contra-el-resto sobre 1,234 clases |
| Calibración | `CalibratedClassifierCV`, validación cruzada de 3 particiones |
| Entrenamiento | 31,656 materiales · **54.1 segundos** · procesador convencional |
| Exactitud | **0.8208** |
| F1 macro | 0.7072 |
| F1 ponderado | 0.8041 |
| Exactitud top-3 | **0.9176** |
| Inferencia | 0.09 segundos por solicitud |
| Despliegue | Pipeline serializado, cargado en memoria dentro del proceso del API |

---

### El punto de operación

Que el modelo entregue probabilidades calibradas permite algo que una predicción cruda no permite: **que el sistema distinga entre las sugerencias de las que está seguro y las que no**, y trate cada grupo de forma distinta.

**El mecanismo.** Cada predicción llega con una confianza —la probabilidad de la clase más votada—. Se define un umbral. Las predicciones que lo superan el sistema **las resuelve por sí solo**; las que no lo superan **las deriva a revisión explícita del gestor**. Es el planteamiento de *clasificación con opción de rechazo*: el modelo tiene permitido abstenerse en lugar de verse obligado a responder siempre.

**El compromiso.** Subir el umbral no mejora el modelo — lo hace más selectivo. Mientras más alto, menos casos lo superan (**cae la cobertura**) pero los que lo superan son más confiables (**sube la exactitud**). La pregunta de diseño no es cuál umbral es "el correcto", sino **qué combinación de exactitud y cobertura conviene a este proceso**. Por eso se caracterizó la curva completa:

| Umbral | Exactitud | Cobertura | Materiales resueltos automáticamente |
|---|---:|---:|---:|
| Sin umbral | 0.8208 | 100.00 % | 7,915 |
| 0.5 | 0.9294 | 73.92 % | 5,851 |
| 0.6 | 0.9517 | 65.08 % | 5,151 |
| 0.7 | 0.9678 | 54.13 % | 4,284 |
| **0.8 (adoptado)** | **0.9888** | **28.24 %** | **2,235** |

Cada fila responde a la misma pregunta con distinta tolerancia al error. Al umbral 0.5, el sistema resolvería tres de cada cuatro solicitudes acertando en el 92.9 %. Al umbral 0.8 resuelve poco más de una de cada cuatro, pero **acierta en el 98.9 % de ellas**.

**Se eligió 0.8, privilegiando deliberadamente la exactitud sobre la cobertura.** La justificación es de **costos asimétricos**, y es específica de un proceso de gobierno de datos:

- Una **categoría incorrecta que ingresa al catálogo sin revisión** genera un costo persistente: distorsiona los reportes de consumo, complica la planificación de compras por tipo de material, y se propaga a todo proceso que consulte el catálogo después. Nadie la detecta, porque nadie la está buscando. Corregirla retroactivamente cuesta más que haberla revisado.
- Una **sugerencia derivada a revisión** solo consume la atención del gestor — que es exactamente el escenario que la herramienta está diseñada para atender. No es un fallo del sistema: es el sistema funcionando.

Los dos errores no cuestan lo mismo, de modo que no tiene sentido tratarlos de forma simétrica.

**El 72 % restante no queda desasistido.** Esta es la precisión que evita que la cobertura de 28 % se lea como una limitación: las solicitudes derivadas a revisión **conservan todo el valor de la herramienta**. El gestor no vuelve al punto de partida — recibe **tres candidatos ordenados por probabilidad** en lugar de enfrentar un catálogo de 1,234 clases. Y la exactitud sobre esas tres sugerencias es del 91.76 %. Lo que cambia entre un régimen y otro no es si el modelo ayuda, sino **quién firma la decisión**.

**Por qué el procedimiento es válido.** Un umbral solo sirve si la confianza efectivamente discrimina entre aciertos y errores. La distribución observada lo confirma: **las predicciones correctas se concentran en la región de confianza alta, mientras que las incorrectas se dispersan hacia valores bajos**. Si la confianza estuviera repartida por igual entre aciertos y errores, cualquier umbral seleccionaría al azar y la predicción selectiva carecería de sentido. La forma de esa distribución es lo que hace legítimo el punto de operación.

**El umbral es un parámetro, no una constante.** Está configurado, no cableado, y la plataforma registra cada corrección del gestor sobre solicitudes que resolvió automáticamente. Eso permite contrastar en operación si la promesa del 98.9 % se cumple y ajustar el umbral en cualquiera de las dos direcciones: elevarlo si las correcciones resultan más frecuentes de lo previsto, o reducirlo para automatizar mayor volumen si resultan menos frecuentes. La revisión debe repetirse después de cada reentrenamiento, porque un modelo nuevo altera la distribución de confianzas sobre la que el umbral fue ajustado.

---

### Comparación con la literatura

El antecedente más cercano identificado es GoldenBullet (Ding y cols., 2002), que clasificaba descripciones de producto contra la taxonomía UNSPSC —la misma con la que el catálogo de la unidad de negocio mantiene correspondencia— y reportó una exactitud del 78 % en la primera predicción y del 88 % sobre las diez primeras sugerencias, discriminando entre 421 categorías.

El modelo desarrollado alcanza **82.08 % en la primera sugerencia y 91.76 % sobre las tres primeras**, sobre **1,234 categorías** —casi el triple— y con una ventana de sugerencias considerablemente más estrecha, ya que la segunda cifra se mide sobre tres opciones y no sobre diez. Ambos resultados provienen de conjuntos de datos distintos y no constituyen una comparación controlada; su valor es situar el desempeño obtenido dentro del orden de magnitud que la literatura reporta para esta clase de problema.

Resulta especialmente pertinente la advertencia de esos mismos autores: una exactitud en el rango del 78 al 88 por ciento **iguala o supera la calidad de la clasificación humana** sobre el mismo material, y perseguir cifras sensiblemente superiores implicaría sobreajustar el modelo a decisiones humanas que a su vez contienen una tasa de error no despreciable. La observación aplica de manera directa a este proyecto, cuyo conjunto de entrenamiento son precisamente las clasificaciones históricas realizadas por los gestores.

### El modelo en operación

El desglose del tiempo de máquina por paso confirmó en producción lo que la competencia había establecido en laboratorio:

| Paso | Segundos | % del total |
|---|---:|---:|
| Normalización de la descripción (modelo de lenguaje) | 4.37 | 70.5 |
| Búsqueda de duplicados (similitud de trigramas) | 1.78 | 28.7 |
| **Clasificación de categoría** | **0.09** | **1.5** |
| Total de máquina | 6.20 | 100.0 |

El clasificador —el componente que constituye el núcleo analítico del trabajo— consume el 1.5 % del tiempo de cómputo. **El costo de inferencia de la configuración seleccionada es despreciable frente al resto del flujo**, de modo que la elección de un modelo lineal no impone ninguna penalización perceptible al usuario. Una arquitectura de mayor capacidad habría desplazado ese costo sin ofrecer, según la evaluación, un desempeño superior.

Sobre las **153 solicitudes** asistidas durante el período de validación, el gestor **conservó la categoría sugerida por el modelo en el 88.2 % de los casos**, con una tasa de corrección del 11.8 %.

Ese acuerdo constituye una validación del clasificador **independiente de su evaluación de laboratorio**: mide su desempeño contra las decisiones efectivas de quienes conocen el catálogo, y no contra una partición retenida de los mismos datos con que fue entrenado. Que el acuerdo en operación —88.2 %— supere a la exactitud sobre datos retenidos —82.08 %— indica que el desempeño estimado en el laboratorio se sostuvo al enfrentar materiales reales.

### Limitaciones del modelo

- **Correspondencia léxica.** La convención de nomenclatura del catálogo hace que el término principal de la descripción coincida con frecuencia con el nombre de la clase a la que el material pertenece, de modo que una parte del desempeño observado es atribuible a esa correspondencia directa. Cuantificar qué proporción del acierto depende de ella requeriría una evaluación por ablación, eliminando el término inicial y midiendo la caída resultante. Ese ejercicio queda planteado como verificación pendiente.
- **Etiquetas no independientes.** El modelo se entrena sobre etiquetas producidas por los propios gestores, que constituyen la mejor referencia disponible pero no una verdad de campo independiente. El techo de desempeño alcanzable está determinado por la consistencia de esas decisiones históricas.
- **Fotografía del catálogo.** Los resultados se obtuvieron sobre un corte a fecha determinada. El desempeño sobre materiales de familias que no estaban representadas en esa extracción no puede inferirse de las mediciones presentadas.
- **Cobertura del espacio de predicción.** Las categorías con muy escasa representación histórica —menos de tres ejemplos— quedan fuera del espacio de predicción del modelo.

# Estado del documento GAMMA — Diagnóstico y trabajo pendiente

**Fecha del análisis:** 11 de agosto de 2026
**Documento evaluado:** `GAMMA.pdf` (27 páginas)
**Contrastado contra:** `Proyecto Final MBIA 2026.pdf` (rúbrica de contenido) y `Guía para Tesis y Trabajos de graduación.pdf` (formato UVG)
**Proyecto:** `/Users/menene/code/www/mbia_gamma` (código, notebooks, esquema de BD)

---

## 0. Resumen ejecutivo

> **Alerta de calendario: la entrega del documento en versión final es el 14 de agosto de 2026. Faltan 3 días.**

El documento tiene **una base sólida pero incompleta**. Lo que está escrito (Capítulos 1–6) es de buena calidad: el planteamiento del problema es concreto, está cuantificado, y el marco teórico cubre correctamente los algoritmos evaluados. **El problema es de volumen y de cobertura de rúbrica, no de calidad.**

De las **8 áreas de contenido que exige la rúbrica del Proyecto Final, solo 1 está cubierta**. Las 7 restantes —incluyendo integración de datos, explotación de información, desarrollo de modelos, visualización, arquitectura, resultados y monetización— **no existen en el documento**, a pesar de que **el trabajo técnico correspondiente sí está hecho en el repositorio**.

Adicionalmente, el documento arrastra **capítulos residuales de la plantilla LaTeX original** (una tesis de mecatrónica): "Derivación de la dinámica del mecanismo", "Control del sistema mecánico", y el anexo "Planos de Construcción". El resumen es **lorem ipsum**. Estos elementos deben eliminarse antes de cualquier entrega.

**Diagnóstico en una línea:** el documento va aproximadamente al **35–40 %**, la brecha es de redacción (no de investigación), y el insumo para cerrarla ya existe en los notebooks y el código.

| Dimensión | Estado |
|---|---|
| Cobertura de rúbrica del curso | 🔴 1 de 8 áreas |
| Capítulos de la guía UVG | 🟡 7 de 13 presentes y completos |
| Formato UVG (letra, márgenes, bibliografía) | 🔴 múltiples desviaciones |
| Figuras y cuadros | 🔴 cero en 27 páginas |
| Resumen / Conclusiones / Recomendaciones | 🔴 vacíos o lorem ipsum |
| Trabajo técnico de respaldo | 🟢 hecho y disponible en el repo |

---

## 1. Estado capítulo por capítulo

| # | Capítulo | Estado | Observación |
|---|---|---|---|
| — | Portada | 🟡 | Errores de forma (ver §3.1) |
| — | Hoja de aprobación | 🟡 | Solo 2 firmantes para una "terna"; verificar |
| — | Prefacio | 🟢 | Bien escrito. Declara limitaciones y confidencialidad correctamente |
| — | Agradecimientos | 🟢 | Completo |
| — | Índice | 🟡 | Refleja capítulos-plantilla que deben eliminarse |
| — | Lista de Figuras | 🔴 | **Vacía** |
| — | Lista de Cuadros | 🔴 | **Vacía** |
| — | Resumen | 🔴 | **Lorem ipsum** |
| 1 | Introducción | 🟢 | Sólida. Falta el inciso (d) de la guía: adelantar las conclusiones principales |
| 2 | Objetivos | 🟢 | Bien estructurados (técnicos / negocio). **Pero comprometen entregables que aún no están evidenciados** (ver §4.5) |
| 3 | Justificación | 🟡 | Buena, pero difiere la justificación financiera a un capítulo que no existe |
| 4 | Marco Teórico | 🟡 | Cubre los algoritmos. **Faltan bloques importantes** (ver §4.6) |
| 5 | Antecedentes | 🟡 | Solo 2 referencias externas. Muy delgado (ver §4.7) |
| 6 | Alcance | 🟢 | Claro y honesto sobre los límites |
| 7 | "Derivación de la dinámica del mecanismo" | ⛔ | **Residuo de plantilla — eliminar** |
| 8 | "Control del sistema mecánico" | ⛔ | **Residuo de plantilla — eliminar** |
| 9 | Conclusiones | 🔴 | **Vacío** |
| 10 | Recomendaciones | 🔴 | **Vacío** |
| — | Referencias / Bibliografía | 🟡 | Formato APA, **no el formato que exige la guía UVG** (ver §3.3). Además aparece duplicado en el índice |
| A | Anexo "Planos de Construcción" | ⛔ | **Residuo de plantilla — eliminar** |
| — | Glosario | 🔴 | Ausente. Muy recomendable dada la densidad de jerga |

---

## 2. Cobertura frente a la rúbrica del Proyecto Final

La rúbrica define 8 bloques de contenido obligatorio. Este es el mapeo real:

| # | Área exigida por la rúbrica | Estado | Dónde está / debería estar |
|---|---|---|---|
| 1 | **Detección de necesidad analítica y descripción del proyecto**<br>· Introducción a la industria/contexto<br>· Problemática actual, razones y procesos<br>· Alcances, objetivos y justificación financiera | 🟡 Parcial | Caps. 1, 2, 3, 6 ✅<br>**Falta:** la justificación **financiera** está diferida a un capítulo inexistente |
| 2 | **Análisis de fuentes de información**<br>· Detalle de fuentes y su naturaleza<br>· Tipos de fuentes y tipos de datos<br>· Repositorios | 🔴 **Ausente** | Existe el insumo: 13 archivos XLSX de SAP por tipo de material, catálogo de 1,538 clases, tabla UNSPSC de Naciones Unidas |
| 3 | **Integración de información**<br>· Procesos de ingestión y movimiento<br>· Transformaciones, filtros, agregaciones<br>· Herramientas tecnológicas | 🔴 **Ausente** | Existe el insumo: `db/init/*.sql` (medallón staging/bronze/silver/gold), `api/app/routers/etl.py`, `migrate.py`, DERs en `docs/*.mmd` |
| 4 | **Explotación de información**<br>· Exploración, análisis descriptivo y estadístico<br>· Descubrimientos<br>· Herramientas | 🔴 **Ausente** | Existe el insumo: notebook `02_evaluacion_modelos.ipynb` §3 (distribución de clases, longitud de descripciones, estadísticos de `short_text`, 3 figuras generadas) |
| 5 | **Desarrollo de modelos analíticos**<br>· Metodología, algoritmos, plan analítico<br>· Justificación de variables y dataset<br>· Aplicación de algoritmos y herramientas | 🔴 **Ausente** | Existe el insumo: notebooks 02 y 03 con **7 modelos evaluados**, métricas completas, matrices de confusión, análisis de confianza y de errores |
| 6 | **Visualización de resultados**<br>· Storytelling<br>· Representaciones visuales y buenas prácticas<br>· Herramientas de visualización | 🔴 **Ausente** | Existe el insumo: vistas `gold.kpi_*`, frontend Vue (12 páginas), diagramas Mermaid. **Falta evidencia del tablero Power BI prometido en objetivos** |
| 7 | **Arquitectura tecnológica y puesta en producción**<br>· Validación del modelo con datos reales<br>· Recursos tecnológicos<br>· Recursos humanos y cambios culturales | 🔴 **Ausente** | Existe el insumo: `docker-compose.yml` (4 servicios), API FastAPI con 8 routers, autenticación, logging. Período de uso real 18 jun – 21 jul 2026 |
| 8 | **Resultados y aplicación de negocio**<br>· Conclusiones y recomendaciones gerenciales<br>· Impacto financiero y monetización<br>· Próximos pasos y recomendaciones técnicas | 🔴 **Ausente** | Existe el insumo parcial: vista `gold.kpi_savings`. **`gold.parameters` está inicializado en 0 — verificar que tenga valores reales de producción** |

**Resultado: 1 área parcialmente cubierta, 7 ausentes.** Este es el hallazgo principal del diagnóstico.

---

## 3. Cumplimiento del formato exigido por la Guía UVG

### 3.1 Portada y preliminares

| Hallazgo | Severidad | Detalle |
|---|---|---|
| **"Tésis" mal escrito** | Alta | Va sin tilde: *Tesis*. Aparece en la portada. Un error ortográfico en la portada es de los peores lugares donde tenerlo |
| **"Facultad de UVG BRIDGE Business School"** | Alta | Redacción incorrecta ("Facultad de" + nombre propio). Verificar la denominación oficial exacta de la unidad académica |
| **Modalidad declarada** | Media | Dice "modalidad de Tesis", pero la rúbrica del curso lo llama *Proyecto Integrador / Proyecto Final*. Confirmar con coordinación cuál es el rótulo correcto |
| **"Terna examinadora" con 2 miembros** | Media | Una *terna* son tres personas; se listan Ing. Horacio Recinos e Ing. Sergio Molina. Además el Ing. Recinos figura simultáneamente como asesor (Vo.Bo.) y como examinador. Verificar la conformación oficial |
| **Fecha de aprobación pre-llenada** | Baja | "21 de septiembre 2026" coincide correctamente con el calendario (Grupo 1, lunes 21 sept, 6:00) ✅ |
| **Listas de Figuras y Cuadros vacías** | Alta | Ver §3.4 |

### 3.2 Estructura capitular exigida por la guía

La guía sugiere: *Objetivos, Justificación, Marco Teórico, Antecedentes, Metodología (materiales y métodos), Resultados, Análisis de resultados (discusión).*

| Elemento | Estado |
|---|---|
| Objetivos | 🟢 Presente |
| Justificación | 🟢 Presente |
| Marco Teórico | 🟢 Presente |
| Antecedentes | 🟢 Presente |
| **Metodología (materiales y métodos)** | 🔴 **Ausente** |
| **Resultados** | 🔴 **Ausente** |
| **Análisis de resultados / discusión** | 🔴 **Ausente** |
| Conclusiones | 🔴 Capítulo vacío |
| Recomendaciones | 🔴 Capítulo vacío |

Los tres capítulos centrales del método científico —Metodología, Resultados y Discusión— **no existen**. Esto es simultáneamente el mayor incumplimiento de la guía UVG y el mayor hueco frente a la rúbrica del curso.

### 3.3 Bibliografía — incumplimiento de formato

La guía UVG (sección III) exige un formato específico **que no es APA**:

```
Apellido, Nombre. Año. Título en cursivas. Nª ed. Ciudad: Editorial. NNN págs.
```

El documento usa APA 7:

```
Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5–32.
```

**Acciones:**
- Reformatear las 12 referencias al formato de la guía, o confirmar por escrito con el asesor que se acepta APA (muchos programas lo aceptan; **pero hay que confirmarlo, no asumirlo**).
- Ordenar alfabéticamente (actualmente ya lo está ✅).
- Sangría de 10 espacios desde la segunda línea (la guía es explícita).
- **Errores de fecha:** `Databricks. (2026)` y `PostgreSQL Global Development Group. (2026)` fechan documentación técnica con el año de consulta. Debe usarse el año de la versión/copyright del documento, con la fecha de consulta aparte. La guía tiene una plantilla específica para fuentes de internet (ejemplo 18).
- **Duplicación en el índice:** aparecen tanto "Referencias" como "Bibliografía" como entradas separadas. Debe ser una sola sección.

### 3.4 Figuras y cuadros — ausencia total

**El documento tiene cero figuras y cero cuadros en 27 páginas.** Para un proyecto de analítica evaluado por una rúbrica que exige explícitamente *"representaciones visuales y buenas prácticas"* y *"aplicación de conceptos de storytelling"*, esto es crítico.

Requisitos de la guía cuando se agreguen:
- Todos los cuadros numerados, con título autoexplicativo, **en formato científico sin color**.
- Las ilustraciones pueden ir a color si la impresión es a color.
- **Prohibido 3D y sombreados.**
- Deben registrarse en la Lista de Figuras y Lista de Cuadros.

Ver §5 para el inventario de figuras que ya existen generadas y solo hay que insertar.

### 3.5 Estilo tipográfico

| Regla de la guía | Estado en el documento | Acción |
|---|---|---|
| Times New Roman o Arial, tamaño 10 | El PDF parece compilado en LaTeX con la fuente por defecto (Computer Modern) | Cambiar a `\usepackage{times}` / `mathptmx` o equivalente |
| **Sin negrilla, subrayado ni cursivas** (salvo nombres científicos, títulos en bibliografía, latinismos) | 🔴 Incumple. Hay negritas en subtítulos y en términos inline: *unicidad*, *exactitud*, *completitud*, *Transformer*, *trigramas*, *TF-IDF*, *pg_trgm* | Decidir: quitar negritas, o documentar la excepción con el asesor |
| Interlineado 1.5 | Verificar | Configurar `\linespread` |
| Sangría de 4 espacios en cada párrafo nuevo | Verificar | LaTeX por defecto usa ~15pt |
| Numeración de subtítulos: `I. A. 1. a. 1) a)` | 🔴 Usa numeración decimal LaTeX (`4.5.1`) | Riesgo medio. Confirmar con el asesor si se acepta la numeración decimal |
| Márgenes: izquierdo 1.5", derecho e inferior 1", superior 1" (2" en páginas especiales) | Verificar | Configurar `geometry` con `left=1.5in` |
| Paginación: romanos minúsculos centrados abajo en preliminares; arábigos desde Introducción | 🟢 Correcto (iii, iv, vii, viii, ix → 1, 2, 3…) | — |
| Número de página arriba a la derecha en páginas que no abren capítulo | Verificar contra la ilustración 7 de la guía | — |
| Cada capítulo inicia en página nueva | 🟢 Correcto | — |
| Resumen máximo 250 palabras, informativo no evaluativo | 🔴 Es lorem ipsum | Redactar |

---

## 4. Debilidades de contenido en lo ya escrito

Esto es lo que la terna va a atacar en el examen individual. Ordenado por riesgo.

### 4.1 🔴 El "94 % de riesgo de duplicidad parcial" es el número más atacable del documento

El Capítulo 1 afirma: *"un riesgo potencial de duplicidad parcial (por similitud textual) que alcanza al 94 % de los registros"*, y el Capítulo 3 lo repite.

**El problema:** no se declara el umbral de similitud, ni el método, ni el operador. Con un umbral de trigramas suficientemente bajo, *cualquier* catálogo técnico da un porcentaje cercano al 100 % —porque casi todo material comparte trigramas con algún otro— y el número deja de significar algo. Un examinador con experiencia lo va a notar de inmediato.

**Qué hacer:**
- Declarar explícitamente: umbral usado, operador `pg_trgm` (`similarity()` / `%`), y la definición precisa. Redactarlo como: *"el 94 % de los registros tiene al menos un vecino con similitud ≥ X"*, no como "riesgo de duplicidad".
- Presentar una **curva de sensibilidad**: % de registros afectados en función del umbral (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9). Esto convierte una cifra atacable en un hallazgo defendible. Es una consulta SQL y un gráfico.
- Validar manualmente una muestra (p. ej. 100 pares) a distintos umbrales y reportar precisión. Esto es lo que convierte el número en evidencia.

### 4.2 🔴 Riesgo de fuga de información en el modelo de clasificación

Observando los datos del notebook:

| `short_text` | `class_name` |
|---|---|
| `MALLA ELECTROSOLDADA 1.22M` | MALLA |
| `MALLA:CICLON;4FT` | MALLA |
| `MALLA:P/COLAR;ARENA;1/4"X48"` | MALLA |

**La primera palabra de la descripción es, con mucha frecuencia, el nombre de la clase.** Esto significa que buena parte del 84.91 % de accuracy podría explicarse por una coincidencia léxica casi directa, no por aprendizaje real. Un examinador puede preguntar: *"¿su modelo aprende, o solo lee la primera palabra?"* — y sin respuesta preparada eso desarma el capítulo de modelos.

**Qué hacer (alta prioridad, esfuerzo bajo):**
- Correr una **ablación**: reentrenar eliminando el primer token de `short_text` y reportar la caída de accuracy. Si el modelo mantiene un desempeño razonable, el argumento queda blindado. Si cae mucho, hay que decirlo con honestidad y reencuadrar la contribución (que sigue siendo válida: automatiza una tarea que hoy es manual).
- Complementar con un baseline trivial ("asignar la clase cuyo nombre coincide con el primer token") para demostrar cuánto valor agrega el modelo por encima de esa heurística. **Este baseline es el mejor amigo del capítulo de modelos**, no su enemigo.

### 4.3 🔴 La justificación financiera mezcla dos magnitudes de tiempo

El Capítulo 1 es honesto y preciso: cada gestión toma **3.3 horas** dentro del rol del gestor, pero el paso que GAMMA automatiza consume **5–10 minutos**.

El Capítulo 3, sin embargo, argumenta sobre las 3.3 horas: *"Mientras una solicitud permanece en gestión —en promedio 3.3 horas—, los procesos que suceden... quedan detenidos."*

**El riesgo:** si el ROI se calcula sobre 3.3 h se está inflando el beneficio en un orden de magnitud, y la terna lo va a detectar. Si se calcula sobre 5–10 min, el ahorro es real pero modesto (≈4.4 solicitudes/día × 7.5 min ≈ 33 min/día ≈ 2.75 h/semana).

**Qué hacer:**
- Construir el ROI **exclusivamente sobre el tiempo que GAMMA efectivamente interviene** (validado contra `gold.kpi_processing_time`, que mide el tiempo real dentro de la herramienta).
- Presentar el efecto sobre las 3.3 h como un **beneficio secundario y cualitativo** (reducción del tiempo de cola / respuesta organizacional), claramente separado del ahorro directo.
- Agregar los beneficios de **calidad** (duplicados evitados, correcciones de categoría) al caso financiero: ahí está el argumento fuerte, porque un duplicado creado tiene costo recurrente en inventario, compras y reportería. Cuantificarlo aunque sea con supuestos declarados.
- **Ser explícito con los supuestos.** Un ROI modesto pero defendible vale más que uno grande e indefendible.

### 4.4 🟡 Inconsistencia en la cifra del tamaño del catálogo

El Capítulo 1 dice: *"análisis exploratorio sobre 39,571 materiales del catálogo... distribuidos en 1,234 categorías"*.

Según el notebook, la cadena real es:

| Etapa | Materiales | Clases |
|---|---|---|
| Cargados de los 13 archivos XLSX | 45,397 | — |
| Con clase asignada | 40,029 | 1,529 |
| Tras filtrar clases con < 3 ejemplos | **39,571** | **1,234** |

Es decir, 39,571 / 1,234 **no es el tamaño del catálogo**: es el tamaño del *dataset de modelado* después de dos filtros. Presentarlo como "el catálogo" es impreciso y se contradice con cualquier cifra que la empresa reporte.

**Qué hacer:** usar 45,397 (o 40,029) al describir el catálogo, y reservar 39,571 / 1,234 para el capítulo de modelos, explicando el criterio de exclusión y los 5,368 materiales sin clase (que además son un hallazgo de calidad de datos por derecho propio).

### 4.5 🟡 Objetivos que comprometen entregables sin evidencia localizable

El Capítulo 2 compromete, entre otros:

| Objetivo comprometido | Evidencia encontrada en el repo |
|---|---|
| Tablero Power BI conectado a la capa Gold | 🔴 No hay archivo `.pbix`. Sí existen las vistas `gold.kpi_*` que lo alimentarían |
| Encuesta de satisfacción a gestores, jefatura y coordinación | 🔴 No hay instrumento ni resultados |
| Cuantificación de ahorro en horas-gestor y ROI | 🟡 Existe la vista `gold.kpi_savings`, pero `gold.parameters` está inicializado con `manual_time_s = 0` y `hourly_rate = 0` — **verificar que producción tenga los valores reales** |
| Manual de usuario | 🔴 No localizado |
| Presentación de capacitación | 🔴 No localizada |
| Presentación de seguimiento de resultados | 🔴 No localizada |
| Auditoría retroactiva masiva del catálogo | 🟡 Las cifras (456 / 246 / 94) sugieren que se hizo, pero no se documenta el método |

**Un objetivo declarado y no evidenciado en resultados es un punto perdido garantizado en la rúbrica.** Si alguno de estos entregables no se va a alcanzar, es preferible ajustar el objetivo ahora que dejarlo sin responder.

### 4.6 🟡 Vacíos en el Marco Teórico

Lo que está, está bien. Falta fundamentar conceptos que el documento *va a usar* en los capítulos pendientes:

- **ISO 8000** — se menciona en la Introducción y en los Objetivos como el estándar al que se normalizan las descripciones, pero **nunca se explica qué es**. Necesita su propia sección.
- **Métricas de evaluación multiclase** — los resultados dependen de accuracy, F1-macro vs F1-weighted, y top-3 accuracy. Con 1,234 clases muy desbalanceadas, la diferencia entre macro y weighted es sustantiva y hay que explicarla antes de reportarla.
- **Predicción selectiva / umbral de confianza** — el sistema opera con umbrales (los datos muestran la curva accuracy-vs-cobertura). Es un concepto que necesita respaldo teórico.
- **Desbalance de clases** — 132 clases tienen 1 solo material; la mediana es 9. Es central para interpretar los resultados.
- **Protocolo de validación** — train/test split, estratificación, por qué no validación cruzada.
- **Metodología de proyectos de analítica** — la rúbrica exige "el ciclo de vida de los proyectos de analítica". Anclarlo a un marco reconocido (CRISP-DM o similar) y estructurar la metodología sobre él es una victoria fácil.
- **Inteligencia de negocios** — la rúbrica exige explícitamente *"una componente de inteligencia de negocios y otra componente de ciencia de datos"*. El marco teórico cubre bien la ciencia de datos, pero **no tiene nada de BI**: KPIs, diseño de tableros, modelo dimensional, gobierno de la medición. Es una omisión visible en una maestría que se llama *Business Intelligence and Analytics*.
- **ROI / monetización de la información** — necesario para sustentar el capítulo 8 de la rúbrica.

### 4.7 🟡 Antecedentes demasiado delgados

Dos referencias externas (Albayrak et al. 2022, Sebastiani 2002) para todo el capítulo. Ambas son pertinentes y están bien usadas, pero es poco para un trabajo de graduación.

**Lo que falta y que un examinador de escuela de negocios preguntará:**

- **"¿Por qué construir en lugar de comprar?"** No hay ninguna mención a las alternativas comerciales del mercado (SAP MDG, Informatica MDM, Verdantis, herramientas de clasificación de catálogo). Un análisis comparativo —aunque sea breve— de build vs. buy, con el costo evitado de licenciamiento, **es exactamente el tipo de argumento que esta maestría espera** y hoy no está.
- Literatura específica de MDM sobre SAP y de normalización de catálogos industriales.
- Casos de aplicación de ML a datos maestros de materiales en industria (existe literatura de manufactura y energía).
- Referencia al marco DAMA-DMBOK para gobierno de datos, además de Loshin.

### 4.8 🟡 Comparabilidad del período de medición

- **Línea base:** 15 feb – 17 jun 2026 (≈4 meses).
- **Período de uso de GAMMA:** 18 jun – 21 jul 2026 (≈5 semanas).

A 4.4 solicitudes/día hábil, el período post son aproximadamente **~105 solicitudes**. Es una muestra pequeña para sostener afirmaciones de ROI.

**Qué hacer:** reportar el `n` exacto explícitamente, acompañar las medias con dispersión (desviación estándar o intervalo de confianza), y declarar como limitación la asimetría de duración y la posible estacionalidad. Reconocer la limitación **protege**; omitirla invita la pregunta.

### 4.9 🟡 El resultado del Transformer (3.95 % de accuracy) necesita manejo cuidadoso

El notebook `03_modelos_candidatos_v2` reporta para multilingual-MiniLM: accuracy 0.0395, F1-macro 0.0003, en 1,460 s.

Eso **no es un modelo que perdió: es un modelo que no convergió.** Reportarlo tal cual como resultado de una comparación justa es un riesgo de credibilidad — la lectura obvia del examinador es "está mal configurado" (probablemente pocas épocas, learning rate inadecuado, o una cabeza de clasificación de 1,234 clases sin entrenamiento suficiente).

**Dos caminos, ambos aceptables:**
1. Reentrenarlo bien (más épocas, LR apropiado) y reportar el resultado real.
2. **Reportarlo honestamente como no convergido bajo el presupuesto de cómputo disponible**, excluirlo de la comparación principal, y discutirlo como hallazgo metodológico. El Marco Teórico ya prepara este argumento correctamente al señalar que los transformers *"suelen requerir un proceso adicional de ajuste fino"* — hay que cerrarlo en Resultados.

**No dejarlo sin comentar.** Un 3.95 % sin explicación es una invitación a la pregunta más incómoda del examen.

### 4.10 🟢 Un hallazgo fuerte que está desaprovechado

XGBoost tardó **11,025 segundos (3 horas)** en entrenar y perdió (81.45 %) contra LinearSVC, que tardó **62.9 segundos** y ganó (84.91 %). fastText logró 80.77 % en **43 segundos**.

Esta es una **excelente historia de selección de modelos en contexto real**: el modelo más simple ganó en precisión *y* fue 175× más rápido, lo que además lo hace viable de reentrenar en producción. Es exactamente el tipo de razonamiento pragmático que distingue un buen proyecto aplicado.

Hoy este hallazgo está enterrado en un notebook. **Debe ser un cuadro y un párrafo destacado del capítulo de modelos.**

### 4.11 🟡 Otros puntos menores

- **Erratas detectadas:** "corporción" → *corporación* (Cap. 2, objetivos técnicos); "Tésis" → *Tesis* (portada). Hacer una revisión ortográfica completa al final.
- **Modelo desplegado vs. modelo evaluado:** el artefacto de producción se reentrena con el 100 % de los datos (`winner['pipeline'].fit(X_full, y_full)`). Es buena práctica, pero implica que el 84.91 % corresponde al modelo del split, no al desplegado. **Hay que decirlo explícitamente** para no exponerse a la acusación de reportar métricas sobre datos de entrenamiento.
- **Anomalía de datos a verificar:** en el EDA hay registros con `source_file = ZCON` pero `material_type = ZSEG` (los materiales de clase MALLA). Puede ser correcto por diseño, o un defecto del cruce. Conviene aclararlo antes de que lo pregunten.
- **Los 5,368 materiales sin clase asignada** (11.8 % del catálogo) son un hallazgo de calidad de datos relevante que hoy solo aparece como un descarte técnico en el notebook. Merece mención en Explotación de la Información.

---

## 5. Inventario: material ya existente que aún no está en el documento

Buena noticia: **la mayor parte del trabajo de los capítulos faltantes ya está hecho.** Es cuestión de redactar y trasladar.

### Para "Análisis de fuentes de información"
- 13 archivos XLSX exportados de SAP por tipo de material (ZCON, ZQUI, ZMAQ, ZEQU, ZRPA, ZSEG, DIEN, ZMER, ZMAF, ZRPI, ZHAR, ZSUM, ZHER) con conteos por archivo.
- Catálogo maestro de 1,538 clases (`Clases de material DEN.xlsx`).
- Tabla UNSPSC de Naciones Unidas.
- Estructura de campos: `material_code`, `class_code`, `short_text`, `class_name`, `material_type`, `article_group`, `sector`, `unspsc`.

### Para "Integración de información"
- `db/init/00_extensions.sql` … `04_gold.sql` — arquitectura medallón completa.
- `db/migrations/` — 5 migraciones con historial de evolución del esquema.
- `api/app/routers/etl.py` (415 líneas) — ingestión de materiales, clases y UNSPSC, con logs.
- `migrate.py`.
- **Diagramas ER ya hechos:** `docs/der.mmd`, `docs/der_silver.mmd`, `docs/der_gold.mmd` → **son figuras listas para insertar**.

### Para "Explotación de información"
Del notebook `02_evaluacion_modelos.ipynb`, sección 3 — **3 figuras ya generadas**:
- Distribución de tamaño de clases (132 clases con 1 material, 697 con 2–10, 517 con 11–50, 103 con 51–100, 80 con 100+).
- Estadísticos de `short_text`: media 32.3 caracteres, mediana 34, máximo 40 (el límite de SAP), 4.9 tokens promedio, 2.3 punto y coma promedio.
- Ejemplos antes/después de normalización de texto.
- Clase más poblada: 081946 (655 materiales). Mediana: 9 materiales por clase.

### Para "Desarrollo de modelos analíticos"
Cuadro comparativo completo, **listo para transcribir**:

| Modelo | Accuracy | F1 Macro | F1 Weighted | Top-3 Acc | Tiempo (s) |
|---|---|---|---|---|---|
| **LinearSVC + CharTFIDF** ⭐ | **0.8491** | **0.7523** | **0.8380** | **0.9404** | **62.9** |
| XGBoost + CharTFIDF | 0.8145 | 0.6821 | 0.8063 | 0.9200 | 11,025.2 |
| fastText | 0.8077 | 0.6897 | 0.8001 | 0.9075 | 43.0 |
| Transformer (MiniLM) | 0.0395 | 0.0003 | 0.0050 | 0.0714 | 1,460.0 |
| LogReg + CharTFIDF | *(en notebook 02)* | | | | |
| LogReg + WordTFIDF | *(en notebook 02)* | | | | |
| RandomForest + WordTFIDF | *(en notebook 02)* | | | | |

> ⚠️ **Los resultados de los 4 modelos del notebook 02 no quedaron guardados en las salidas del `.ipynb`.** Solo se conserva el resumen del notebook 03. **Hay que re-ejecutar el notebook 02 y guardar las salidas**, o al menos recuperar las métricas de los 3 modelos que faltan en el cuadro. Sin esto, la afirmación de "seis enfoques evaluados" del Marco Teórico queda sin respaldo tabular completo.

Además ya existen: análisis de umbral de confianza (accuracy vs. cobertura para 0.5–0.9), matriz de confusión del ganador, análisis de errores, e hiperparámetros documentados de todos los pipelines.

### Para "Arquitectura tecnológica y puesta en producción"
- `docker-compose.yml` — 4 servicios (db, api, lab, frontend).
- API FastAPI con 8 routers: `auth`, `chat` (757 líneas), `etl`, `duplicates`, `model`, `logs`, `export`, health.
- Frontend Vue con 12 páginas (Chat, Etl, Datos, Arquitectura, Export, Logs, Laboratorio, Docs, Api, Referencia, Presentación, Login).
- `frontend/src/components/ArchitectureDiagram.vue` — **diagrama de arquitectura ya hecho, listo para figura**.
- Autenticación con roles, flag de administrador, y exclusión sistemática de usuarios admin en todas las vistas KPI (detalle metodológico bueno: la medición excluye tráfico de pruebas — **vale la pena mencionarlo, demuestra rigor**).
- Pipeline de preprocesamiento replicado idénticamente entre entrenamiento y producción (`preprocess_text` en `api/app/routers/model.py`) — otro detalle de rigor que merece mención.

### Para "Resultados y aplicación de negocio"
Vistas gold ya construidas: `kpi_processing_time`, `kpi_quality`, `kpi_savings`, `kpi_step_breakdown`, `kpi_duplicates`, `kpi_requests_by_user`, `requests_users`, `materials_by_type`.

**Lo que falta es ejecutarlas contra los datos de producción del período 18 jun – 21 jul y volcar los números al documento.** Esa es la brecha real del capítulo de resultados: no es análisis pendiente, es extracción pendiente.

---

## 6. Trabajo faltante, priorizado

### 🔴 P0 — Bloqueantes para la entrega del 14 de agosto

| # | Tarea | Esfuerzo |
|---|---|---|
| 1 | **Eliminar los capítulos residuales de plantilla** (7, 8 y Anexo A "Planos de Construcción") | 10 min |
| 2 | **Redactar el Resumen** (máx. 250 palabras, informativo, sustituir lorem ipsum) | 1 h |
| 3 | **Extraer los KPIs reales de producción** de las vistas `gold.*` para el período 18 jun – 21 jul. Verificar que `gold.parameters` tenga `manual_time_s` y `hourly_rate` con valores reales, no 0 | 2 h |
| 4 | **Escribir Metodología** (materiales y métodos) — cubre rúbrica 2 y 3 | 4–6 h |
| 5 | **Escribir Explotación de la información** — cubre rúbrica 4. El insumo está en el notebook | 3–4 h |
| 6 | **Escribir Desarrollo de modelos analíticos** — cubre rúbrica 5. El insumo está en los notebooks | 4–6 h |
| 7 | **Escribir Resultados y aplicación de negocio** con el ROI — cubre rúbrica 8 | 4–6 h |
| 8 | **Escribir Arquitectura y puesta en producción** — cubre rúbrica 7 | 3–4 h |
| 9 | **Escribir Conclusiones y Recomendaciones** (capítulos hoy vacíos) | 2–3 h |
| 10 | **Insertar figuras y cuadros** y poblar las listas correspondientes | 3–4 h |
| 11 | **Corregir la portada**: "Tésis" → "Tesis", denominación de la facultad, modalidad | 15 min |

### 🟡 P1 — Alto impacto en la nota, hacer si el tiempo alcanza

| # | Tarea | Esfuerzo |
|---|---|---|
| 12 | **Ablación del primer token** para blindar el capítulo de modelos (§4.2) | 1 h |
| 13 | **Curva de sensibilidad del umbral de duplicados** para sustentar el 94 % (§4.1) | 2 h |
| 14 | **Re-ejecutar el notebook 02** guardando salidas, para completar el cuadro de los 7 modelos | 1 h + cómputo |
| 15 | **Capítulo de Visualización de resultados** con storytelling — cubre rúbrica 6 | 3 h |
| 16 | **Evidencia del tablero Power BI** (capturas + descripción) | 2 h |
| 17 | **Corregir la cifra del catálogo** (39,571 vs 45,397) en toda la redacción (§4.4) | 30 min |
| 18 | **Separar el ROI de las 3.3 h** y construirlo sobre el tiempo real intervenido (§4.3) | 2 h |
| 19 | **Resolver el resultado del Transformer**: reentrenar o encuadrar honestamente (§4.9) | 1–3 h |
| 20 | **Ampliar Marco Teórico**: ISO 8000, métricas multiclase, desbalance, CRISP-DM, BI/KPIs (§4.6) | 3 h |
| 21 | **Reformatear bibliografía** al formato de la guía UVG, o confirmar APA por escrito (§3.3) | 1–2 h |
| 22 | **Resultados de la encuesta de satisfacción** (si se aplicó; si no, ajustar el objetivo) | 2 h |

### 🟢 P2 — Pulido; puede ir a la entrega final del 2 de octubre

| # | Tarea |
|---|---|
| 23 | Glosario (SAP, ISO 8000, MDM, pg_trgm, TF-IDF, medallón, UNSPSC, short_text, LLM…) |
| 24 | Análisis build vs. buy en Antecedentes (§4.7) — alto valor para escuela de negocios |
| 25 | Ampliar Antecedentes con literatura de MDM en SAP y DAMA-DMBOK |
| 26 | Ajustar tipografía a Times/Arial 10, quitar negritas, verificar márgenes e interlineado (§3.5) |
| 27 | Anexos reales: manual de usuario, instrumento de encuesta, diccionario de datos, capturas de la herramienta |
| 28 | Revisión ortográfica completa ("corporción" y otras) |
| 29 | Agregar el inciso (d) a la Introducción: adelantar las conclusiones principales |
| 30 | Unificar "Referencias" y "Bibliografía" en una sola sección del índice |

---

## 7. Plan sugerido para los 3 días restantes

Dado que la entrega es el **14 de agosto** y quedan tres días, la estrategia recomendada es **cobertura antes que perfección**: la rúbrica evalúa 8 áreas de contenido, y hoy 7 están en cero. Un capítulo breve pero presente puntúa; un capítulo ausente no puntúa nada.

**Día 1 (11 ago) — Datos y limpieza estructural**
- Tareas 1, 3, 11 (limpieza y extracción de KPIs reales).
- Tarea 4: Metodología completa (cubre rúbrica 2 y 3).
- Si el tiempo alcanza: tareas 12 y 13 (las dos defensas metodológicas más importantes; son consultas y un reentrenamiento corto).

**Día 2 (12 ago) — Núcleo analítico**
- Tarea 5: Explotación de la información.
- Tarea 6: Desarrollo de modelos analíticos.
- Tarea 10: insertar figuras conforme se escribe (no dejarlo para el final).

**Día 3 (13 ago) — Negocio y cierre**
- Tarea 7: Resultados y ROI.
- Tarea 8: Arquitectura y puesta en producción.
- Tarea 9: Conclusiones y Recomendaciones.
- Tarea 2: Resumen (se escribe de último, como indica la guía).
- Revisión de forma y compilación final.

**14 ago:** entrega con margen. **No dejar la compilación para el mismo día.**

Después del 14 de agosto queda tiempo real para pulir: la presentación se envía el **14 de septiembre**, la defensa es el **21 de septiembre** (Grupo 1, 6:00), y la entrega final con las modificaciones de los evaluadores es el **2 de octubre**. Todo lo marcado como P2 —y buena parte de P1— puede atenderse en esa ventana.

---

## 8. Otros entregables del curso (más allá del documento)

| Entregable | Fecha | Estado |
|---|---|---|
| Definición del proyecto | 13 abr 2026 | ✅ Cumplido (obligatorio, sin puntos) |
| **Documento en versión final** | **14 ago 2026** | 🔴 **~35–40 % — 3 días** |
| Envío de la presentación | 14 sept 2026 | 🔴 No iniciada (existe `Presentacion.vue` en el frontend como base) |
| Presentación de negocio, 45 min | 21 sept 2026, 6:00 | 🔴 Pendiente |
| Examen individual por integrante | Tras la presentación | ⚠️ **La calificación es individual.** Los tres integrantes deben dominar todo el proyecto, no solo su parte |
| Entrega final con modificaciones | 2 oct 2026 | — |

**Nota sobre el examen individual:** la rúbrica establece que *"si el estudiante no aprueba el examen individual también debe volver a cursar el Proyecto Integrador"*. Las secciones §4.1 (el 94 %), §4.2 (fuga del primer token), §4.3 (ROI sobre 3.3 h) y §4.9 (el Transformer) son las cuatro preguntas más probables del examen. Conviene que los tres integrantes tengan respuesta preparada para las cuatro.

---

## 9. Lo que está bien y conviene conservar

Para que el diagnóstico no se lea sólo como una lista de faltantes — hay cosas genuinamente buenas aquí:

- **El planteamiento del problema está cuantificado**, no es retórico: 456 duplicados, 246 mal categorizados, 4.4 solicitudes/día, 3.3 h por gestión. Esto es exactamente lo que la rúbrica premia.
- **El Prefacio maneja la confidencialidad con rigor** y declara las limitaciones del alcance por adelantado, tal como pide la guía UVG.
- **El Capítulo 6 (Alcance) es honesto** sobre lo que queda fuera: creación masiva, remediación retroactiva. Delimitar bien protege en la defensa.
- **La validación con usuarios reales durante 5 semanas en producción** es la mayor fortaleza del proyecto. Muy pocos trabajos de graduación llegan a eso, y hay que subrayarlo en la presentación.
- **El rigor de instrumentación es notable**: exclusión de usuarios admin de las vistas KPI, preprocesamiento idéntico entre entrenamiento y producción, timestamps por paso del pipeline. Son detalles de ingeniería que conviene hacer visibles en el documento — hoy están invisibles.
- **La decisión de que GAMMA no escriba directamente en SAP** (asistencia, no automatización ciega) es defendible y madura desde el punto de vista de gobierno de datos. Vale la pena argumentarla explícitamente.
- **El marco teórico de algoritmos está bien construido** y las citas primarias son correctas (Cox 1958, Cortes & Vapnik 1995, Breiman 2001, Chen & Guestrin 2016, Vaswani et al. 2017, Salton & Buckley 1988). Está citando las fuentes originales, no manuales de segunda mano.

---

*Generado el 11 de agosto de 2026 a partir de `GAMMA.pdf`, `Proyecto Final MBIA 2026.pdf`, `Guía para Tesis y Trabajos de graduación.pdf` y el estado del repositorio `mbia_gamma`.*

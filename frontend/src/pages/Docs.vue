<script setup lang="ts">
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import MermaidDiagram from '@/components/MermaidDiagram.vue'

const derBronze = `erDiagram
    ingestion_logs {
        BIGSERIAL id PK
        TEXT file_name
        TEXT file_path
        INTEGER row_count
        TEXT status
        TEXT error_message
        TIMESTAMPTZ ingested_at
    }

    prediction_logs {
        BIGSERIAL id PK
        BIGINT request_id FK
        TEXT type
        JSONB input
        JSONB output
        NUMERIC confidence
        JSONB user_decision
        TIMESTAMPTZ logged_at
    }
`

const derSilver = `erDiagram
    material_types {
        BIGSERIAL id PK
        TEXT code UK
        TEXT description
    }

    unspsc {
        BIGSERIAL id PK
        TEXT code UK
        TEXT description
    }

    classes {
        BIGSERIAL id PK
        TEXT code UK
        TEXT name
        BIGINT material_type_id FK
        BIGINT unspsc_id FK
        TEXT article_group
        TEXT sector
    }

    units_of_measure {
        BIGSERIAL id PK
        TEXT code UK
        TEXT description
    }

    materials {
        BIGSERIAL id PK
        TEXT code UK
        BIGINT class_id FK
        BIGINT unit_of_measure_id FK
        TEXT short_text
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
        BOOLEAN deletion_flag
    }

    conversations {
        UUID id PK
        TEXT title
        JSONB messages
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    requests {
        BIGSERIAL id PK
        UUID conversation_id FK
        BIGINT material_type_id FK
        TEXT name
        TEXT long_text
        JSONB specifications
        TEXT short_text
        TEXT article_group
        TEXT category
        NUMERIC confidence
        JSONB alternatives
        JSONB duplicates
        BOOLEAN auto_resolved
        BOOLEAN corrected
        TEXT status
        TIMESTAMPTZ created_at
        TIMESTAMPTZ confirmed_at
        TIMESTAMPTZ exported_at
        NUMERIC processing_time_s
    }

    dataset_train {
        TEXT short_text
        BIGINT material_type_id FK
        TEXT article_group
    }

    dataset_test {
        TEXT short_text
        BIGINT material_type_id FK
        TEXT article_group
    }

    material_types ||--o{ classes : "material_type_id"
    material_types ||--o{ requests : "material_type_id"
    material_types ||--o{ dataset_train : "material_type_id"
    material_types ||--o{ dataset_test : "material_type_id"
    unspsc ||--o{ classes : "unspsc_id"
    classes ||--o{ materials : "class_id"
    units_of_measure ||--o{ materials : "unit_of_measure_id"
    conversations ||--o{ requests : "conversation_id"
`

const derGold = `erDiagram
    parameters {
        TEXT id PK
        NUMERIC value
    }

    kpi_processing_time {
        TIMESTAMPTZ week
        BIGINT materials
        NUMERIC avg_time_s
        NUMERIC auto_rate
    }

    kpi_quality {
        TIMESTAMPTZ week
        NUMERIC accuracy
        NUMERIC avg_confidence
    }

    kpi_savings {
        TIMESTAMPTZ week
        BIGINT materials
        NUMERIC hours_saved
        NUMERIC savings_q
    }

    materials_by_type {
        TEXT material_type_id
        TEXT type_description
        BIGINT total_materials
    }
`
</script>

<template>
  <section class="py-20 px-6">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold tracking-tight mb-2">Documentacion</h1>
      <p class="text-muted-foreground mb-10">Informacion centralizada del proyecto: esquema de datos, contrato del API, decisiones de diseno y guia de despliegue.</p>

      <Accordion type="multiple" class="w-full">

        <!-- Esquema de datos -->
        <AccordionItem value="esquema">
          <AccordionTrigger class="text-lg font-semibold">Esquema de datos</AccordionTrigger>
          <AccordionContent>
            <div class="space-y-6 text-sm text-muted-foreground">
              <p>
                La base de datos utiliza una <strong class="text-foreground">arquitectura medallon de tres capas</strong> implementada
                como esquemas de PostgreSQL. Esta separacion no introduce overhead de rendimiento — los esquemas son namespaces logicos
                dentro del mismo motor y la misma conexion — pero aporta claridad organizacional al definir responsabilidades
                claras para cada capa.
              </p>

              <Separator />

              <div>
                <div class="flex items-center gap-2 mb-2">
                  <Badge class="bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 hover:bg-amber-100">Bronze</Badge>
                  <span class="text-foreground font-medium">Logs y trazabilidad</span>
                </div>
                <p class="mb-2">
                  Bronze registra la actividad del sistema sin almacenar datos crudos — los archivos XLSX de SAP
                  se conservan en disco y se reprocesan si es necesario. Esta capa cumple dos funciones:
                </p>
                <p class="mb-2">
                  <strong class="text-foreground">Logs de ingesta:</strong> cada vez que se importa un archivo de SAP,
                  se registra el nombre, ruta, cantidad de filas procesadas y estado de la operacion. Esto permite
                  trazabilidad sin duplicar datos en la base.
                </p>
                <p class="mb-4">
                  <strong class="text-foreground">Logs de prediccion:</strong> cada vez que el sistema ejecuta uno de
                  los tres servicios (duplicados, descripcion, categorizacion), se registra la entrada, salida del modelo,
                  confianza y la decision final del usuario. Esta informacion alimenta los KPIs de gold y permite evaluar
                  el modelo a lo largo del tiempo.
                </p>
                <MermaidDiagram :chart="derBronze" />
              </div>

              <Separator />

              <div>
                <div class="flex items-center gap-2 mb-2">
                  <Badge class="bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-200 hover:bg-slate-200">Silver</Badge>
                  <span class="text-foreground font-medium">Datos operacionales y de referencia</span>
                </div>
                <p class="mb-2">
                  Silver es la capa de trabajo. Aqui viven los datos normalizados que el API consulta y modifica en cada
                  solicitud. El maestro de materiales se almacena limpio y con un indice de similitud difusa (pg_trgm)
                  que permite buscar duplicados de forma eficiente.
                </p>
                <p class="mb-2">
                  Las solicitudes de alta de material se gestionan completamente en esta capa, desde la propuesta inicial
                  hasta la confirmacion y exportacion. Cada solicitud registra tiempos de procesamiento, categoria asignada,
                  nivel de confianza y si el usuario corrigio la propuesta del sistema — datos que alimentan directamente
                  las vistas de gold.
                </p>
                <p class="mb-4">
                  Tambien contiene los datasets de entrenamiento y prueba para el modelo de categorizacion, derivados del
                  maestro normalizado. Esto permite que el laboratorio (Jupyter) acceda directamente a datos listos para
                  experimentacion sin necesidad de procesamiento adicional.
                </p>
                <MermaidDiagram :chart="derSilver" />
              </div>

              <Separator />

              <div>
                <div class="flex items-center gap-2 mb-2">
                  <Badge class="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 hover:bg-yellow-100">Gold</Badge>
                  <span class="text-foreground font-medium">Agregados para dashboard</span>
                </div>
                <p class="mb-2">
                  Gold contiene exclusivamente vistas y parametros de configuracion. No se escriben datos directamente en
                  esta capa — las vistas leen de silver al momento de ser consultadas. Esto garantiza que los indicadores
                  siempre reflejen el estado actual sin necesidad de procesos de sincronizacion.
                </p>
                <p class="mb-4">
                  Los KPIs cubren tres dimensiones: tiempos de procesamiento (promedio por semana, tasa de auto-resolucion),
                  calidad del modelo (exactitud de la categorizacion, confianza promedio) y monetizacion (horas-hombre
                  ahorradas y su equivalente en quetzales). Power BI se conecta directamente a este esquema.
                </p>
                <MermaidDiagram :chart="derGold" />
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-2">Justificacion de la arquitectura</h4>
                <ul class="space-y-2 list-disc list-inside">
                  <li>
                    <strong>Tres capas en lugar de staging + medallon:</strong> el esquema staging original era
                    redundante con silver. Al unificarlos, el API escribe directamente en silver y se elimina
                    la necesidad de promover datos entre esquemas operacionales.
                  </li>
                  <li>
                    <strong>Bronze como capa de logs:</strong> los archivos XLSX se conservan en disco, no en la
                    base de datos. Bronze solo registra metadatos de ingesta y logs de prediccion — datos crudos
                    del sistema, no datos de trabajo.
                  </li>
                  <li>
                    <strong>Gold como vistas puras:</strong> al no materializar datos en gold, se evita la
                    duplicacion y la desincronizacion. Los KPIs se calculan en tiempo real sobre silver.
                  </li>
                  <li>
                    <strong>Todo en una sola instancia de PostgreSQL:</strong> la comunicacion entre esquemas no
                    tiene costo adicional. Un JOIN entre silver y gold es identico a un JOIN entre tablas del mismo
                    esquema. La separacion es puramente organizacional.
                  </li>
                </ul>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        <!-- API -->
        <AccordionItem value="api">
          <AccordionTrigger class="text-lg font-semibold">API</AccordionTrigger>
          <AccordionContent>
            <div class="space-y-4 text-sm text-muted-foreground">
              <div>
                <h4 class="text-foreground font-medium mb-1">Por que Python</h4>
                <p>
                  Python es el lenguaje natural para este proyecto porque el equipo ya trabaja con el en analisis
                  de datos y machine learning. Las librerias del ecosistema cientifico (pandas, scikit-learn, openpyxl)
                  se integran directamente en el backend sin necesidad de servicios intermedios. Usar el mismo lenguaje
                  para el API, el modelo y la exportacion reduce la friccion y permite que cualquier miembro del equipo
                  contribuya en cualquier parte del sistema.
                </p>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-1">Por que FastAPI</h4>
                <p>
                  FastAPI combina rendimiento con productividad. La validacion automatica con Pydantic garantiza que
                  los datos que entran y salen del API cumplen con el contrato definido — si un campo falta o tiene
                  el tipo incorrecto, el error se detecta antes de llegar a la logica de negocio. La documentacion
                  Swagger se genera automaticamente a partir de los modelos, eliminando la necesidad de mantenerla
                  por separado. Ademas, su soporte nativo para operaciones asincronas permite manejar llamadas al
                  LLM y al modelo sin bloquear el servidor.
                </p>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-2">Endpoints</h4>
                <div class="space-y-3">
                  <div class="p-3 rounded-md border bg-card">
                    <div class="flex items-center gap-2 mb-1">
                      <Badge variant="outline" class="text-xs font-mono">GET</Badge>
                      <code class="text-xs">/api/health</code>
                    </div>
                    <p class="text-xs">Verificacion de salud del servicio.</p>
                  </div>

                  <div class="p-3 rounded-md border bg-card">
                    <div class="flex items-center gap-2 mb-1">
                      <Badge variant="outline" class="text-xs font-mono">POST</Badge>
                      <code class="text-xs">/api/duplicates</code>
                    </div>
                    <p class="text-xs">Realiza fuzzy search contra el maestro existente en silver, aprovechando la extension pg_trgm de PostgreSQL para encontrar materiales similares sin requerir coincidencias exactas.</p>
                  </div>

                  <div class="p-3 rounded-md border bg-card">
                    <div class="flex items-center gap-2 mb-1">
                      <Badge variant="outline" class="text-xs font-mono">POST</Badge>
                      <code class="text-xs">/api/model/predict</code>
                    </div>
                    <p class="text-xs">Ejecuta el modelo de clasificacion y devuelve la categoria predicha, nivel de confianza y las top-K alternativas.</p>
                  </div>
                </div>

                <p class="mt-3">
                  La documentacion interactiva completa esta disponible en la seccion
                  <a href="/api" class="text-foreground underline underline-offset-4">API</a> de este portal.
                </p>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        <!-- Decisiones de diseno -->
        <AccordionItem value="decisiones">
          <AccordionTrigger class="text-lg font-semibold">Decisiones de diseno</AccordionTrigger>
          <AccordionContent>
            <div class="space-y-4 text-sm text-muted-foreground">
              <div>
                <h4 class="text-foreground font-medium mb-1">Modelo integrado en la API</h4>
                <p>
                  El modelo de categorizacion no es un servicio separado. Vive dentro del API como un endpoint mas.
                  Esto simplifica la orquestacion (un contenedor menos), el despliegue y la comunicacion. El endpoint
                  <code>/api/model/predict</code> mantiene un contrato fijo: cambiar el modelo interno no requiere
                  cambios en ningun otro componente.
                </p>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-1">Confirmacion humana obligatoria</h4>
                <p>
                  Ninguna propuesta del sistema se persiste sin revision del usuario. Esto no es solo una medida de
                  seguridad — es el mecanismo que genera los datos de correccion que alimentan los KPIs de calidad
                  y permiten medir si el modelo mejora con el tiempo.
                </p>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-1">Exportacion Excel para carga masiva</h4>
                <p>
                  SAP no expone una API de escritura accesible para este flujo. La solucion pragmatica es generar
                  archivos .xlsx formateados para el proceso de carga masiva existente. Esto se integra sin friccion
                  con el flujo actual del equipo.
                </p>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-1">Importacion incremental de SAP</h4>
                <p>
                  Los CSV del maestro y las categorias se importan periodicamente con logica incremental — solo se
                  agregan o actualizan registros nuevos. Bronze conserva cada ingesta con timestamp para trazabilidad
                  y silver se actualiza con los datos normalizados.
                </p>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-1">Monetizacion por ahorro de horas-hombre</h4>
                <p>
                  El sistema registra el tiempo que tarda en procesar cada solicitud. Comparado contra la linea base
                  del proceso manual (parametro configurable), se calcula el ahorro en horas y su equivalente monetario.
                  Esto permite justificar la inversion en la herramienta con datos concretos.
                </p>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        <!-- Modelo de clasificacion -->
        <AccordionItem value="modelo">
          <AccordionTrigger class="text-lg font-semibold">Modelo de clasificacion</AccordionTrigger>
          <AccordionContent>
            <div class="space-y-6 text-sm text-muted-foreground">
              <p>
                El sistema predice la <strong class="text-foreground">clase de material</strong> (denominacion estandar)
                a partir del <code>short_text</code> de SAP. El modelo fue entrenado con <strong class="text-foreground">39,571 materiales</strong>
                distribuidos en <strong class="text-foreground">1,234 clases</strong>, extraidos de 13 archivos Excel de distintos
                tipos de material (ZCON, ZQUI, ZRPI, ZSUM, etc.).
              </p>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-2">Pipeline</h4>
                <ol class="list-decimal list-inside space-y-1">
                  <li><strong class="text-foreground">Preprocesamiento:</strong> uppercase, eliminar acentos, reemplazar delimitadores (<code>;:,/</code>) por espacios, conservar solo alfanumericos.</li>
                  <li><strong class="text-foreground">Vectorizacion TF-IDF:</strong> convierte el texto limpio en un vector sparse de 50,000 dimensiones usando character n-grams (2-5 caracteres).</li>
                  <li><strong class="text-foreground">Clasificacion:</strong> un modelo LinearSVC calibrado mapea el vector a una de las 1,234 clases y devuelve probabilidades de confianza.</li>
                </ol>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-3">Modelos evaluados</h4>
                <div class="space-y-4">

                  <div class="p-4 rounded-md border bg-card">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="text-foreground font-medium">1. Logistic Regression + Character TF-IDF</span>
                    </div>
                    <p class="mb-2">
                      Regresion logistica multinomial (<code>solver='saga'</code>, <code>C=5.0</code>) sobre vectores TF-IDF
                      de character n-grams (2-5, 50k features). Modela la probabilidad de cada clase como una funcion softmax
                      sobre combinaciones lineales de los features. Produce probabilidades calibradas de forma nativa y es
                      interpretable, pero la convergencia fue extremadamente lenta — <strong class="text-foreground">1,071 segundos</strong>
                      (17 minutos) con 50k character features.
                    </p>
                  </div>

                  <div class="p-4 rounded-md border bg-card">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="text-foreground font-medium">2. Logistic Regression + Word TF-IDF</span>
                    </div>
                    <p class="mb-2">
                      Misma regresion logistica pero tokenizando por <strong class="text-foreground">palabras completas</strong>
                      (unigramas y bigramas, 30k features). Captura terminos exactos como "CABLE ELECTRICO", pero pierde la
                      capacidad de reconocer subpalabras. Esto lo hace vulnerable a las abreviaciones y typos comunes en textos
                      SAP. Rapido de entrenar (29s) y con buenas probabilidades nativas.
                    </p>
                  </div>

                  <div class="p-4 rounded-md border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="text-foreground font-medium">3. LinearSVC + Character TF-IDF</span>
                      <Badge class="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 hover:bg-green-100">Ganador</Badge>
                    </div>
                    <p class="mb-2">
                      Support Vector Machine lineal (<code>LinearSVC</code>, <code>C=1.0</code>) envuelto en
                      <code>CalibratedClassifierCV</code> para obtener probabilidades. Encuentra hiperplanos que maximizan
                      el margen de separacion entre clases en un espacio de 50k dimensiones de character n-grams. A diferencia
                      de la regresion logistica que optimiza log-likelihood, SVM optimiza directamente el margen de decision,
                      lo que suele generalizar mejor.
                    </p>
                    <p class="mb-2">
                      El uso de <strong class="text-foreground">character n-grams</strong> (2-5 caracteres) es clave para textos SAP:
                      captura subpalabras ("TORNI", "ORNIL" de "TORNILLO"), es robusto a abreviaciones ("ELECTR" matchea tanto
                      "ELECTRICO" como "ELECTRONICO"), tolerante a typos, y <code>char_wb</code> respeta limites de palabra
                      evitando n-grams espurios.
                    </p>
                    <p>
                      Mejor accuracy y F1 de todos los modelos con un tiempo de entrenamiento razonable (63s). Las probabilidades
                      son aproximadas (calibradas post-hoc via Platt scaling), no nativas.
                    </p>
                  </div>

                  <div class="p-4 rounded-md border bg-card">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="text-foreground font-medium">4. Random Forest + Word TF-IDF</span>
                    </div>
                    <p class="mb-2">
                      Ensemble de 300 arboles de decision, cada uno entrenado sobre un subconjunto aleatorio de datos y features.
                      La prediccion es el voto mayoritario. Cada arbol aprende reglas como "si TF-IDF de TORNILLO &gt; 0.3 y
                      TF-IDF de HEXAGONAL &gt; 0.1, entonces clase X". Robusto a overfitting y no requiere calibracion para
                      probabilidades. Buen F1 macro pero no captura patrones sub-palabra y es mas lento en inferencia (300 arboles).
                    </p>
                  </div>

                  <Separator />
                  <p class="text-xs text-muted-foreground italic">Los siguientes 3 modelos fueron evaluados en una segunda ronda de experimentacion (notebook 03) contra el baseline ganador.</p>

                  <div class="p-4 rounded-md border bg-card">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="text-foreground font-medium">5. XGBoost + Character TF-IDF</span>
                    </div>
                    <p class="mb-2">
                      Gradient boosting (<code>XGBClassifier</code>, 500 arboles, <code>max_depth=6</code>, <code>lr=0.1</code>)
                      sobre los mismos vectores CharTFIDF de 50k features. XGBoost construye arboles secuencialmente, donde cada
                      arbol nuevo corrige los errores del anterior. Usa <code>multi:softprob</code> para clasificacion multiclase
                      y produce probabilidades nativas. A pesar de ser el metodo dominante en datos tabulares, no supero al LinearSVC
                      en este problema — los vectores TF-IDF sparse de alta dimensionalidad favorecen a modelos lineales.
                      Extremadamente lento: <strong class="text-foreground">11,025 segundos</strong> (~3 horas) por la combinacion
                      de 500 arboles x 1,234 clases.
                    </p>
                  </div>

                  <div class="p-4 rounded-md border bg-card">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="text-foreground font-medium">6. fastText</span>
                    </div>
                    <p class="mb-2">
                      Modelo de Facebook Research que aprende embeddings de subpalabras de forma nativa — no necesita TF-IDF externo.
                      Cada palabra se descompone en character n-grams (2-5) y el embedding final es la suma de sus componentes.
                      Configurado con <code>epoch=50</code>, <code>lr=0.5</code>, <code>dim=100</code>, <code>wordNgrams=2</code>
                      y loss <code>softmax</code>. Extremadamente rapido de entrenar (<strong class="text-foreground">43 segundos</strong>),
                      lo que lo hace ideal para iteracion rapida. Rendimiento competitivo (accuracy 80.8%) pero por debajo del
                      LinearSVC, probablemente porque los embeddings de 100 dimensiones comprimen demasiado la informacion que
                      el espacio sparse de 50k dimensiones preserva.
                    </p>
                  </div>

                  <div class="p-4 rounded-md border bg-card">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="text-foreground font-medium">7. Transformer fine-tuned (Multilingual-MiniLM)</span>
                      <Badge class="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 hover:bg-red-100">Fallido</Badge>
                    </div>
                    <p class="mb-2">
                      Transformer pre-entrenado de Microsoft (<code>Multilingual-MiniLM-L12-H384</code>, 118M parametros, 12 capas,
                      384 dimensiones hidden) fine-tuneado con 5 epochs, <code>batch_size=64</code>, <code>lr=2e-5</code> y
                      <code>max_len=64</code> tokens. A pesar de ser el modelo mas sofisticado, obtuvo un
                      <strong class="text-foreground">accuracy de solo 3.95%</strong> — esencialmente aleatorio para 1,234 clases.
                    </p>
                    <p class="mb-2">
                      El fracaso se explica por la combinacion de <strong class="text-foreground">muchas clases (1,234) con pocos
                      ejemplos por clase</strong> (mediana de 9). Fine-tunear un transformer requiere cientos de ejemplos por clase
                      para ajustar los 118M parametros. Con solo 5 epochs y ~25 ejemplos promedio por clase en train, el modelo
                      no logro aprender patrones discriminativos — la loss apenas bajo de 6.9 a 5.96 y el train accuracy nunca
                      supero 3.6%. Los textos SAP cortos (5-8 tokens promedio) tambien subaprovechan la capacidad del transformer
                      de modelar dependencias contextuales largas.
                    </p>
                  </div>
                </div>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-3">Comparacion de metricas</h4>
                <div class="overflow-x-auto">
                  <table class="w-full text-xs">
                    <thead>
                      <tr class="border-b">
                        <th class="text-left py-2 pr-3 text-foreground">Modelo</th>
                        <th class="text-right py-2 px-2 text-foreground">Accuracy</th>
                        <th class="text-right py-2 px-2 text-foreground">F1 Macro</th>
                        <th class="text-right py-2 px-2 text-foreground">F1 Weighted</th>
                        <th class="text-right py-2 px-2 text-foreground">Precision</th>
                        <th class="text-right py-2 px-2 text-foreground">Recall</th>
                        <th class="text-right py-2 px-2 text-foreground">Top-3 Acc</th>
                        <th class="text-right py-2 pl-2 text-foreground">Tiempo</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr class="border-b">
                        <td class="py-2 pr-3">LogReg + CharTFIDF</td>
                        <td class="text-right py-2 px-2">0.8293</td>
                        <td class="text-right py-2 px-2">0.6713</td>
                        <td class="text-right py-2 px-2">0.8126</td>
                        <td class="text-right py-2 px-2">0.8158</td>
                        <td class="text-right py-2 px-2">0.8293</td>
                        <td class="text-right py-2 px-2">0.9359</td>
                        <td class="text-right py-2 pl-2">1071.2s</td>
                      </tr>
                      <tr class="border-b">
                        <td class="py-2 pr-3">LogReg + WordTFIDF</td>
                        <td class="text-right py-2 px-2">0.8291</td>
                        <td class="text-right py-2 px-2">0.6949</td>
                        <td class="text-right py-2 px-2">0.8178</td>
                        <td class="text-right py-2 px-2">0.8265</td>
                        <td class="text-right py-2 px-2">0.8291</td>
                        <td class="text-right py-2 px-2">0.9275</td>
                        <td class="text-right py-2 pl-2">29.1s</td>
                      </tr>
                      <tr class="border-b bg-green-50 dark:bg-green-950 font-medium text-foreground">
                        <td class="py-2 pr-3">LinearSVC + CharTFIDF</td>
                        <td class="text-right py-2 px-2">0.8491</td>
                        <td class="text-right py-2 px-2">0.7523</td>
                        <td class="text-right py-2 px-2">0.8380</td>
                        <td class="text-right py-2 px-2">0.8419</td>
                        <td class="text-right py-2 px-2">0.8491</td>
                        <td class="text-right py-2 px-2">0.9404</td>
                        <td class="text-right py-2 pl-2">62.9s</td>
                      </tr>
                      <tr class="border-b">
                        <td class="py-2 pr-3">RandomForest + WordTFIDF</td>
                        <td class="text-right py-2 px-2">0.8334</td>
                        <td class="text-right py-2 px-2">0.7360</td>
                        <td class="text-right py-2 px-2">0.8254</td>
                        <td class="text-right py-2 px-2">0.8354</td>
                        <td class="text-right py-2 px-2">0.8334</td>
                        <td class="text-right py-2 px-2">0.9263</td>
                        <td class="text-right py-2 pl-2">46.7s</td>
                      </tr>
                      <tr class="border-b border-t-2 border-t-muted">
                        <td class="py-2 pr-3">XGBoost + CharTFIDF</td>
                        <td class="text-right py-2 px-2">0.8145</td>
                        <td class="text-right py-2 px-2">0.6821</td>
                        <td class="text-right py-2 px-2">0.8063</td>
                        <td class="text-right py-2 px-2">0.8136</td>
                        <td class="text-right py-2 px-2">0.8145</td>
                        <td class="text-right py-2 px-2">0.9200</td>
                        <td class="text-right py-2 pl-2">11025.2s</td>
                      </tr>
                      <tr class="border-b">
                        <td class="py-2 pr-3">fastText</td>
                        <td class="text-right py-2 px-2">0.8077</td>
                        <td class="text-right py-2 px-2">0.6897</td>
                        <td class="text-right py-2 px-2">0.8001</td>
                        <td class="text-right py-2 px-2">0.8071</td>
                        <td class="text-right py-2 px-2">0.8075</td>
                        <td class="text-right py-2 px-2">0.9075</td>
                        <td class="text-right py-2 pl-2">43.0s</td>
                      </tr>
                      <tr>
                        <td class="py-2 pr-3 text-muted-foreground/60">Transformer (MiniLM)</td>
                        <td class="text-right py-2 px-2 text-red-500">0.0395</td>
                        <td class="text-right py-2 px-2 text-red-500">0.0003</td>
                        <td class="text-right py-2 px-2 text-red-500">0.0050</td>
                        <td class="text-right py-2 px-2 text-red-500">0.0032</td>
                        <td class="text-right py-2 px-2 text-red-500">0.0395</td>
                        <td class="text-right py-2 px-2 text-red-500">0.0714</td>
                        <td class="text-right py-2 pl-2">1460.0s</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-2">Por que LinearSVC + CharTFIDF</h4>
                <p class="mb-3">
                  Tras evaluar <strong class="text-foreground">7 modelos en 2 rondas de experimentacion</strong>, LinearSVC + CharTFIDF
                  se confirma como el mejor modelo para este problema.
                </p>
                <ul class="space-y-2 list-disc list-inside">
                  <li>
                    <strong class="text-foreground">Mejor en todas las metricas:</strong> Accuracy (84.9%), F1 Weighted (83.8%),
                    F1 Macro (75.2%) y Top-3 Accuracy (94.0%) — superior en cada dimension frente a los 6 modelos restantes.
                  </li>
                  <li>
                    <strong class="text-foreground">F1 Macro significativamente mayor:</strong> 0.7523 vs 0.6713-0.7360 del resto.
                    Mejor rendimiento en clases minoritarias, critico con 1,234 clases desbalanceadas.
                  </li>
                  <li>
                    <strong class="text-foreground">Top-3 Accuracy del 94%:</strong> en el 94% de los casos, la clase correcta
                    esta entre las 3 primeras predicciones. Permite flujos donde el usuario selecciona de una lista corta.
                  </li>
                  <li>
                    <strong class="text-foreground">Tiempo razonable:</strong> 63 segundos de entrenamiento. XGBoost tardo 3 horas
                    con peores resultados; el transformer tardo 24 minutos y fallo completamente.
                  </li>
                  <li>
                    <strong class="text-foreground">Character n-grams:</strong> la ventaja sobre modelos word-level y embeddings
                    (fastText, transformer) confirma que los textos SAP se benefician de analisis sub-palabra en un espacio sparse
                    de alta dimensionalidad. Los modelos que comprimen la representacion (fastText 100d, MiniLM 384d) pierden
                    informacion discriminativa.
                  </li>
                  <li>
                    <strong class="text-foreground">Modelos complejos no ayudan:</strong> ni gradient boosting (XGBoost), ni
                    subword embeddings (fastText), ni transformers pre-entrenados superaron a un SVM lineal. Esto sugiere que
                    el problema es fundamentalmente lineal en el espacio de character n-grams — la complejidad adicional no
                    aporta y en el caso del transformer, perjudica por overfitting con pocos ejemplos por clase.
                  </li>
                </ul>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-3">Matriz de confusion (Top 20 clases)</h4>
                <p class="mb-3">
                  Evaluada sobre el conjunto de prueba (7,915 materiales). El modelo comete
                  <strong class="text-foreground">1,194 errores (15.09%)</strong> en total. A continuacion
                  el desglose por clase para las 20 mas frecuentes.
                </p>

                <div>
                  <h5 class="text-foreground font-medium text-xs mb-2">Clases con buen rendimiento (F1 &gt; 0.90)</h5>
                  <p class="mb-3">
                    14 de las 20 clases principales superan F1 de 0.90. Son clases con vocabulario distintivo donde el
                    texto casi siempre contiene el nombre de la clase.
                  </p>
                  <div class="overflow-x-auto mb-4">
                    <table class="w-full text-xs">
                      <thead>
                        <tr class="border-b">
                          <th class="text-left py-2 pr-3 text-foreground">Clase</th>
                          <th class="text-right py-2 px-2 text-foreground">Precision</th>
                          <th class="text-right py-2 px-2 text-foreground">Recall</th>
                          <th class="text-right py-2 px-2 text-foreground">F1</th>
                          <th class="text-right py-2 pl-2 text-foreground">Soporte</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr class="border-b"><td class="py-1.5 pr-3">CAMISA</td><td class="text-right px-2">1.00</td><td class="text-right px-2">0.99</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">1.00</td><td class="text-right pl-2">105</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">TEE:TUBERIA</td><td class="text-right px-2">1.00</td><td class="text-right px-2">1.00</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">1.00</td><td class="text-right pl-2">59</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">CODO:TUBERIAS</td><td class="text-right px-2">0.99</td><td class="text-right px-2">1.00</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.99</td><td class="text-right pl-2">94</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">ESLINGA</td><td class="text-right px-2">1.00</td><td class="text-right px-2">0.95</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.98</td><td class="text-right pl-2">63</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">MANGUERA</td><td class="text-right px-2">1.00</td><td class="text-right px-2">0.96</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.98</td><td class="text-right pl-2">55</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">TORNILLO</td><td class="text-right px-2">0.95</td><td class="text-right px-2">0.98</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.97</td><td class="text-right pl-2">130</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">TUBO</td><td class="text-right px-2">0.97</td><td class="text-right px-2">0.96</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.97</td><td class="text-right pl-2">77</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">INSUMOS:OFICINA</td><td class="text-right px-2">1.00</td><td class="text-right px-2">0.90</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.95</td><td class="text-right pl-2">87</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">CUBO</td><td class="text-right px-2">0.95</td><td class="text-right px-2">0.94</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.94</td><td class="text-right pl-2">62</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">SENSOR</td><td class="text-right px-2">0.96</td><td class="text-right px-2">0.92</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.94</td><td class="text-right pl-2">59</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">CABLE</td><td class="text-right px-2">0.99</td><td class="text-right px-2">0.87</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.93</td><td class="text-right pl-2">118</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">CONECTOR</td><td class="text-right px-2">0.98</td><td class="text-right px-2">0.89</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.93</td><td class="text-right pl-2">72</td></tr>
                        <tr class="border-b"><td class="py-1.5 pr-3">RODAMIENTO</td><td class="text-right px-2">0.98</td><td class="text-right px-2">0.88</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.93</td><td class="text-right pl-2">52</td></tr>
                        <tr><td class="py-1.5 pr-3">LLAVE</td><td class="text-right px-2">0.97</td><td class="text-right px-2">0.88</td><td class="text-right px-2 text-green-600 dark:text-green-400 font-medium">0.92</td><td class="text-right pl-2">96</td></tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <div>
                  <h5 class="text-foreground font-medium text-xs mb-2">Clases problematicas (F1 &lt; 0.70)</h5>
                  <div class="overflow-x-auto mb-3">
                    <table class="w-full text-xs">
                      <thead>
                        <tr class="border-b">
                          <th class="text-left py-2 pr-3 text-foreground">Clase</th>
                          <th class="text-right py-2 px-2 text-foreground">Precision</th>
                          <th class="text-right py-2 px-2 text-foreground">Recall</th>
                          <th class="text-right py-2 px-2 text-foreground">F1</th>
                          <th class="text-right py-2 px-2 text-foreground">Soporte</th>
                          <th class="text-left py-2 pl-3 text-foreground">Causa</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr class="border-b">
                          <td class="py-1.5 pr-3">BUJE:ELECTRICO</td>
                          <td class="text-right px-2 text-red-600 dark:text-red-400 font-medium">0.25</td>
                          <td class="text-right px-2 text-red-600 dark:text-red-400 font-medium">0.02</td>
                          <td class="text-right px-2 text-red-600 dark:text-red-400 font-medium">0.04</td>
                          <td class="text-right px-2">51</td>
                          <td class="pl-3">Recall casi nulo — solo 1 de 51 muestras predicha correctamente. Confundida con TORNILLO.</td>
                        </tr>
                        <tr class="border-b">
                          <td class="py-1.5 pr-3">REPUESTO</td>
                          <td class="text-right px-2">0.74</td>
                          <td class="text-right px-2 text-red-600 dark:text-red-400 font-medium">0.40</td>
                          <td class="text-right px-2 text-red-600 dark:text-red-400 font-medium">0.52</td>
                          <td class="text-right px-2">131</td>
                          <td class="pl-3">Clase generica (repuesto). El texto describe <em>que</em> es la pieza, asi que el modelo predice la clase especifica en vez de la generica.</td>
                        </tr>
                        <tr>
                          <td class="py-1.5 pr-3">HERRAMIENTA</td>
                          <td class="text-right px-2">0.82</td>
                          <td class="text-right px-2 text-red-600 dark:text-red-400 font-medium">0.47</td>
                          <td class="text-right px-2 text-red-600 dark:text-red-400 font-medium">0.60</td>
                          <td class="text-right px-2">59</td>
                          <td class="pl-3">Mismo problema — "LLAVE ALLEN 5MM" parece mas LLAVE que HERRAMIENTA.</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-3">Top 10 confusiones mas frecuentes</h4>
                <p class="mb-3">
                  La mayoria de errores ocurren entre clases que son esencialmente
                  <strong class="text-foreground">el mismo concepto con nombres distintos</strong> — un problema de
                  calidad de datos en el catalogo de clases, no del modelo.
                </p>
                <div class="overflow-x-auto">
                  <table class="w-full text-xs">
                    <thead>
                      <tr class="border-b">
                        <th class="text-left py-2 pr-3 text-foreground">Clase real</th>
                        <th class="text-left py-2 px-2 text-foreground">Prediccion</th>
                        <th class="text-right py-2 px-2 text-foreground">Errores</th>
                        <th class="text-left py-2 pl-3 text-foreground">Tipo</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr class="border-b">
                        <td class="py-1.5 pr-3">CONTACTOR:ELECT.</td>
                        <td class="px-2">CONTACTO:ELECT.</td>
                        <td class="text-right px-2">7</td>
                        <td class="pl-3"><Badge variant="outline" class="text-[10px]">nombre similar</Badge></td>
                      </tr>
                      <tr class="border-b">
                        <td class="py-1.5 pr-3">TUBO:NO METALICO</td>
                        <td class="px-2">TUBO</td>
                        <td class="text-right px-2">6</td>
                        <td class="pl-3"><Badge variant="outline" class="text-[10px]">subclase vs general</Badge></td>
                      </tr>
                      <tr class="border-b">
                        <td class="py-1.5 pr-3">FUENTE:ALIMENTACION</td>
                        <td class="px-2">FUENTE ALIMENTACION</td>
                        <td class="text-right px-2">6</td>
                        <td class="pl-3"><Badge variant="outline" class="text-[10px]">formato distinto</Badge></td>
                      </tr>
                      <tr class="border-b">
                        <td class="py-1.5 pr-3">CARGADOR DE BATERIAS</td>
                        <td class="px-2">CARGADOR:BATERIAS</td>
                        <td class="text-right px-2">6</td>
                        <td class="pl-3"><Badge variant="outline" class="text-[10px]">formato distinto</Badge></td>
                      </tr>
                      <tr class="border-b">
                        <td class="py-1.5 pr-3">FUSIBLE</td>
                        <td class="px-2">FUSIBLE</td>
                        <td class="text-right px-2">5</td>
                        <td class="pl-3"><Badge variant="outline" class="text-[10px]">clases duplicadas</Badge></td>
                      </tr>
                      <tr class="border-b">
                        <td class="py-1.5 pr-3">INTERRUPTOR</td>
                        <td class="px-2">INTERRUPTOR:AUTOMATICO</td>
                        <td class="text-right px-2">5</td>
                        <td class="pl-3"><Badge variant="outline" class="text-[10px]">subclase vs general</Badge></td>
                      </tr>
                      <tr class="border-b">
                        <td class="py-1.5 pr-3">REPUESTO</td>
                        <td class="px-2">INTERRUPTOR:AUTOMATICO</td>
                        <td class="text-right px-2">4</td>
                        <td class="pl-3"><Badge variant="outline" class="text-[10px]">clase generica</Badge></td>
                      </tr>
                      <tr class="border-b">
                        <td class="py-1.5 pr-3">FUENTE ALIMENTACION</td>
                        <td class="px-2">FUENTE:ALIMENTACION</td>
                        <td class="text-right px-2">4</td>
                        <td class="pl-3"><Badge variant="outline" class="text-[10px]">formato distinto</Badge></td>
                      </tr>
                      <tr class="border-b">
                        <td class="py-1.5 pr-3">TRANSFORMADOR</td>
                        <td class="px-2">TRANSFORMADOR:CORRIENTE</td>
                        <td class="text-right px-2">4</td>
                        <td class="pl-3"><Badge variant="outline" class="text-[10px]">subclase vs general</Badge></td>
                      </tr>
                      <tr>
                        <td class="py-1.5 pr-3">BUJE:ELECTRICO</td>
                        <td class="px-2">TORNILLO</td>
                        <td class="text-right px-2">4</td>
                        <td class="pl-3"><Badge variant="outline" class="text-[10px]">confusion real</Badge></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p class="mt-3">
                  Solo 1 de las 10 confusiones principales es una <strong class="text-foreground">confusion real</strong>
                  del modelo. Las otras 9 son problemas de naming en el catalogo de clases (duplicados, formatos distintos,
                  subclases). Unificar estas clases duplicadas mejoraria la accuracy sin tocar el modelo.
                </p>
              </div>

              <Separator />

              <div>
                <h4 class="text-foreground font-medium mb-3">Analisis de confianza</h4>
                <p class="mb-3">
                  El modelo sabe cuando esta inseguro. Filtrando por umbral de confianza se puede aumentar la accuracy
                  a cambio de cubrir menos materiales automaticamente.
                </p>
                <div class="overflow-x-auto mb-3">
                  <table class="w-full text-xs">
                    <thead>
                      <tr class="border-b">
                        <th class="text-left py-2 pr-3 text-foreground">Umbral</th>
                        <th class="text-right py-2 px-2 text-foreground">Accuracy</th>
                        <th class="text-right py-2 px-2 text-foreground">Cobertura</th>
                        <th class="text-right py-2 pl-2 text-foreground">Materiales</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr class="border-b"><td class="py-1.5 pr-3">0.50</td><td class="text-right px-2">92.80%</td><td class="text-right px-2">78.81%</td><td class="text-right pl-2">6,238</td></tr>
                      <tr class="border-b"><td class="py-1.5 pr-3">0.60</td><td class="text-right px-2">94.84%</td><td class="text-right px-2">70.50%</td><td class="text-right pl-2">5,580</td></tr>
                      <tr class="border-b"><td class="py-1.5 pr-3">0.70</td><td class="text-right px-2">96.74%</td><td class="text-right px-2">60.52%</td><td class="text-right pl-2">4,790</td></tr>
                      <tr><td class="py-1.5 pr-3">0.80</td><td class="text-right px-2">98.62%</td><td class="text-right px-2">42.25%</td><td class="text-right pl-2">3,344</td></tr>
                    </tbody>
                  </table>
                </div>
                <p>
                  Esto habilita un flujo de <strong class="text-foreground">auto-aprobacion</strong>: predicciones por
                  encima del umbral se aceptan automaticamente, las demas pasan a
                  <strong class="text-foreground">revision humana</strong>. El umbral es un parametro configurable en
                  <code>gold.parameters</code>.
                </p>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        <!-- Guia de despliegue -->
        <AccordionItem value="despliegue">
          <AccordionTrigger class="text-lg font-semibold">Guia de despliegue</AccordionTrigger>
          <AccordionContent>
            <div class="space-y-4 text-sm text-muted-foreground">
              <p>Todo el proyecto se orquesta con Docker Compose. Cuatro servicios en una red interna:</p>

              <div class="grid grid-cols-2 gap-3">
                <div class="p-3 rounded-md border bg-card">
                  <p class="text-foreground font-medium text-xs mb-1">db (PostgreSQL 16)</p>
                  <p class="text-xs">Puerto 5436. Esquemas bronze, silver y gold. Scripts de inicializacion en <code>db/init/</code>.</p>
                </div>
                <div class="p-3 rounded-md border bg-card">
                  <p class="text-foreground font-medium text-xs mb-1">api (FastAPI)</p>
                  <p class="text-xs">Puerto 8000. Hot-reload con uvicorn. Codigo montado por volumen.</p>
                </div>
                <div class="p-3 rounded-md border bg-card">
                  <p class="text-foreground font-medium text-xs mb-1">lab (Jupyter Lab)</p>
                  <p class="text-xs">Puerto 8888. Notebooks montados por volumen en <code>lab/notebooks/</code>.</p>
                </div>
                <div class="p-3 rounded-md border bg-card">
                  <p class="text-foreground font-medium text-xs mb-1">frontend (Vite + Nginx)</p>
                  <p class="text-xs">Puerto 8080. Reverse proxy a API y Lab. Codigo montado por volumen.</p>
                </div>
              </div>

              <div class="p-4 rounded-md border bg-card font-mono text-xs space-y-1">
                <p class="text-foreground">cp .env.example .env &nbsp;&nbsp;# completar credenciales</p>
                <p class="text-foreground">docker compose up --build</p>
              </div>

              <p>
                Los scripts SQL de <code>db/init/</code> solo se ejecutan cuando el volumen de datos esta vacio.
                Si se modifica el esquema, recrear con <code>docker compose down -v</code> antes de levantar.
                Las variables de entorno se configuran en <code>.env</code> (ver <code>.env.example</code>).
              </p>
            </div>
          </AccordionContent>
        </AccordionItem>

      </Accordion>
    </div>
  </section>
</template>

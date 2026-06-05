<script setup lang="ts">
import { ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import MermaidDiagram from '@/components/MermaidDiagram.vue'
import { API_BASE } from '@/config'

const activeTab = ref('api')

const isLocal = window.location.hostname === 'localhost'
const docsUrl = isLocal ? `${API_BASE}/docs` : '/swagger-ui'

const derBronze = `erDiagram
    ingestion_logs {
        BIGSERIAL id PK
        TEXT file_name
        TEXT file_path
        INTEGER row_count
        TEXT status
        TEXT error_message
        NUMERIC elapsed_s
        TIMESTAMPTZ ingested_at
    }

    prediction_logs {
        BIGSERIAL id PK
        BIGINT request_id FK
        TEXT type
        JSONB input
        JSONB output
        NUMERIC confidence
        NUMERIC elapsed_s
        JSONB user_decision
        TIMESTAMPTZ logged_at
    }

    duplicate_logs {
        BIGSERIAL id PK
        UUID conversation_id FK
        BIGINT request_id FK
        TEXT action
        TEXT short_text
        TEXT selected_material_id
        JSONB duplicates
        NUMERIC elapsed_s
        TIMESTAMPTZ logged_at
    }

    llm_logs {
        BIGSERIAL id PK
        UUID conversation_id FK
        TEXT model
        TEXT system_prompt
        TEXT user_message
        INTEGER history_len
        TEXT response_raw
        JSONB response_parsed
        TEXT action
        INTEGER tokens_in
        INTEGER tokens_out
        NUMERIC elapsed_s
        TEXT error
        TIMESTAMPTZ logged_at
    }

    app_errors {
        BIGSERIAL id PK
        TEXT source
        TEXT message
        JSONB details
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
        TIMESTAMPTZ llm_completed_at
        TIMESTAMPTZ duplicates_completed_at
        TIMESTAMPTZ duplicates_decided_at
        TIMESTAMPTZ predict_completed_at
        TIMESTAMPTZ confirmed_at
        TIMESTAMPTZ discarded_at
        TIMESTAMPTZ exported_at
        NUMERIC llm_elapsed_s
        NUMERIC duplicates_elapsed_s
        NUMERIC predict_elapsed_s
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
        NUMERIC avg_total_s
        NUMERIC avg_llm_s
        NUMERIC avg_duplicates_s
        NUMERIC avg_predict_s
        NUMERIC avg_user_review_s
        NUMERIC avg_dup_decision_s
        NUMERIC auto_rate
    }

    kpi_quality {
        TIMESTAMPTZ week
        BIGINT materials
        NUMERIC accuracy
        NUMERIC avg_confidence
        BIGINT duplicate_matches
        BIGINT corrections
    }

    kpi_savings {
        TIMESTAMPTZ week
        BIGINT materials
        NUMERIC avg_processing_s
        NUMERIC hours_saved
        NUMERIC savings_q
    }

    kpi_step_breakdown {
        TIMESTAMPTZ week
        BIGINT total_requests
        NUMERIC avg_llm_s
        NUMERIC avg_dup_search_s
        NUMERIC avg_predict_s
        NUMERIC avg_machine_total_s
        NUMERIC avg_dup_decision_s
        NUMERIC avg_user_review_s
        NUMERIC avg_wall_time_s
        BIGINT confirmed
        BIGINT discarded
        BIGINT existing_matches
    }

    kpi_duplicates {
        TIMESTAMPTZ week
        BIGINT total_decisions
        BIGINT accepted
        BIGINT rejected
        NUMERIC avg_search_s
    }

    materials_by_type {
        TEXT material_type_code
        TEXT type_description
        BIGINT total_materials
    }
`
</script>

<template>
  <section class="max-w-6xl mx-auto px-6 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold tracking-tight">Referencia</h1>
      <p class="text-sm text-muted-foreground mt-1">Documentacion tecnica del proyecto: API interactiva, esquema de datos, decisiones de diseno y modelo de clasificacion.</p>
    </div>

    <Tabs v-model="activeTab">
      <TabsList class="mb-6 flex-wrap h-auto gap-1">
        <TabsTrigger value="api" class="gap-2">
          <i class="fa-solid fa-plug text-xs"></i>
          API
        </TabsTrigger>
        <TabsTrigger value="esquema" class="gap-2">
          <i class="fa-solid fa-database text-xs"></i>
          Esquema
        </TabsTrigger>
        <TabsTrigger value="decisiones" class="gap-2">
          <i class="fa-solid fa-scale-balanced text-xs"></i>
          Decisiones
        </TabsTrigger>
        <TabsTrigger value="modelo" class="gap-2">
          <i class="fa-solid fa-brain text-xs"></i>
          Modelo
        </TabsTrigger>
        <TabsTrigger value="despliegue" class="gap-2">
          <i class="fa-solid fa-rocket text-xs"></i>
          Despliegue
        </TabsTrigger>
      </TabsList>

      <!-- API (Swagger) -->
      <TabsContent value="api">
        <div class="rounded-lg border overflow-hidden" style="height: calc(100vh - 16rem)">
          <iframe
            :src="docsUrl"
            class="w-full h-full border-0"
            title="Swagger UI"
          />
        </div>
      </TabsContent>

      <!-- Esquema de datos -->
      <TabsContent value="esquema">
        <div class="max-w-4xl space-y-6 text-sm text-muted-foreground">
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
              Bronze registra toda la actividad del sistema en cinco tablas especializadas. No almacena datos crudos — los
              archivos XLSX de SAP se conservan en disco y se reprocesan si es necesario.
            </p>
            <p class="mb-2">
              <strong class="text-foreground">ingestion_logs:</strong> cada importacion de archivos SAP queda registrada con nombre,
              ruta, filas procesadas, estado y tiempo de ejecucion. Permite trazabilidad completa sin duplicar datos.
            </p>
            <p class="mb-2">
              <strong class="text-foreground">prediction_logs:</strong> cada ejecucion de los servicios de duplicados, descripcion o
              categorizacion registra entrada, salida, confianza, tiempo y decision del usuario. Alimenta los KPIs de gold.
            </p>
            <p class="mb-2">
              <strong class="text-foreground">duplicate_logs:</strong> cada decision de aceptar o rechazar un duplicado se registra
              con el material seleccionado, los candidatos presentados y el tiempo de busqueda. Permite analizar la tasa de
              reutilizacion real del maestro.
            </p>
            <p class="mb-2">
              <strong class="text-foreground">llm_logs:</strong> cada interaccion con Gemini registra el prompt del sistema, mensaje
              del usuario, respuesta parseada, tokens consumidos, tiempo de respuesta y errores. Permite monitorear costos y
              detectar degradacion del servicio.
            </p>
            <p class="mb-4">
              <strong class="text-foreground">app_errors:</strong> errores capturados tanto en frontend como en backend se centralizan
              aqui con source, mensaje y detalles estructurados. Reemplaza los silent catches por trazabilidad explicita.
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
              solicitud. El maestro de materiales se almacena limpio y con un indice de similitud difusa (<code>gin_trgm_ops</code>)
              que permite buscar duplicados de forma eficiente.
            </p>
            <p class="mb-2">
              Las solicitudes (<code>requests</code>) gestionan el ciclo completo de alta de material, desde la propuesta inicial
              hasta la exportacion. Cada solicitud registra <strong class="text-foreground">timestamps por cada paso del pipeline</strong>
              (LLM, duplicados, prediccion, decision del usuario, confirmacion) y duraciones computadas por paso. Esto permite
              desglosar el tiempo de procesamiento en tiempo maquina vs tiempo de decision humana — datos que alimentan directamente
              las vistas de gold para monetizacion.
            </p>
            <p class="mb-2">
              Las conversaciones (<code>conversations</code>) almacenan el historial del chat con titulo dinamico que se actualiza
              segun el contexto: nombre del producto confirmado, material existente seleccionado, o propuesta del LLM.
            </p>
            <p class="mb-4">
              Los datasets de entrenamiento y prueba para el modelo de categorizacion se derivan del maestro normalizado,
              permitiendo que Jupyter acceda a datos listos para experimentacion sin procesamiento adicional.
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
              Gold contiene <strong class="text-foreground">exclusivamente vistas</strong> y una tabla de parametros de configuracion.
              No se escriben datos directamente — las vistas leen de silver y bronze al momento de ser consultadas, garantizando
              que los indicadores siempre reflejen el estado actual sin procesos de sincronizacion.
            </p>
            <p class="mb-2">
              Los KPIs cubren cinco dimensiones: <strong class="text-foreground">tiempos de procesamiento</strong> desglosados por
              paso (LLM, duplicados, prediccion, revision humana), <strong class="text-foreground">calidad del modelo</strong>
              (accuracy, confianza, correcciones), <strong class="text-foreground">monetizacion</strong> (horas-hombre ahorradas y
              su equivalente en quetzales), <strong class="text-foreground">duplicados</strong> (tasa de aceptacion vs rechazo) y
              <strong class="text-foreground">desglose por paso</strong> (tiempo maquina vs tiempo usuario, wall time total,
              outcomes por estado). Power BI se conecta directamente a este esquema.
            </p>
            <p class="mb-4">
              Los parametros configurables (<code>manual_time_s</code> y <code>hourly_rate</code>) definen la linea base del proceso
              manual y la tarifa horaria para calcular el ahorro monetario.
            </p>
            <MermaidDiagram :chart="derGold" />
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-2">Justificacion de la arquitectura</h4>
            <ul class="space-y-2 list-disc list-inside">
              <li>
                <strong>Tres capas sin staging:</strong> el esquema staging original era redundante con silver. El API
                escribe directamente en silver, eliminando la necesidad de promover datos entre esquemas.
              </li>
              <li>
                <strong>Bronze como capa de logs:</strong> cinco tablas especializadas (ingestion, prediction, duplicates,
                LLM, errors) en vez de una generica. Cada tabla tiene su estructura optimizada para el tipo de evento.
              </li>
              <li>
                <strong>Gold como vistas puras:</strong> al no materializar datos en gold, se evita la duplicacion y
                desincronizacion. Los KPIs se calculan en tiempo real sobre silver y bronze.
              </li>
              <li>
                <strong>Todo en una sola instancia de PostgreSQL:</strong> la comunicacion entre esquemas no tiene costo
                adicional. Un JOIN entre silver y bronze es identico a un JOIN dentro del mismo esquema. La separacion
                es puramente organizacional.
              </li>
            </ul>
          </div>
        </div>
      </TabsContent>

      <!-- Decisiones de diseno -->
      <TabsContent value="decisiones">
        <div class="max-w-4xl space-y-4 text-sm text-muted-foreground">

          <div>
            <h4 class="text-foreground font-medium mb-1">Pipeline de 3 pasos: LLM, Duplicados, ML</h4>
            <p>
              Cada solicitud de alta de material pasa por un pipeline secuencial de tres pasos.
              Primero, <strong class="text-foreground">Gemini</strong> (<code>gemini-2.0-flash</code>) normaliza la descripcion
              del usuario en campos estructurados (short_text, long_text, tipo de material, especificaciones). Segundo, se ejecuta
              un <strong class="text-foreground">fuzzy search</strong> con <code>pg_trgm</code> contra el maestro existente para
              detectar duplicados — si el usuario acepta uno, el flujo termina sin crear material nuevo. Tercero, si no hay
              duplicado, el <strong class="text-foreground">modelo LinearSVC</strong> predice la clase de material con alternativas
              ranked por confianza. El usuario confirma o corrige cada propuesta antes de que se persista.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-1">Interfaz conversacional con chat</h4>
            <p>
              El flujo de alta de material se implementa como un chat interactivo, no como un formulario. El usuario describe
              el material en lenguaje natural y el sistema responde con propuestas estructuradas. Esto reduce la friccion — no
              hay campos obligatorios que llenar ni taxonomias que navegar. Las conversaciones se persisten con historial completo,
              titulo dinamico (se renombra segun el producto confirmado, duplicado seleccionado o propuesta del LLM) y pueden
              retomarse en cualquier momento. La entrada de texto se deshabilita durante la revision de duplicados para forzar
              la interaccion por botones.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-1">Confirmacion humana obligatoria</h4>
            <p>
              Ninguna propuesta del sistema se persiste sin revision del usuario. No es solo una medida de seguridad — es
              el mecanismo que genera los datos de correccion que alimentan los KPIs de calidad. Cuando el usuario corrige
              una categoria, el campo <code>corrected</code> se marca como <code>true</code> y la correccion se refleja en
              las metricas de accuracy semanales. Esto permite medir si el modelo mejora con el tiempo y cuanto trabajo
              adicional genera la revision humana.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-1">Modelo integrado en la API</h4>
            <p>
              El modelo de categorizacion (<code>LinearSVC + TF-IDF</code>) vive dentro del API como un endpoint, no como
              un servicio separado. El artefacto (<code>.joblib</code>) se carga en memoria al primer request y se reutiliza.
              Esto simplifica la orquestacion (un contenedor menos), el despliegue y la comunicacion. El endpoint
              <code>/api/model/predict</code> mantiene un contrato fijo: cambiar el modelo interno — o incluso la arquitectura
              completa — no requiere cambios en ningun otro componente.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-1">Timestamps por paso para monetizacion</h4>
            <p>
              Cada solicitud registra <strong class="text-foreground">7 timestamps</strong> a lo largo del pipeline:
              <code>created_at</code>, <code>llm_completed_at</code>, <code>duplicates_completed_at</code>,
              <code>duplicates_decided_at</code>, <code>predict_completed_at</code>, <code>confirmed_at</code> y
              <code>exported_at</code>. Ademas, las duraciones de cada paso maquina se almacenan explicitamente
              (<code>llm_elapsed_s</code>, <code>duplicates_elapsed_s</code>, <code>predict_elapsed_s</code>).
              Al confirmar, <code>processing_time_s</code> se computa automaticamente como la suma de los tiempos maquina.
              Gold usa estos campos para desglosar el wall time en tiempo maquina vs tiempo de decision humana, lo que
              permite calcular el ahorro real comparado contra el proceso manual parametrizado.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-1">Logging centralizado sin silent catches</h4>
            <p>
              Todos los errores — tanto del backend como del frontend — se registran en <code>bronze.app_errors</code>
              con source, mensaje y detalles estructurados. Las interacciones con el LLM se logean completamente en
              <code>bronze.llm_logs</code> (prompt, respuesta, tokens, tiempo, errores). Las decisiones de duplicados
              van a <code>bronze.duplicate_logs</code>. Esto reemplaza los <code>catch {}</code> silenciosos por
              trazabilidad explicita y permite diagnosticar problemas sin acceso al servidor.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-1">Autenticacion JWT con activacion manual</h4>
            <p>
              Los usuarios se registran pero quedan inactivos hasta que un administrador los activa. La autenticacion
              usa JWT con <code>bcrypt</code> para hashing de passwords. Todas las rutas protegidas (chat, ETL, export,
              logs) requieren token valido. El frontend persiste la sesion en localStorage y adjunta el token
              automaticamente via <code>authFetch</code>. Las rutas publicas (presentacion, arquitectura) no requieren
              autenticacion.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-1">Importacion incremental desde Excel</h4>
            <p>
              Los archivos XLSX de SAP se importan con logica incremental (<code>ON CONFLICT DO UPDATE</code>) — solo se
              agregan o actualizan registros. El sistema auto-crea registros de referencia faltantes (tipos de material,
              UNSPSC, unidades de medida) a partir de valores compuestos en los archivos (<code>"ZCON - Materiales"</code>
              se parsea automaticamente). Soporta tres tipos de carga: materiales, clases/denominaciones y codigos UNSPSC.
              Cada ingesta queda registrada en <code>bronze.ingestion_logs</code> con tiempo de ejecucion.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-1">Exportacion XLSX con formato SAP</h4>
            <p>
              SAP no expone una API de escritura accesible para este flujo. La solucion es generar archivos <code>.xlsx</code>
              formateados con <code>openpyxl</code> para el proceso de carga masiva existente. El usuario puede filtrar
              por estado, excluir solicitudes ya exportadas y seleccionar registros especificos. El archivo incluye
              headers estilizados, columnas de tiempos por paso y se marca automaticamente como exportado para evitar
              duplicacion. Esto se integra sin friccion con el flujo actual del equipo.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-1">Deteccion de duplicados con pg_trgm</h4>
            <p>
              La busqueda de duplicados usa la extension <code>pg_trgm</code> de PostgreSQL con un indice GIN sobre
              <code>short_text</code>. Esto permite encontrar materiales similares sin requerir coincidencias exactas
              — es tolerante a typos, abreviaciones y variaciones de formato comunes en textos SAP. Los resultados
              se presentan al usuario como tarjetas clickeables: aceptar un duplicado termina el flujo (status
              <code>existing_match</code>), rechazar todos continua al paso de categorizacion ML.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-1">Monetizacion por ahorro de horas-hombre</h4>
            <p>
              El sistema compara el <code>processing_time_s</code> de cada solicitud contra la linea base del proceso
              manual (parametro <code>manual_time_s</code> en <code>gold.parameters</code>). La diferencia se convierte
              a horas y se multiplica por la tarifa horaria (<code>hourly_rate</code>) para calcular el ahorro en
              quetzales. Las vistas de gold agregan esto por semana, permitiendo generar reportes de ROI en Power BI.
              El desglose por paso (LLM, duplicados, prediccion, revision humana) permite identificar cuellos de
              botella y optimizar el flujo.
            </p>
          </div>
        </div>
      </TabsContent>

      <!-- Modelo de clasificacion -->
      <TabsContent value="modelo">
        <div class="max-w-4xl space-y-6 text-sm text-muted-foreground">
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
      </TabsContent>

      <!-- Despliegue -->
      <TabsContent value="despliegue">
        <div class="max-w-4xl space-y-4 text-sm text-muted-foreground">
          <p>
            Todo el proyecto se orquesta con <strong class="text-foreground">Docker Compose</strong>. Seis servicios
            en una red interna, con un reverse proxy Nginx que unifica el acceso.
          </p>

          <div class="grid grid-cols-2 lg:grid-cols-3 gap-3">
            <div class="p-3 rounded-md border bg-card">
              <p class="text-foreground font-medium text-xs mb-1">db (PostgreSQL 16)</p>
              <p class="text-xs">Puerto 5436. Esquemas bronze, silver y gold. Extension <code>pg_trgm</code> para fuzzy search. Scripts de inicializacion en <code>db/init/</code>.</p>
            </div>
            <div class="p-3 rounded-md border bg-card">
              <p class="text-foreground font-medium text-xs mb-1">api (FastAPI + Python 3.12)</p>
              <p class="text-xs">Puerto 8001. Uvicorn con hot-reload. Incluye modelo ML (<code>.joblib</code>), Gemini SDK, openpyxl y pandas. 8 routers: auth, chat, etl, duplicates, model, logs, export.</p>
            </div>
            <div class="p-3 rounded-md border bg-card">
              <p class="text-foreground font-medium text-xs mb-1">lab (Jupyter Lab)</p>
              <p class="text-xs">Puerto 8888. Imagen <code>scipy-notebook</code>. Notebooks y datos montados por volumen en <code>lab/</code>.</p>
            </div>
            <div class="p-3 rounded-md border bg-card">
              <p class="text-foreground font-medium text-xs mb-1">frontend (Vue 3 + Nginx)</p>
              <p class="text-xs">Puerto 8089. Dual-mode: desarrollo (Vite dev server) o produccion (build + Nginx). Controlado por <code>FRONTEND_MODE</code>.</p>
            </div>
            <div class="p-3 rounded-md border bg-card">
              <p class="text-foreground font-medium text-xs mb-1">planka (Kanban)</p>
              <p class="text-xs">Puerto 3000. Tablero de gestion de proyecto. Base de datos propia independiente (<code>planka-db</code>).</p>
            </div>
            <div class="p-3 rounded-md border bg-card">
              <p class="text-foreground font-medium text-xs mb-1">planka-db (PostgreSQL 16)</p>
              <p class="text-xs">Instancia exclusiva para Planka. Aislada del esquema medallon de GAMMA.</p>
            </div>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-2">Reverse proxy (Nginx)</h4>
            <p class="mb-3">
              El frontend en produccion sirve la SPA desde Nginx, que ademas actua como reverse proxy para unificar
              todos los servicios bajo un solo dominio:
            </p>
            <div class="space-y-1.5">
              <div class="flex items-center gap-3 p-2 rounded border bg-card font-mono text-xs">
                <Badge variant="outline" class="text-[10px] shrink-0 w-24 justify-center">/*</Badge>
                <span>SPA (Vue 3) con fallback a <code>index.html</code></span>
              </div>
              <div class="flex items-center gap-3 p-2 rounded border bg-card font-mono text-xs">
                <Badge variant="outline" class="text-[10px] shrink-0 w-24 justify-center">/api/*</Badge>
                <span>Proxy a FastAPI (<code>api:8000</code>)</span>
              </div>
              <div class="flex items-center gap-3 p-2 rounded border bg-card font-mono text-xs">
                <Badge variant="outline" class="text-[10px] shrink-0 w-24 justify-center">/swagger-ui</Badge>
                <span>Proxy a Swagger docs (<code>api:8000/docs</code>)</span>
              </div>
              <div class="flex items-center gap-3 p-2 rounded border bg-card font-mono text-xs">
                <Badge variant="outline" class="text-[10px] shrink-0 w-24 justify-center">/lab/*</Badge>
                <span>Proxy a Jupyter Lab (<code>lab:8888</code>) con WebSocket upgrade</span>
              </div>
            </div>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-2">Frontend dual-mode</h4>
            <p>
              El Dockerfile del frontend usa un <strong class="text-foreground">multi-stage build</strong> controlado por
              el argumento <code>FRONTEND_MODE</code>. En <code>development</code>, ejecuta el dev server de Vite con
              hot-reload (puerto 80 dentro del contenedor). En <code>production</code>, compila la SPA con
              <code>npm run build</code> y sirve los archivos estaticos desde Nginx. Los volumenes montan el codigo
              fuente para que los cambios se reflejen en tiempo real durante desarrollo.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-2">Inicio rapido</h4>
            <div class="p-4 rounded-md border bg-card font-mono text-xs space-y-1">
              <p class="text-foreground">cp .env.example .env &nbsp;&nbsp;<span class="text-muted-foreground"># completar credenciales</span></p>
              <p class="text-foreground">docker compose up --build</p>
            </div>
            <p class="mt-3">
              Los scripts SQL de <code>db/init/</code> solo se ejecutan cuando el volumen de datos esta vacio.
              Si se modifica el esquema, recrear con <code>docker compose down -v</code> antes de levantar.
            </p>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-2">Variables de entorno</h4>
            <div class="space-y-1.5">
              <div class="flex items-center gap-3 p-2 rounded border bg-card text-xs">
                <code class="text-foreground font-mono shrink-0 w-48">DB_USER, DB_PASSWORD, DB_NAME</code>
                <span>Credenciales de la base de datos principal</span>
              </div>
              <div class="flex items-center gap-3 p-2 rounded border bg-card text-xs">
                <code class="text-foreground font-mono shrink-0 w-48">JWT_SECRET</code>
                <span>Clave secreta para firmar tokens JWT</span>
              </div>
              <div class="flex items-center gap-3 p-2 rounded border bg-card text-xs">
                <code class="text-foreground font-mono shrink-0 w-48">GEMINI_API_KEY</code>
                <span>API key de Google Gemini para el LLM</span>
              </div>
              <div class="flex items-center gap-3 p-2 rounded border bg-card text-xs">
                <code class="text-foreground font-mono shrink-0 w-48">JUPYTER_TOKEN</code>
                <span>Token de acceso a Jupyter Lab</span>
              </div>
              <div class="flex items-center gap-3 p-2 rounded border bg-card text-xs">
                <code class="text-foreground font-mono shrink-0 w-48">FRONTEND_MODE</code>
                <span><code>development</code> o <code>production</code> (default: development)</span>
              </div>
              <div class="flex items-center gap-3 p-2 rounded border bg-card text-xs">
                <code class="text-foreground font-mono shrink-0 w-48">PLANKA_SECRET, PLANKA_URL</code>
                <span>Configuracion del tablero Kanban</span>
              </div>
            </div>
          </div>

          <Separator />

          <div>
            <h4 class="text-foreground font-medium mb-2">Stack tecnologico</h4>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <p class="text-foreground font-medium text-xs mb-2">Frontend</p>
                <ul class="text-xs space-y-1 list-disc list-inside">
                  <li>Vue 3 + TypeScript</li>
                  <li>Vite 6 (Node 20)</li>
                  <li>Tailwind CSS 4</li>
                  <li>shadcn-vue (card, badge, tabs, accordion, etc.)</li>
                  <li>Vue Router con guards de autenticacion</li>
                </ul>
              </div>
              <div>
                <p class="text-foreground font-medium text-xs mb-2">Backend</p>
                <ul class="text-xs space-y-1 list-disc list-inside">
                  <li>FastAPI + Pydantic v2</li>
                  <li>SQLAlchemy 2.0 + psycopg2</li>
                  <li>Google Gemini (<code>gemini-2.0-flash</code>)</li>
                  <li>scikit-learn (LinearSVC + TF-IDF)</li>
                  <li>pandas + openpyxl</li>
                  <li>PyJWT + bcrypt</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </TabsContent>
    </Tabs>
  </section>
</template>

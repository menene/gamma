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

    kpi_requests_by_user {
        TIMESTAMPTZ week
        BIGINT user_id
        TEXT user_email
        TEXT user_name
        BIGINT total_requests
        BIGINT confirmed
        BIGINT discarded
        BIGINT existing_matches
        BIGINT corrections
        NUMERIC avg_processing_s
    }

    requests_users {
        BIGINT request_id
        TIMESTAMPTZ created_at
        TIMESTAMPTZ confirmed_at
        TIMESTAMPTZ discarded_at
        TIMESTAMPTZ exported_at
        TEXT status
        BIGINT material_type_id
        TEXT material_type_code
        TEXT material_type_description
        TEXT material_name
        TEXT short_text
        TEXT long_text
        TEXT class_code
        NUMERIC confidence
        BOOLEAN corrected
        BOOLEAN auto_resolved
        NUMERIC processing_time_s
        NUMERIC llm_elapsed_s
        NUMERIC duplicates_elapsed_s
        NUMERIC predict_elapsed_s
        BIGINT user_id
        TEXT user_email
        TEXT user_name
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
      <p class="text-sm text-muted-foreground mt-1">API interactiva y esquema de la base de datos.</p>
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
      </TabsList>

      <!-- API (Swagger) -->
      <TabsContent value="api">
        <div class="rounded-lg border overflow-hidden" style="height: calc(100vh - 16rem)">
          <iframe
            :src="docsUrl"
            class="w-full h-full border-0 bg-white"
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
            <p class="mb-2">
              Todas las vistas de solicitudes, materiales y usuarios <strong class="text-foreground">excluyen las cuentas admin</strong>
              (usadas para pruebas), de modo que los indicadores solo reflejan actividad real y no ruido de testing.
            </p>

            <h5 class="text-foreground font-medium mt-4 mb-2">Vistas disponibles</h5>
            <p class="mb-2">
              <strong class="text-foreground">kpi_processing_time:</strong> tiempos de procesamiento por semana sobre solicitudes
              confirmadas. Muestra cantidad de materiales, promedio de tiempo total y por paso (LLM, duplicados, prediccion), tiempo
              de revision del usuario, tiempo de decision de duplicados y la tasa de resolucion automatica.
            </p>
            <p class="mb-2">
              <strong class="text-foreground">kpi_quality:</strong> calidad del modelo por semana. Muestra accuracy (proporcion de
              clasificaciones no corregidas), confianza promedio, cantidad de coincidencias con material existente y cuantas
              clasificaciones corrigio el usuario.
            </p>
            <p class="mb-2">
              <strong class="text-foreground">kpi_savings:</strong> monetizacion por semana. Cruza el tiempo de procesamiento con los
              parametros configurables para mostrar horas-hombre ahorradas y su equivalente en quetzales frente al proceso manual.
            </p>
            <p class="mb-2">
              <strong class="text-foreground">kpi_step_breakdown:</strong> desglose fino por paso (por semana de creacion, todas las
              solicitudes). Separa tiempo maquina vs tiempo de decision humana, muestra el wall time total de punta a punta y los
              outcomes por estado (confirmadas, descartadas, coincidencias existentes).
            </p>
            <p class="mb-2">
              <strong class="text-foreground">kpi_duplicates:</strong> decisiones sobre duplicados por semana. Muestra total de
              decisiones, cuantos duplicados se aceptaron (se reuso un material existente y no se creo uno nuevo) vs cuantos se
              rechazaron (se siguio con el alta), y el tiempo promedio de busqueda.
            </p>
            <p class="mb-2">
              <strong class="text-foreground">kpi_requests_by_user:</strong> actividad semanal desglosada por usuario. Muestra el total
              de solicitudes y su conteo por estado (confirmadas, descartadas, coincidencias existentes), correcciones y tiempo de
              procesamiento promedio.
            </p>
            <p class="mb-2">
              <strong class="text-foreground">requests_users:</strong> vista de detalle, una fila por solicitud enriquecida con el
              tipo de material, la clase, las metricas de tiempo y el usuario que la creo. El tiempo de procesamiento se reconstruye
              de los pasos cuando no se calculo al confirmar, y se excluyen las solicitudes heredadas que no tienen ningun tiempo
              medido (no utilizables).
            </p>
            <p class="mb-4">
              <strong class="text-foreground">materials_by_type:</strong> resumen del maestro de materiales agrupado por tipo de
              material, ordenado de mayor a menor cantidad. Incluye los materiales importados por ETL y excluye los creados por
              cuentas admin.
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
    </Tabs>
  </section>
</template>


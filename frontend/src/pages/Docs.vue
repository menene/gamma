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
    materials {
        TEXT id PK
        BOOLEAN deletion_flag
        TEXT material_type_id FK
        TEXT article_group
        TEXT unit_of_measure
        TEXT manufacturer_info
        TEXT class_id FK
        TEXT short_text
        TIMESTAMPTZ updated_at
    }

    classes {
        TEXT id PK
        TEXT name
        TEXT article_group
        TEXT sector
        TEXT material_type_id FK
        TEXT unspsc_id FK
    }

    unspsc {
        TEXT id PK
        TEXT description
    }

    material_types {
        TEXT id PK
        TEXT description
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
        TEXT name
        TEXT long_text
        JSONB specifications
        TEXT short_text
        TEXT material_type_id FK
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
        TEXT material_type_id FK
        TEXT article_group
    }

    dataset_test {
        TEXT short_text
        TEXT material_type_id FK
        TEXT article_group
    }

    material_types ||--o{ materials : "material_type_id"
    material_types ||--o{ classes : "material_type_id"
    material_types ||--o{ requests : "material_type_id"
    material_types ||--o{ dataset_train : "material_type_id"
    material_types ||--o{ dataset_test : "material_type_id"
    classes ||--o{ materials : "class_id"
    unspsc ||--o{ classes : "unspsc_id"
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

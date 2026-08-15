<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import MermaidDiagram from '@/components/MermaidDiagram.vue'
import { API_BASE } from '@/config'
import { authFetch } from '@/composables/useAuth'

interface Comparacion { metric: string; anterior: number | null; nueva: number | null; delta: number | null }
interface Job {
  job_id: number
  status: string
  step: string | null
  started_at: string | null
  finished_at: string | null
  elapsed_s: number | null
  n_train: number | null
  n_test: number | null
  n_classes: number | null
  metrics: Record<string, number> | null
  comparison?: Comparacion[]
  error_message: string | null
}
interface Version {
  id: number | null
  version: string
  file_name: string
  is_active: boolean
  model_name: string | null
  n_classes: number | null
  n_samples: number | null
  accuracy: number | null
  f1_macro: number | null
  top3_accuracy: number | null
  size_bytes: number | null
  created_at: string | null
  notes: string | null
}

const activeTab = ref('operacion')

// Competencia de modelos, evaluada con particion agrupada por descripcion:
// ninguna descripcion del maestro cruza la frontera entre entrenamiento y
// prueba, de modo que las cifras corresponden al caso de uso de la plataforma
// —clasificar un material que aun no existe—. Medido con
// lab/scripts/eval_grouped_split.py. Ordenados por accuracy descendente.
const modelos = [
  { nombre: 'LinearSVC + CharTFIDF', accuracy: 0.8208, f1Macro: 0.7072, f1Weighted: 0.8041, precision: 0.8079, recall: 0.8208, top3: 0.9176, tiempo: 54.1, ganador: true },
  { nombre: 'RandomForest + WordTFIDF', accuracy: 0.8133, f1Macro: 0.7029, f1Weighted: 0.8014, precision: 0.8195, recall: 0.8133, top3: 0.9063, tiempo: 46.0 },
  { nombre: 'LogReg + WordTFIDF', accuracy: 0.8095, f1Macro: 0.6689, f1Weighted: 0.7949, precision: 0.8066, recall: 0.8095, top3: 0.9135, tiempo: 28.9 },
  { nombre: 'LogReg + CharTFIDF', accuracy: 0.8080, f1Macro: 0.6423, f1Weighted: 0.7886, precision: 0.7912, recall: 0.8080, top3: 0.9248, tiempo: 1071.9 },
  { nombre: 'fastText', accuracy: 0.7780, f1Macro: 0.6275, f1Weighted: 0.7648, precision: 0.7743, recall: 0.7771, top3: 0.8865, tiempo: 42.8 },
]

// Sin cifra bajo esta particion todavia. No se listan con la medicion anterior
// porque no seria comparable con las filas de arriba.
const pendientes = [
  { nombre: 'Transformer (MiniLM)', motivo: 'reevaluacion en curso' },
  { nombre: 'XGBoost + CharTFIDF', motivo: 'sin reevaluar' },
]

const series = [
  { key: 'accuracy' as const, label: 'Accuracy', color: 'var(--series-1)' },
  { key: 'f1Macro' as const, label: 'F1 macro', color: 'var(--series-2)' },
  { key: 'top3' as const, label: 'Top-3', color: 'var(--series-3)' },
]

const fmtTiempo = (s: number) => (s >= 1000 ? `${(s / 60).toFixed(0)} min` : `${s.toFixed(1)} s`)

const pipeline = `flowchart LR
    A["short_text<br/>(SAP, 40 caracteres)"] --> B["Normalizacion<br/>mayusculas, sin acentos,<br/>separadores a espacio"]
    B --> C["TF-IDF<br/>n-gramas de caracter 2-5<br/>50,000 dimensiones"]
    C --> D["LinearSVC<br/>one-vs-rest<br/>1,234 hiperplanos"]
    D --> E["Calibracion de Platt<br/>margen a probabilidad"]
    E --> F["Top-3 clases<br/>+ confianza"]
    F --> G{"Supera el<br/>umbral?"}
    G -->|Si| H["Sugerencia automatica"]
    G -->|No| I["Revision del gestor"]
    style A fill:#e8f0fb,stroke:#2a78d6,color:#0b0b0b
    style F fill:#e6f6f0,stroke:#1baf7a,color:#0b0b0b
    style H fill:#e6f6f0,stroke:#1baf7a,color:#0b0b0b
    style I fill:#fdeee7,stroke:#eb6834,color:#0b0b0b`

const versiones = ref<Version[]>([])
const jobs = ref<Job[]>([])
const jobActivo = ref<Job | null>(null)
const cargando = ref(false)
const error = ref<string | null>(null)
const aviso = ref<string | null>(null)
const confirmando = ref(false)
const rollbackObjetivo = ref<string | null>(null)

let timer: number | undefined

const enCurso = computed(() =>
  jobActivo.value !== null && ['pending', 'running'].includes(jobActivo.value.status)
)

function mb(bytes: number | null): string {
  if (!bytes) return '—'
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function fecha(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-GT', { dateStyle: 'short', timeStyle: 'short' })
}

function pct(v: number | null | undefined): string {
  return v === null || v === undefined ? '—' : `${(v * 100).toFixed(2)}%`
}

const etiquetaMetrica: Record<string, string> = {
  accuracy: 'Exactitud',
  f1_macro: 'F1 macro',
  f1_weighted: 'F1 ponderado',
  top3_accuracy: 'Top-3',
}

async function cargar() {
  error.value = null
  try {
    const [rv, rj] = await Promise.all([
      authFetch(`${API_BASE}/api/model/versions`),
      authFetch(`${API_BASE}/api/model/retrain?limit=10`),
    ])
    if (!rv.ok || !rj.ok) throw new Error('No se pudo consultar el estado del modelo')
    versiones.value = await rv.json()
    jobs.value = await rj.json()
    const vivo = jobs.value.find((j) => ['pending', 'running'].includes(j.status))
    if (vivo) {
      await detalle(vivo.job_id)
      arrancarSondeo()
    } else if (jobs.value.length && !jobActivo.value) {
      await detalle(jobs.value[0].job_id)
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error de conexion'
  }
}

async function detalle(id: number) {
  const r = await authFetch(`${API_BASE}/api/model/retrain/${id}`)
  if (r.ok) jobActivo.value = await r.json()
}

function arrancarSondeo() {
  detenerSondeo()
  timer = window.setInterval(async () => {
    if (!jobActivo.value) return detenerSondeo()
    await detalle(jobActivo.value.job_id)
    if (!['pending', 'running'].includes(jobActivo.value.status)) {
      detenerSondeo()
      await cargar()
    }
  }, 3000)
}

function detenerSondeo() {
  if (timer) { clearInterval(timer); timer = undefined }
}

async function reentrenar() {
  confirmando.value = false
  cargando.value = true
  error.value = null
  aviso.value = null
  try {
    const r = await authFetch(`${API_BASE}/api/model/retrain`, { method: 'POST' })
    const data = await r.json()
    if (!r.ok) throw new Error(data.detail || 'No se pudo iniciar el reentrenamiento')
    aviso.value = data.message
    await detalle(data.job_id)
    arrancarSondeo()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error de conexion'
  } finally {
    cargando.value = false
  }
}

async function revertir(version: string) {
  rollbackObjetivo.value = null
  cargando.value = true
  error.value = null
  aviso.value = null
  try {
    const r = await authFetch(`${API_BASE}/api/model/rollback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version }),
    })
    const data = await r.json()
    if (!r.ok) throw new Error(data.detail || 'No se pudo revertir')
    aviso.value = data.message
    await cargar()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error de conexion'
  } finally {
    cargando.value = false
  }
}

const colorEstado: Record<string, string> = {
  completed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  running: 'bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-200',
  pending: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
}

onMounted(cargar)
onUnmounted(detenerSondeo)
</script>

<template>
  <section class="max-w-6xl mx-auto px-6 py-8">
    <div class="mb-8">
      <h1 class="text-2xl font-bold tracking-tight">Modelo</h1>
      <p class="text-sm text-muted-foreground mt-1">
        Operacion, arquitectura y evaluacion del clasificador de categoria
      </p>
    </div>

    <div v-if="error" class="mb-6 rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm">
      <i class="fa-solid fa-triangle-exclamation mr-2"></i>{{ error }}
    </div>
    <div v-if="aviso" class="mb-6 rounded-md border px-4 py-3 text-sm text-muted-foreground">
      <i class="fa-solid fa-circle-info mr-2"></i>{{ aviso }}
    </div>

    <Tabs v-model="activeTab">
      <TabsList class="mb-6 flex-wrap h-auto gap-1">
        <TabsTrigger value="operacion" class="gap-2">
          <i class="fa-solid fa-arrows-rotate text-xs"></i>
          Operacion
        </TabsTrigger>
        <TabsTrigger value="arquitectura" class="gap-2">
          <i class="fa-solid fa-diagram-project text-xs"></i>
          Como funciona
        </TabsTrigger>
        <TabsTrigger value="evaluacion" class="gap-2">
          <i class="fa-solid fa-chart-simple text-xs"></i>
          Evaluacion
        </TabsTrigger>
      </TabsList>

      <TabsContent value="operacion">
    <!-- Reentrenamiento -->
    <Card class="mb-8">
      <CardHeader class="pb-3">
        <CardTitle class="text-base flex items-center gap-2">
          <i class="fa-solid fa-arrows-rotate text-sm text-muted-foreground"></i>
          Reentrenamiento del modelo
        </CardTitle>
        <CardDescription>
          Reconstruye el clasificador con el maestro de materiales vigente y las correcciones
          registradas por los gestores. El artefacto actual se archiva con marca de tiempo antes
          de publicar el nuevo, de modo que siempre se puede revertir.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div class="rounded-md border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm mb-4">
          <p class="font-medium mb-1">
            <i class="fa-solid fa-triangle-exclamation mr-2"></i>Proceso de uso excepcional
          </p>
          <p class="text-muted-foreground text-xs">
            Ejecutelo unicamente despues de una carga importante al maestro. Toma varios minutos,
            mantiene en memoria el modelo actual y el nuevo a la vez, y el servicio de prediccion
            puede responder mas lento mientras dura.
          </p>
        </div>

        <div v-if="!confirmando" class="flex items-center gap-3">
          <Button :disabled="cargando || enCurso" class="gap-2" @click="confirmando = true">
            <i class="fa-solid fa-play text-xs"></i>
            {{ enCurso ? 'Reentrenamiento en curso' : 'Iniciar reentrenamiento' }}
          </Button>
          <Button variant="outline" class="gap-2" :disabled="cargando" @click="cargar">
            <i class="fa-solid fa-rotate text-xs"></i>
            Actualizar
          </Button>
        </div>
        <div v-else class="rounded-md border p-4">
          <p class="text-sm font-medium mb-1">¿Confirma que desea reentrenar el modelo?</p>
          <p class="text-xs text-muted-foreground mb-3">
            El modelo en produccion se reemplazara al terminar. Podra revertirlo desde el historial
            de versiones.
          </p>
          <div class="flex gap-2">
            <Button size="sm" :disabled="cargando" @click="reentrenar">Si, reentrenar</Button>
            <Button size="sm" variant="outline" @click="confirmando = false">Cancelar</Button>
          </div>
        </div>

        <!-- Estado de la ejecucion -->
        <template v-if="jobActivo">
          <Separator class="my-5" />
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm font-medium">
              Ejecucion #{{ jobActivo.job_id }}
              <span
                class="ml-2 px-2 py-0.5 rounded text-xs font-medium"
                :class="colorEstado[jobActivo.status] || 'bg-muted'"
              >{{ jobActivo.status }}</span>
            </p>
            <span class="text-xs text-muted-foreground">
              {{ fecha(jobActivo.started_at) }}
              <template v-if="jobActivo.elapsed_s"> · {{ jobActivo.elapsed_s.toFixed(1) }}s</template>
            </span>
          </div>

          <p v-if="enCurso" class="text-sm text-muted-foreground mb-3">
            <i class="fa-solid fa-spinner fa-spin mr-2"></i>{{ jobActivo.step || 'procesando' }}
          </p>

          <div v-if="jobActivo.error_message"
               class="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs font-mono">
            {{ jobActivo.error_message }}
          </div>

          <div v-if="jobActivo.comparison?.length && jobActivo.status === 'completed'">
            <p class="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Comparacion con el modelo anterior
            </p>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-xs text-muted-foreground border-b">
                    <th class="text-left font-medium py-1.5">Metrica</th>
                    <th class="text-right font-medium py-1.5">Anterior</th>
                    <th class="text-right font-medium py-1.5">Nueva</th>
                    <th class="text-right font-medium py-1.5">Diferencia</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="c in jobActivo.comparison" :key="c.metric" class="border-b last:border-0">
                    <td class="py-1.5">{{ etiquetaMetrica[c.metric] || c.metric }}</td>
                    <td class="text-right tabular-nums text-muted-foreground">{{ pct(c.anterior) }}</td>
                    <td class="text-right tabular-nums font-medium">{{ pct(c.nueva) }}</td>
                    <td
                      class="text-right tabular-nums"
                      :class="c.delta === null ? 'text-muted-foreground'
                        : c.delta >= 0 ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-red-600 dark:text-red-400'"
                    >
                      <template v-if="c.delta !== null">
                        {{ c.delta >= 0 ? '+' : '' }}{{ (c.delta * 100).toFixed(2) }} pp
                      </template>
                      <template v-else>—</template>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="text-xs text-muted-foreground mt-2">
              Si alguna metrica empeoro de forma relevante, revierta a la version anterior desde el
              historial.
            </p>
          </div>
        </template>
      </CardContent>
    </Card>

    <!-- Versiones -->
    <div class="flex items-baseline justify-between mb-4">
      <h2 class="text-base font-semibold tracking-tight">Versiones del modelo</h2>
      <span class="text-xs text-muted-foreground">{{ versiones.length }} registradas</span>
    </div>
    <Card>
      <CardContent class="pt-5">
        <p v-if="!versiones.length" class="text-sm text-muted-foreground">
          No hay versiones registradas.
        </p>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-xs text-muted-foreground border-b">
                <th class="text-left font-medium py-2">Version</th>
                <th class="text-left font-medium py-2">Creada</th>
                <th class="text-right font-medium py-2">Clases</th>
                <th class="text-right font-medium py-2">Exactitud</th>
                <th class="text-right font-medium py-2">Top-3</th>
                <th class="text-right font-medium py-2">Tamano</th>
                <th class="text-right font-medium py-2"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="v in versiones" :key="v.version" class="border-b last:border-0">
                <td class="py-2">
                  <span class="font-mono text-xs">{{ v.version }}</span>
                  <Badge v-if="v.is_active" class="ml-2 text-xs">activa</Badge>
                </td>
                <td class="py-2 text-muted-foreground text-xs">{{ fecha(v.created_at) }}</td>
                <td class="py-2 text-right tabular-nums">{{ v.n_classes ?? '—' }}</td>
                <td class="py-2 text-right tabular-nums">{{ pct(v.accuracy) }}</td>
                <td class="py-2 text-right tabular-nums">{{ pct(v.top3_accuracy) }}</td>
                <td class="py-2 text-right tabular-nums text-muted-foreground text-xs">{{ mb(v.size_bytes) }}</td>
                <td class="py-2 text-right">
                  <template v-if="!v.is_active">
                    <Button
                      v-if="rollbackObjetivo !== v.version"
                      size="sm" variant="outline" class="text-xs h-7"
                      :disabled="cargando || enCurso"
                      @click="rollbackObjetivo = v.version"
                    >Revertir</Button>
                    <span v-else class="inline-flex gap-1">
                      <Button size="sm" class="text-xs h-7" :disabled="cargando"
                              @click="revertir(v.version)">Confirmar</Button>
                      <Button size="sm" variant="ghost" class="text-xs h-7"
                              @click="rollbackObjetivo = null">No</Button>
                    </span>
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
      </TabsContent>

      <TabsContent value="arquitectura">
        <div class="max-w-4xl space-y-6 text-sm text-muted-foreground">
        <div class="max-w-4xl space-y-6 text-sm text-muted-foreground">
          <p>
            El sistema predice la <strong class="text-foreground">clase de material</strong> (denominacion estandar)
            a partir del <code>short_text</code> de SAP. El modelo fue entrenado con <strong class="text-foreground">39,571 materiales</strong>
            distribuidos en <strong class="text-foreground">1,234 clases</strong>, extraidos de 13 archivos Excel de distintos
            tipos de material (ZCON, ZQUI, ZRPI, ZSUM, etc.).
          </p>

          <Separator />


          <div>
            <h4 class="text-foreground font-medium mb-3">Pipeline</h4>
            <MermaidDiagram :chart="pipeline" />
            <p class="mt-3">
              El modelo no impone una categoria: devuelve las tres mas probables con su confianza.
              Cuando la confianza supera el umbral configurado la sugerencia se acepta de forma automatica;
              cuando no, la solicitud pasa a revision del gestor. El umbral es el parametro que traduce
              tolerancia al error en cobertura de automatizacion.
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
                  <tr class="border-b"><td class="py-1.5 pr-3">0.50</td><td class="text-right px-2">92.94%</td><td class="text-right px-2">73.92%</td><td class="text-right pl-2">5,851</td></tr>
                  <tr class="border-b"><td class="py-1.5 pr-3">0.60</td><td class="text-right px-2">95.17%</td><td class="text-right px-2">65.08%</td><td class="text-right pl-2">5,151</td></tr>
                  <tr class="border-b"><td class="py-1.5 pr-3">0.70</td><td class="text-right px-2">96.78%</td><td class="text-right px-2">54.13%</td><td class="text-right pl-2">4,284</td></tr>
                  <tr><td class="py-1.5 pr-3">0.80</td><td class="text-right px-2">98.88%</td><td class="text-right px-2">28.24%</td><td class="text-right pl-2">2,235</td></tr>
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
        </div>
      </TabsContent>

      <TabsContent value="evaluacion">
        <div class="max-w-4xl space-y-6 text-sm text-muted-foreground">

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
                </div>
                <p class="mb-2">
                  Transformer pre-entrenado de Microsoft (<code>Multilingual-MiniLM-L12-H384</code>, 118M parametros, 12 capas,
                  384 dimensiones hidden) sometido a ajuste fino sobre los <code>short_text</code> normalizados, con
                  <code>batch_size=64</code> y 15 epochs. Es el unico candidato que modela el texto de forma contextual en
                  lugar de tratarlo como una bolsa de rasgos.
                </p>
                <p class="mb-2">
                  Queda por debajo de las configuraciones clasicas y con 50 veces el tiempo de entrenamiento del ganador
                  —ademas sobre GPU, mientras que el ganador se entrena en CPU—. La brecha mas grande esta en el F1 macro:
                  con 118M de parametros y una mediana de 9 materiales por clase, el modelo aprende las categorias pobladas
                  y se desploma en la cola larga, que es donde vive mas de la mitad de la taxonomia.
                  <span class="text-muted-foreground">Su cifra bajo esta particion esta en curso de medicion.</span>
                </p>
              </div>
            </div>
          </div>

          <Separator />


          <div>
            <h4 class="text-foreground font-medium mb-3">Comparacion de metricas</h4>

            <!-- Grafica: barras agrupadas, una fila por modelo -->
            <div class="viz-root rounded-md border bg-card p-4 mb-4">
              <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mb-4">
                <div v-for="s in series" :key="s.key" class="flex items-center gap-1.5">
                  <span class="w-2.5 h-2.5 rounded-[2px] shrink-0" :style="{ background: s.color }"></span>
                  <span class="text-xs text-foreground">{{ s.label }}</span>
                </div>
              </div>

              <div class="space-y-3">
                <div v-for="m in modelos" :key="m.nombre">
                  <div class="flex items-baseline gap-2 mb-1">
                    <span class="text-xs" :class="m.ganador ? 'text-foreground font-medium' : 'text-muted-foreground'">
                      {{ m.nombre }}
                    </span>
                    <span v-if="m.ganador" class="text-[10px] uppercase tracking-wide text-muted-foreground">ganador</span>
                  </div>
                  <div class="space-y-[2px]">
                    <div
                      v-for="s in series"
                      :key="s.key"
                      class="flex items-center gap-2"
                      :title="`${m.nombre} — ${s.label}: ${m[s.key].toFixed(4)}`"
                    >
                      <div class="viz-track relative h-3 flex-1 rounded-[2px]">
                        <div
                          class="absolute inset-y-0 left-0 rounded-r-[4px]"
                          :style="{ width: `${m[s.key] * 100}%`, background: s.color }"
                        ></div>
                      </div>
                      <span class="w-9 shrink-0 text-right text-[10px] tabular-nums text-muted-foreground">
                        {{ m[s.key].toFixed(3) }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Eje: alineado con la pista, no con la fila completa. -->
              <div class="flex items-center gap-2 mt-2 pt-2 border-t">
                <div class="flex-1 flex justify-between text-[10px] text-muted-foreground">
                  <span>0</span><span>0.25</span><span>0.50</span><span>0.75</span><span>1.0</span>
                </div>
                <span class="w-9 shrink-0"></span>
              </div>
            </div>

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
                  <tr
                    v-for="m in modelos"
                    :key="m.nombre"
                    class="border-b last:border-0"
                    :class="m.ganador ? 'bg-green-50 dark:bg-green-950 font-medium text-foreground' : ''"
                  >
                    <td class="py-2 pr-3">{{ m.nombre }}</td>
                    <td class="text-right py-2 px-2 tabular-nums">{{ m.accuracy.toFixed(4) }}</td>
                    <td class="text-right py-2 px-2 tabular-nums">{{ m.f1Macro.toFixed(4) }}</td>
                    <td class="text-right py-2 px-2 tabular-nums">{{ m.f1Weighted.toFixed(4) }}</td>
                    <td class="text-right py-2 px-2 tabular-nums">{{ m.precision.toFixed(4) }}</td>
                    <td class="text-right py-2 px-2 tabular-nums">{{ m.recall.toFixed(4) }}</td>
                    <td class="text-right py-2 px-2 tabular-nums">{{ m.top3.toFixed(4) }}</td>
                    <td class="text-right py-2 pl-2 tabular-nums">{{ fmtTiempo(m.tiempo) }}</td>
                  </tr>
                  <tr v-for="p in pendientes" :key="p.nombre" class="border-b last:border-0 text-muted-foreground">
                    <td class="py-2 pr-3">{{ p.nombre }}</td>
                    <td class="text-right py-2 px-2" colspan="7">{{ p.motivo }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>


          <Separator />


          <div>
            <h4 class="text-foreground font-medium mb-2">Por que LinearSVC + CharTFIDF</h4>
            <p class="mb-3">
              Los modelos se evaluaron sobre la misma particion, con la misma semilla y las mismas metricas.
              El mas simple resulto tambien el mejor.
            </p>
            <ul class="space-y-2 list-disc list-inside">
              <li>
                <strong class="text-foreground">Mejor en todas las metricas:</strong> accuracy (82.1%), F1 weighted (80.4%),
                F1 macro (70.7%) y Top-3 (91.8%) — superior en cada dimension frente al resto de configuraciones evaluadas.
              </li>
              <li>
                <strong class="text-foreground">F1 macro mayor:</strong> 0.7072 contra 0.6275-0.7029 del resto.
                Es la metrica que pesa igual a todas las clases, y por lo tanto la que mide el desempeno sobre la cola larga:
                mas de la mitad de las 1,234 clases tiene diez materiales o menos.
              </li>
              <li>
                <strong class="text-foreground">Top-3 del 92%:</strong> en el 92% de los casos la clase correcta esta entre
                las tres primeras. Es la metrica alineada con el uso real, donde el gestor confirma sobre una lista corta.
              </li>
              <li>
                <strong class="text-foreground">Costo de entrenamiento:</strong> 54 segundos en CPU, frente a las tres horas
                de XGBoost y los 52 minutos en GPU del transformer, ambos con resultados inferiores.
                En un sistema que se reentrena desde la propia aplicacion, esa diferencia define si el reentrenamiento es un
                boton o es infraestructura aparte.
              </li>
              <li>
                <strong class="text-foreground">Los n-gramas de caracter son el sesgo correcto:</strong> capturan subpalabras,
                toleran abreviaturas y errores de digitacion, y mantienen informativo un texto con tokens nunca vistos —
                requisito para clasificar materiales que aun no existen en el maestro. Los modelos que comprimen esa
                representacion a un espacio denso (fastText 100d, MiniLM 384d) pierden capacidad discriminativa.
              </li>
              <li>
                <strong class="text-foreground">La capacidad adicional no tiene datos con que estimarse:</strong> ni el
                gradient boosting, ni los embeddings de subpalabras, ni un transformer preentrenado con 118M de parametros
                superaron a un SVM lineal. Con una mediana de nueve materiales por clase, mas capacidad no compensa la
                escasez de datos: la amplifica.
              </li>
            </ul>
          </div>
        </div>
      </TabsContent>
    </Tabs>
  </section>
</template>

<style scoped>
/*
  Paleta categorica de la grafica de metricas. Tres series (blue, orange, aqua),
  validadas para deficiencia de vision cromatica en ambos modos. Se declaran como
  variables locales porque los tokens --chart-* del tema son escala de grises y no
  distinguen series.
*/
.viz-root {
  --series-1: #2a78d6;
  --series-2: #eb6834;
  --series-3: #1baf7a;
  --viz-grid: rgb(0 0 0 / 0.06);
}

/* Pista con lineas de referencia cada 25 %, recesivas frente a las barras. */
.viz-track {
  background:
    linear-gradient(to right, var(--viz-grid) 1px, transparent 1px) 25% 0 / 25% 100% repeat-x,
    rgb(0 0 0 / 0.04);
}

/*
  No hace falta una media query de `prefers-color-scheme`: useTheme.ts resuelve la
  preferencia del sistema y la escribe siempre como clase `dark` sobre <html>, de
  modo que esta clase es la unica fuente de verdad. Agregar la media query
  romperia el caso "sistema oscuro con tema claro elegido por el usuario".
*/
:root.dark .viz-root {
  --series-1: #3987e5;
  --series-2: #d95926;
  --series-3: #199e70;
  --viz-grid: rgb(255 255 255 / 0.10);
}

:root.dark .viz-track {
  background:
    linear-gradient(to right, var(--viz-grid) 1px, transparent 1px) 25% 0 / 25% 100% repeat-x,
    rgb(255 255 255 / 0.06);
}
</style>

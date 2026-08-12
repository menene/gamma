<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
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
        Reentrenamiento y versiones del clasificador de categoria
      </p>
    </div>

    <div v-if="error" class="mb-6 rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm">
      <i class="fa-solid fa-triangle-exclamation mr-2"></i>{{ error }}
    </div>
    <div v-if="aviso" class="mb-6 rounded-md border px-4 py-3 text-sm text-muted-foreground">
      <i class="fa-solid fa-circle-info mr-2"></i>{{ aviso }}
    </div>

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
  </section>
</template>

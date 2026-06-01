<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { API_BASE } from '@/config'
import { authFetch } from '@/composables/useAuth'

const API = `${API_BASE}/api/etl`

interface IngestionLog {
  id: number
  file_name: string
  file_path: string | null
  row_count: number
  status: string
  error_message: string | null
  ingested_at: string
}

interface QueueItem {
  id: number
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  row_count?: number
  elapsed_s?: number
  error?: string
}

interface TableCounts {
  'silver.materials': number
  'silver.classes': number
  'silver.unspsc': number
}

type SectionKey = 'materials' | 'classes' | 'unspsc'

const logs = ref<IngestionLog[]>([])
const counts = ref<TableCounts>({ 'silver.materials': 0, 'silver.classes': 0, 'silver.unspsc': 0 })

const queues = ref<Record<SectionKey, QueueItem[]>>({
  materials: [],
  classes: [],
  unspsc: [],
})
const processing = ref<Record<SectionKey, boolean>>({
  materials: false,
  classes: false,
  unspsc: false,
})

const fileInputs = ref<Record<SectionKey, HTMLInputElement | null>>({
  materials: null,
  classes: null,
  unspsc: null,
})

let nextQueueId = 0

async function fetchLogs() {
  try {
    const res = await authFetch(`${API}/logs`)
    if (res.ok) logs.value = await res.json()
  } catch { /* ignore */ }
}

async function fetchCounts() {
  try {
    const res = await authFetch(`${API}/counts`)
    if (res.ok) counts.value = await res.json()
  } catch { /* ignore */ }
}

async function processQueue(key: SectionKey) {
  if (processing.value[key]) return
  processing.value[key] = true

  while (true) {
    const item = queues.value[key].find(q => q.status === 'pending')
    if (!item) break

    item.status = 'uploading'
    const form = new FormData()
    form.append('file', item.file)

    try {
      const res = await authFetch(`${API}/upload/${key}`, { method: 'POST', body: form })
      if (res.ok) {
        const data = await res.json()
        item.status = 'success'
        item.row_count = data.row_count
        item.elapsed_s = data.elapsed_s
      } else {
        const err = await res.json().catch(() => ({ detail: 'Error desconocido' }))
        item.status = 'error'
        item.error = err.detail || 'Error'
      }
    } catch (e: any) {
      item.status = 'error'
      item.error = e.message
    }

    await fetchCounts()
  }

  await fetchLogs()
  processing.value[key] = false
}

function addFiles(key: SectionKey, event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) return

  for (const file of Array.from(files)) {
    queues.value[key].push({
      id: nextQueueId++,
      file,
      status: 'pending',
    })
  }

  input.value = ''
  processQueue(key)
}

function removeFromQueue(key: SectionKey, id: number) {
  const idx = queues.value[key].findIndex(q => q.id === id)
  if (idx !== -1 && queues.value[key][idx].status !== 'uploading') {
    queues.value[key].splice(idx, 1)
  }
}

function clearCompleted(key: SectionKey) {
  queues.value[key] = queues.value[key].filter(q => q.status === 'pending' || q.status === 'uploading')
}

function queueSummary(key: SectionKey) {
  const q = queues.value[key]
  const pending = q.filter(i => i.status === 'pending').length
  const uploading = q.filter(i => i.status === 'uploading').length
  const success = q.filter(i => i.status === 'success').length
  const error = q.filter(i => i.status === 'error').length
  return { pending, uploading, success, error, total: q.length }
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('es-GT', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

onMounted(() => {
  fetchLogs()
  fetchCounts()
})

const sections = [
  {
    key: 'materials' as const,
    title: 'Maestro de Materiales',
    icon: 'fa-solid fa-cubes',
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    description: 'Carga los archivos del maestro SAP exportados por tipo de material (ZCON, DIEN, ZEQU, etc.). Podes subir varios a la vez.',
    table: 'silver.materials' as const,
    columns: ['Material', 'Tipo material', 'Grupo de articulos', 'Unidad medida base', 'Info fabr./insp.', 'Denom.estandar', 'Texto breve de material'],
  },
  {
    key: 'classes' as const,
    title: 'Clases / Denominaciones',
    icon: 'fa-solid fa-tags',
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
    description: 'Catalogo de clases de material con denominaciones y grupos de articulos.',
    table: 'silver.classes' as const,
    columns: ['Codigo', 'Denominacion', 'Grupo de Articulos', 'Sector', 'Tipo de Material', 'UNSPSC'],
  },
  {
    key: 'unspsc' as const,
    title: 'UNSPSC (Naciones Unidas)',
    icon: 'fa-solid fa-globe',
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    description: 'Clasificador UNSPSC con segmentos, familias, clases y productos.',
    table: 'silver.unspsc' as const,
    columns: ['Codigo Producto', 'Nombre Producto'],
  },
]
</script>

<template>
  <section class="max-w-6xl mx-auto px-6 py-10 space-y-10">

    <!-- Header -->
    <div>
      <h1 class="text-3xl font-bold tracking-tight">Carga de Datos</h1>
      <p class="text-muted-foreground mt-1">Importa archivos Excel para poblar las tablas de referencia del sistema.</p>
    </div>

    <!-- Table counts summary -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div v-for="s in sections" :key="s.key" class="flex items-center gap-3 rounded-lg border p-4">
        <div :class="[s.bgColor, 'w-10 h-10 rounded-lg flex items-center justify-center']">
          <i :class="[s.icon, s.color, 'text-sm']"></i>
        </div>
        <div>
          <p class="text-2xl font-bold tabular-nums">{{ counts[s.table]?.toLocaleString() ?? 0 }}</p>
          <p class="text-xs text-muted-foreground">{{ s.title }}</p>
        </div>
      </div>
    </div>

    <Separator />

    <!-- Upload sections -->
    <div class="space-y-6">
      <Card v-for="s in sections" :key="s.key">
        <CardHeader>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div :class="[s.bgColor, 'w-9 h-9 rounded-lg flex items-center justify-center']">
                <i :class="[s.icon, s.color, 'text-sm']"></i>
              </div>
              <div>
                <CardTitle class="text-lg">{{ s.title }}</CardTitle>
                <CardDescription>{{ s.description }}</CardDescription>
              </div>
            </div>
            <!-- Queue summary badges -->
            <div v-if="queues[s.key].length > 0" class="flex items-center gap-2">
              <Badge v-if="queueSummary(s.key).uploading" class="bg-blue-500/10 text-blue-600 hover:bg-blue-500/10 gap-1 text-xs">
                <i class="fa-solid fa-spinner fa-spin text-[10px]"></i>
                {{ queueSummary(s.key).uploading }} procesando
              </Badge>
              <Badge v-if="queueSummary(s.key).pending" variant="outline" class="gap-1 text-xs">
                <i class="fa-solid fa-clock text-[10px]"></i>
                {{ queueSummary(s.key).pending }} en cola
              </Badge>
              <Badge v-if="queueSummary(s.key).success" class="bg-green-500/10 text-green-600 hover:bg-green-500/10 gap-1 text-xs">
                <i class="fa-solid fa-check text-[10px]"></i>
                {{ queueSummary(s.key).success }}
              </Badge>
              <Badge v-if="queueSummary(s.key).error" class="bg-red-500/10 text-red-600 hover:bg-red-500/10 gap-1 text-xs">
                <i class="fa-solid fa-xmark text-[10px]"></i>
                {{ queueSummary(s.key).error }}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent class="space-y-4">

          <!-- Expected columns -->
          <div>
            <p class="text-xs text-muted-foreground mb-2">Columnas esperadas:</p>
            <div class="flex flex-wrap gap-1.5">
              <Badge v-for="col in s.columns" :key="col" variant="outline" class="text-xs font-mono">
                {{ col }}
              </Badge>
            </div>
          </div>

          <Separator />

          <!-- Upload button -->
          <div class="flex items-center gap-3">
            <input
              :ref="(el) => { fileInputs[s.key] = el as HTMLInputElement }"
              type="file"
              accept=".xlsx"
              multiple
              class="hidden"
              @change="addFiles(s.key, $event)"
            />
            <Button
              variant="outline"
              class="gap-2"
              @click="fileInputs[s.key]?.click()"
            >
              <i class="fa-solid fa-file-arrow-up text-xs"></i>
              Seleccionar archivos .xlsx
            </Button>
            <Button
              v-if="queues[s.key].some(q => q.status === 'success' || q.status === 'error')"
              variant="ghost"
              size="sm"
              class="gap-1 text-xs text-muted-foreground"
              @click="clearCompleted(s.key)"
            >
              <i class="fa-solid fa-broom text-[10px]"></i>
              Limpiar
            </Button>
          </div>

          <!-- File queue -->
          <div v-if="queues[s.key].length > 0" class="space-y-1.5">
            <div
              v-for="item in queues[s.key]"
              :key="item.id"
              class="flex items-center gap-3 px-3 py-2 rounded-md text-sm"
              :class="{
                'bg-blue-500/5 border border-blue-500/20': item.status === 'uploading',
                'bg-muted/50': item.status === 'pending',
                'bg-green-500/5 border border-green-500/20': item.status === 'success',
                'bg-red-500/5 border border-red-500/20': item.status === 'error',
              }"
            >
              <!-- Status icon -->
              <i
                class="text-xs w-4 text-center shrink-0"
                :class="{
                  'fa-solid fa-clock text-muted-foreground': item.status === 'pending',
                  'fa-solid fa-spinner fa-spin text-blue-500': item.status === 'uploading',
                  'fa-solid fa-circle-check text-green-500': item.status === 'success',
                  'fa-solid fa-circle-xmark text-red-500': item.status === 'error',
                }"
              ></i>

              <!-- File name -->
              <span class="font-mono text-xs truncate flex-1">{{ item.file.name }}</span>

              <!-- File size -->
              <span class="text-xs text-muted-foreground shrink-0">{{ formatSize(item.file.size) }}</span>

              <!-- Result info -->
              <span v-if="item.status === 'success'" class="text-xs text-green-600 shrink-0">
                {{ item.row_count?.toLocaleString() }} filas · {{ item.elapsed_s }}s
              </span>
              <span v-if="item.status === 'error'" class="text-xs text-red-500 truncate max-w-[200px] shrink-0" :title="item.error">
                {{ item.error }}
              </span>

              <!-- Remove button -->
              <button
                v-if="item.status !== 'uploading'"
                class="text-muted-foreground hover:text-destructive transition-colors shrink-0"
                @click="removeFromQueue(s.key, item.id)"
              >
                <i class="fa-solid fa-xmark text-xs"></i>
              </button>
            </div>
          </div>

        </CardContent>
      </Card>
    </div>

    <Separator />

    <!-- Ingestion history -->
    <div>
      <h2 class="text-xl font-semibold mb-4 flex items-center gap-2">
        <i class="fa-solid fa-clock-rotate-left text-muted-foreground text-sm"></i>
        Historial de importaciones
      </h2>

      <Card v-if="logs.length === 0">
        <CardContent class="py-8 text-center text-muted-foreground text-sm">
          No hay importaciones registradas.
        </CardContent>
      </Card>

      <div v-else class="rounded-lg border overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-muted/50">
            <tr>
              <th class="text-left px-4 py-2.5 font-medium text-muted-foreground">Archivo</th>
              <th class="text-left px-4 py-2.5 font-medium text-muted-foreground">Destino</th>
              <th class="text-right px-4 py-2.5 font-medium text-muted-foreground">Filas</th>
              <th class="text-center px-4 py-2.5 font-medium text-muted-foreground">Estado</th>
              <th class="text-right px-4 py-2.5 font-medium text-muted-foreground">Fecha</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="log in logs" :key="log.id" class="hover:bg-muted/30 transition-colors">
              <td class="px-4 py-2.5 font-mono text-xs">{{ log.file_name }}</td>
              <td class="px-4 py-2.5">
                <Badge variant="outline" class="text-xs">{{ log.file_path }}</Badge>
              </td>
              <td class="px-4 py-2.5 text-right tabular-nums">{{ log.row_count.toLocaleString() }}</td>
              <td class="px-4 py-2.5 text-center">
                <Badge
                  :class="log.status === 'success'
                    ? 'bg-green-500/10 text-green-600 hover:bg-green-500/10'
                    : 'bg-red-500/10 text-red-600 hover:bg-red-500/10'"
                  class="text-xs"
                >
                  {{ log.status }}
                </Badge>
              </td>
              <td class="px-4 py-2.5 text-right text-xs text-muted-foreground">{{ formatDate(log.ingested_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </section>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Input } from '@/components/ui/input'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { API_BASE } from '@/config'
import { authFetch } from '@/composables/useAuth'

const activeTab = ref('importar')

// ═══════════════════════════════════════════════════
// ETL (Importar)
// ═══════════════════════════════════════════════════

const ETL_API = `${API_BASE}/api/etl`

interface IngestionLog {
  id: number
  file_name: string
  file_path: string | null
  row_count: number
  status: string
  error_message: string | null
  elapsed_s: number | null
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
    const res = await authFetch(`${ETL_API}/logs`)
    if (res.ok) logs.value = await res.json()
  } catch { /* */ }
}

async function fetchCounts() {
  try {
    const res = await authFetch(`${ETL_API}/counts`)
    if (res.ok) counts.value = await res.json()
  } catch { /* */ }
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
      const res = await authFetch(`${ETL_API}/upload/${key}`, { method: 'POST', body: form })
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
    queues.value[key].push({ id: nextQueueId++, file, status: 'pending' })
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
  return {
    pending: q.filter(i => i.status === 'pending').length,
    uploading: q.filter(i => i.status === 'uploading').length,
    success: q.filter(i => i.status === 'success').length,
    error: q.filter(i => i.status === 'error').length,
    total: q.length,
  }
}

function formatDateEtl(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('es-GT', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const etlSections = [
  {
    key: 'unspsc' as const,
    title: 'UNSPSC (Naciones Unidas)',
    icon: 'fa-solid fa-globe',
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    description: 'Clasificador UNSPSC con segmentos, familias, clases y productos. Debe cargarse primero.',
    table: 'silver.unspsc' as const,
    columns: ['Codigo Producto', 'Nombre Producto'],
  },
  {
    key: 'classes' as const,
    title: 'Clases / Denominaciones',
    icon: 'fa-solid fa-tags',
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
    description: 'Catalogo de clases de material. Requiere UNSPSC cargado.',
    table: 'silver.classes' as const,
    columns: ['Codigo', 'Denominacion', 'Grupo de Articulos', 'Sector', 'Tipo de Material', 'UNSPSC'],
  },
  {
    key: 'materials' as const,
    title: 'Maestro de Materiales',
    icon: 'fa-solid fa-cubes',
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    description: 'Carga los archivos del maestro SAP. Requiere clases cargadas.',
    table: 'silver.materials' as const,
    columns: ['Material', 'Unidad medida base', 'Denom.estandar', 'Texto breve de material'],
  },
]

// ═══════════════════════════════════════════════════
// Export (Exportar)
// ═══════════════════════════════════════════════════

const EXPORT_API = `${API_BASE}/api/export`

interface RequestRow {
  id: number
  conversation_id: string | null
  short_text: string | null
  long_text: string | null
  material_type_code: string | null
  category: string | null
  class_name: string | null
  confidence: number | null
  corrected: boolean
  status: string
  created_at: string
  confirmed_at: string | null
  exported_at: string | null
}

const requests = ref<RequestRow[]>([])
const exportLoading = ref(false)
const exporting = ref(false)
const selectedIds = ref<Set<number>>(new Set())
const searchQuery = ref('')
const statusFilter = ref('confirmed')
const excludeExported = ref(true)

const filteredRequests = computed(() => {
  if (!searchQuery.value.trim()) return requests.value
  const q = searchQuery.value.toLowerCase()
  return requests.value.filter(r =>
    (r.short_text?.toLowerCase().includes(q)) ||
    (r.long_text?.toLowerCase().includes(q)) ||
    (r.category?.toLowerCase().includes(q)) ||
    (r.material_type_code?.toLowerCase().includes(q)) ||
    String(r.id).includes(q)
  )
})

const allSelected = computed(() =>
  filteredRequests.value.length > 0 && filteredRequests.value.every(r => selectedIds.value.has(r.id))
)

function toggleAll() {
  if (allSelected.value) {
    filteredRequests.value.forEach(r => selectedIds.value.delete(r.id))
  } else {
    filteredRequests.value.forEach(r => selectedIds.value.add(r.id))
  }
}

function toggleRow(id: number) {
  if (selectedIds.value.has(id)) selectedIds.value.delete(id)
  else selectedIds.value.add(id)
}

function formatDateExport(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-GT', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const statusOptions = [
  { value: 'confirmed', label: 'Confirmados' },
  { value: 'confirmed,exported', label: 'Confirmados + Exportados' },
  { value: 'confirmed,exported,existing_match', label: 'Todos finalizados' },
  { value: 'pending,confirmed,exported,discarded,existing_match', label: 'Todos' },
]

async function fetchRequests() {
  exportLoading.value = true
  selectedIds.value.clear()
  try {
    const params = new URLSearchParams({
      status: statusFilter.value,
      exclude_exported: String(excludeExported.value),
    })
    const res = await authFetch(`${EXPORT_API}/requests?${params}`)
    if (res.ok) requests.value = await res.json()
  } catch { /* */ }
  exportLoading.value = false
}

async function exportSelected() {
  const ids = Array.from(selectedIds.value)
  if (ids.length === 0) return

  exporting.value = true
  try {
    const res = await authFetch(`${EXPORT_API}/xlsx`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids }),
    })

    if (res.ok) {
      const blob = await res.blob()
      const disposition = res.headers.get('Content-Disposition') || ''
      const match = disposition.match(/filename="(.+)"/)
      const filename = match ? match[1] : 'gamma_export.xlsx'

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      await fetchRequests()
    }
  } catch { /* */ }
  exporting.value = false
}

// ═══════════════════════════════════════════════════
// Init
// ═══════════════════════════════════════════════════

onMounted(() => {
  fetchLogs()
  fetchCounts()
  fetchRequests()
})
</script>

<template>
  <section class="max-w-6xl mx-auto px-6 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold tracking-tight">Datos</h1>
      <p class="text-sm text-muted-foreground mt-1">Importacion de datos maestros y exportacion de solicitudes</p>
    </div>

    <Tabs v-model="activeTab">
      <TabsList class="mb-6">
        <TabsTrigger value="importar" class="gap-2">
          <i class="fa-solid fa-file-import text-xs"></i>
          Importar
        </TabsTrigger>
        <TabsTrigger value="exportar" class="gap-2">
          <i class="fa-solid fa-file-excel text-xs"></i>
          Exportar
        </TabsTrigger>
      </TabsList>

      <!-- ════════════════════════ IMPORTAR ════════════════════════ -->
      <TabsContent value="importar" class="space-y-8">

        <!-- Table counts -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div v-for="s in etlSections" :key="s.key" class="flex items-center gap-3 rounded-lg border p-4">
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
          <Card v-for="s in etlSections" :key="s.key">
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
              <div>
                <p class="text-xs text-muted-foreground mb-2">Columnas esperadas:</p>
                <div class="flex flex-wrap gap-1.5">
                  <Badge v-for="col in s.columns" :key="col" variant="outline" class="text-xs font-mono">{{ col }}</Badge>
                </div>
              </div>

              <Separator />

              <div class="flex items-center gap-3">
                <input
                  :ref="(el) => { fileInputs[s.key] = el as HTMLInputElement }"
                  type="file" accept=".xlsx" multiple class="hidden"
                  @change="addFiles(s.key, $event)"
                />
                <Button variant="outline" class="gap-2" @click="fileInputs[s.key]?.click()">
                  <i class="fa-solid fa-file-arrow-up text-xs"></i>
                  Seleccionar archivos .xlsx
                </Button>
                <Button
                  v-if="queues[s.key].some(q => q.status === 'success' || q.status === 'error')"
                  variant="ghost" size="sm" class="gap-1 text-xs text-muted-foreground"
                  @click="clearCompleted(s.key)"
                >
                  <i class="fa-solid fa-broom text-[10px]"></i>
                  Limpiar cola
                </Button>
              </div>

              <div v-if="queues[s.key].length > 0" class="space-y-1.5">
                <div
                  v-for="item in queues[s.key]" :key="item.id"
                  class="flex items-center gap-3 px-3 py-2 rounded-md text-sm"
                  :class="{
                    'bg-blue-500/5 border border-blue-500/20': item.status === 'uploading',
                    'bg-muted/50': item.status === 'pending',
                    'bg-green-500/5 border border-green-500/20': item.status === 'success',
                    'bg-red-500/5 border border-red-500/20': item.status === 'error',
                  }"
                >
                  <i class="text-xs w-4 text-center shrink-0" :class="{
                    'fa-solid fa-clock text-muted-foreground': item.status === 'pending',
                    'fa-solid fa-spinner fa-spin text-blue-500': item.status === 'uploading',
                    'fa-solid fa-circle-check text-green-500': item.status === 'success',
                    'fa-solid fa-circle-xmark text-red-500': item.status === 'error',
                  }"></i>
                  <span class="font-mono text-xs truncate flex-1">{{ item.file.name }}</span>
                  <span class="text-xs text-muted-foreground shrink-0">{{ formatSize(item.file.size) }}</span>
                  <span v-if="item.status === 'success'" class="text-xs text-green-600 shrink-0">
                    {{ item.row_count?.toLocaleString() }} filas · {{ item.elapsed_s }}s
                  </span>
                  <span v-if="item.status === 'error'" class="text-xs text-red-500 truncate max-w-[200px] shrink-0" :title="item.error">
                    {{ item.error }}
                  </span>
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
                  <td class="px-4 py-2.5"><Badge variant="outline" class="text-xs">{{ log.file_path }}</Badge></td>
                  <td class="px-4 py-2.5 text-right tabular-nums">{{ log.row_count.toLocaleString() }}</td>
                  <td class="px-4 py-2.5 text-center">
                    <Badge :class="log.status === 'success' ? 'bg-green-500/10 text-green-600 hover:bg-green-500/10' : 'bg-red-500/10 text-red-600 hover:bg-red-500/10'" class="text-xs">
                      {{ log.status }}
                    </Badge>
                  </td>
                  <td class="px-4 py-2.5 text-right text-xs text-muted-foreground">{{ formatDateEtl(log.ingested_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </TabsContent>

      <!-- ════════════════════════ EXPORTAR ════════════════════════ -->
      <TabsContent value="exportar" class="space-y-4">

        <!-- Filters -->
        <Card>
          <CardContent class="p-4 flex flex-wrap items-center gap-4">
            <div class="flex items-center gap-2">
              <label class="text-xs text-muted-foreground shrink-0">Estado:</label>
              <select
                v-model="statusFilter"
                class="text-sm border rounded-md px-3 py-1.5 bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                @change="fetchRequests"
              >
                <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>

            <label class="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" v-model="excludeExported" class="rounded" @change="fetchRequests" />
              <span class="text-xs text-muted-foreground">Excluir ya exportados</span>
            </label>

            <div class="flex-1 min-w-[200px]">
              <Input v-model="searchQuery" placeholder="Buscar por texto, clase, tipo..." class="text-sm h-9" />
            </div>

            <div class="flex items-center gap-3 shrink-0">
              <span class="text-xs text-muted-foreground">
                {{ filteredRequests.length }} solicitudes
                <span v-if="selectedIds.size > 0">· {{ selectedIds.size }} seleccionadas</span>
              </span>
              <Button
                size="sm" class="gap-2"
                :disabled="selectedIds.size === 0 || exporting"
                @click="exportSelected"
              >
                <i class="fa-solid fa-file-excel text-xs"></i>
                Exportar {{ selectedIds.size > 0 ? `(${selectedIds.size})` : '' }}
              </Button>
            </div>
          </CardContent>
        </Card>

        <!-- Table -->
        <Card>
          <CardContent class="p-0">
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b bg-muted/50">
                    <th class="px-3 py-3 text-left w-10">
                      <input type="checkbox" :checked="allSelected" :indeterminate="selectedIds.size > 0 && !allSelected" class="rounded" @change="toggleAll" />
                    </th>
                    <th class="px-3 py-3 text-left text-xs font-medium text-muted-foreground">ID</th>
                    <th class="px-3 py-3 text-left text-xs font-medium text-muted-foreground">Descripcion corta</th>
                    <th class="px-3 py-3 text-left text-xs font-medium text-muted-foreground">Tipo</th>
                    <th class="px-3 py-3 text-left text-xs font-medium text-muted-foreground">Clase</th>
                    <th class="px-3 py-3 text-left text-xs font-medium text-muted-foreground">Confianza</th>
                    <th class="px-3 py-3 text-left text-xs font-medium text-muted-foreground">Estado</th>
                    <th class="px-3 py-3 text-left text-xs font-medium text-muted-foreground">Confirmado</th>
                    <th class="px-3 py-3 text-left text-xs font-medium text-muted-foreground">Exportado</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="req in filteredRequests" :key="req.id"
                    class="border-b last:border-0 hover:bg-muted/30 transition-colors cursor-pointer"
                    :class="selectedIds.has(req.id) ? 'bg-primary/5' : ''"
                    @click="toggleRow(req.id)"
                  >
                    <td class="px-3 py-3">
                      <input type="checkbox" :checked="selectedIds.has(req.id)" class="rounded" @click.stop @change="toggleRow(req.id)" />
                    </td>
                    <td class="px-3 py-3 text-xs text-muted-foreground font-mono">{{ req.id }}</td>
                    <td class="px-3 py-3">
                      <div class="font-mono text-xs">{{ req.short_text || '—' }}</div>
                      <div v-if="req.long_text" class="text-[10px] text-muted-foreground truncate max-w-[300px]">{{ req.long_text }}</div>
                    </td>
                    <td class="px-3 py-3">
                      <Badge v-if="req.material_type_code" class="text-[10px] bg-amber-500/10 text-amber-600 hover:bg-amber-500/10">{{ req.material_type_code }}</Badge>
                      <span v-else class="text-muted-foreground">—</span>
                    </td>
                    <td class="px-3 py-3">
                      <div v-if="req.category" class="flex flex-col">
                        <span class="font-mono text-xs">{{ req.category }}</span>
                        <span v-if="req.class_name" class="text-[10px] text-muted-foreground">{{ req.class_name }}</span>
                      </div>
                      <span v-else class="text-muted-foreground">—</span>
                    </td>
                    <td class="px-3 py-3 text-xs">
                      <div v-if="req.confidence != null" class="flex items-center gap-1.5">
                        <div class="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div class="h-full rounded-full"
                            :class="req.confidence > 0.7 ? 'bg-green-500' : req.confidence > 0.4 ? 'bg-amber-500' : 'bg-red-500'"
                            :style="{ width: `${req.confidence * 100}%` }"
                          ></div>
                        </div>
                        <span class="text-muted-foreground">{{ (req.confidence * 100).toFixed(0) }}%</span>
                        <i v-if="req.corrected" class="fa-solid fa-pen text-amber-500 text-[10px]" title="Corregido por usuario"></i>
                      </div>
                      <span v-else class="text-muted-foreground">—</span>
                    </td>
                    <td class="px-3 py-3">
                      <Badge variant="outline" class="text-[10px]" :class="{
                        'bg-green-500/10 text-green-600 hover:bg-green-500/10': req.status === 'confirmed',
                        'bg-blue-500/10 text-blue-600 hover:bg-blue-500/10': req.status === 'exported',
                        'bg-red-500/10 text-red-600 hover:bg-red-500/10': req.status === 'discarded',
                      }">{{ req.status }}</Badge>
                    </td>
                    <td class="px-3 py-3 text-[10px] text-muted-foreground">{{ formatDateExport(req.confirmed_at) }}</td>
                    <td class="px-3 py-3 text-[10px] text-muted-foreground">{{ formatDateExport(req.exported_at) }}</td>
                  </tr>
                  <tr v-if="filteredRequests.length === 0">
                    <td colspan="9" class="px-3 py-12 text-center text-muted-foreground">
                      <div class="flex flex-col items-center gap-2">
                        <i class="fa-solid fa-inbox text-3xl"></i>
                        <p class="text-sm">{{ exportLoading ? 'Cargando...' : 'Sin solicitudes para exportar' }}</p>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  </section>
</template>

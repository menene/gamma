<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { API_BASE } from '@/config'
import { authFetch } from '@/composables/useAuth'

const API = `${API_BASE}/api/export`

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
const loading = ref(false)
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

function formatDate(iso: string | null): string {
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
  loading.value = true
  selectedIds.value.clear()
  try {
    const params = new URLSearchParams({
      status: statusFilter.value,
      exclude_exported: String(excludeExported.value),
    })
    const res = await authFetch(`${API}/requests?${params}`)
    if (res.ok) requests.value = await res.json()
  } catch { /* */ }
  loading.value = false
}

async function exportSelected() {
  const ids = Array.from(selectedIds.value)
  if (ids.length === 0) return

  exporting.value = true
  try {
    const res = await authFetch(`${API}/xlsx`, {
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

      // Refresh list — exported items may now be excluded
      await fetchRequests()
    }
  } catch { /* */ }
  exporting.value = false
}

onMounted(fetchRequests)
</script>

<template>
  <section class="max-w-7xl mx-auto px-6 py-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Exportar solicitudes</h1>
        <p class="text-sm text-muted-foreground mt-1">Selecciona las solicitudes a exportar como XLSX</p>
      </div>
      <Button
        class="gap-2"
        :disabled="selectedIds.size === 0 || exporting"
        @click="exportSelected"
      >
        <i class="fa-solid fa-file-excel text-sm"></i>
        Exportar {{ selectedIds.size > 0 ? `(${selectedIds.size})` : '' }}
      </Button>
    </div>

    <!-- Filters -->
    <Card class="mb-4">
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
          <Input
            v-model="searchQuery"
            placeholder="Buscar por texto, clase, tipo..."
            class="text-sm h-9"
          />
        </div>

        <div class="text-xs text-muted-foreground shrink-0">
          {{ filteredRequests.length }} solicitudes
          <span v-if="selectedIds.size > 0">· {{ selectedIds.size }} seleccionadas</span>
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
                  <input
                    type="checkbox"
                    :checked="allSelected"
                    :indeterminate="selectedIds.size > 0 && !allSelected"
                    class="rounded"
                    @change="toggleAll"
                  />
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
                v-for="req in filteredRequests"
                :key="req.id"
                class="border-b last:border-0 hover:bg-muted/30 transition-colors cursor-pointer"
                :class="selectedIds.has(req.id) ? 'bg-primary/5' : ''"
                @click="toggleRow(req.id)"
              >
                <td class="px-3 py-3">
                  <input
                    type="checkbox"
                    :checked="selectedIds.has(req.id)"
                    class="rounded"
                    @click.stop
                    @change="toggleRow(req.id)"
                  />
                </td>
                <td class="px-3 py-3 text-xs text-muted-foreground font-mono">{{ req.id }}</td>
                <td class="px-3 py-3">
                  <div class="font-mono text-xs">{{ req.short_text || '—' }}</div>
                  <div v-if="req.long_text" class="text-[10px] text-muted-foreground truncate max-w-[300px]">{{ req.long_text }}</div>
                </td>
                <td class="px-3 py-3">
                  <Badge v-if="req.material_type_code" class="text-[10px] bg-amber-500/10 text-amber-600 hover:bg-amber-500/10">
                    {{ req.material_type_code }}
                  </Badge>
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
                      <div
                        class="h-full rounded-full"
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
                  <Badge
                    :variant="req.status === 'confirmed' ? 'default' : 'outline'"
                    class="text-[10px]"
                    :class="{
                      'bg-green-500/10 text-green-600 hover:bg-green-500/10': req.status === 'confirmed',
                      'bg-blue-500/10 text-blue-600 hover:bg-blue-500/10': req.status === 'exported',
                      'bg-red-500/10 text-red-600 hover:bg-red-500/10': req.status === 'discarded',
                    }"
                  >
                    {{ req.status }}
                  </Badge>
                </td>
                <td class="px-3 py-3 text-[10px] text-muted-foreground">{{ formatDate(req.confirmed_at) }}</td>
                <td class="px-3 py-3 text-[10px] text-muted-foreground">{{ formatDate(req.exported_at) }}</td>
              </tr>
              <tr v-if="filteredRequests.length === 0">
                <td colspan="9" class="px-3 py-12 text-center text-muted-foreground">
                  <div class="flex flex-col items-center gap-2">
                    <i class="fa-solid fa-inbox text-3xl"></i>
                    <p class="text-sm">{{ loading ? 'Cargando...' : 'Sin solicitudes para exportar' }}</p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </section>
</template>

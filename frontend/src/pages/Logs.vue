<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { API_BASE } from '@/config'
import { authFetch } from '@/composables/useAuth'

const API = `${API_BASE}/api/logs`

interface AppError {
  id: number
  source: string
  message: string
  details: Record<string, any> | null
  logged_at: string
}

interface LLMLog {
  id: number
  conversation_id: string | null
  model: string
  user_message: string
  action: string | null
  tokens_in: number | null
  tokens_out: number | null
  elapsed_s: number | null
  error: string | null
  logged_at: string
}

interface DuplicateLog {
  id: number
  conversation_id: string | null
  request_id: number | null
  action: string
  short_text: string | null
  selected_material_id: string | null
  logged_at: string
}

interface PredictionLog {
  id: number
  type: string
  input: Record<string, any> | null
  output: Record<string, any> | null
  confidence: number | null
  logged_at: string
}

const activeTab = ref('errors')
const errors = ref<AppError[]>([])
const llmLogs = ref<LLMLog[]>([])
const duplicateLogs = ref<DuplicateLog[]>([])
const predictionLogs = ref<PredictionLog[]>([])
const loading = ref(false)
const expandedIds = ref<Set<string>>(new Set())

function toggleExpand(key: string) {
  if (expandedIds.value.has(key)) expandedIds.value.delete(key)
  else expandedIds.value.add(key)
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('es-GT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const llmErrors = computed(() => llmLogs.value.filter(l => l.error))
const llmSuccesses = computed(() => llmLogs.value.filter(l => !l.error))

async function fetchAll() {
  loading.value = true
  try {
    const [errRes, llmRes, dupRes, predRes] = await Promise.all([
      authFetch(`${API}/errors?limit=200`),
      authFetch(`${API}/llm?limit=200`),
      authFetch(`${API}/duplicates?limit=200`),
      authFetch(`${API}/predictions?limit=200`),
    ])
    if (errRes.ok) errors.value = await errRes.json()
    if (llmRes.ok) llmLogs.value = await llmRes.json()
    if (dupRes.ok) duplicateLogs.value = await dupRes.json()
    if (predRes.ok) predictionLogs.value = await predRes.json()
  } catch { /* nothing to log to */ }
  loading.value = false
}

onMounted(fetchAll)
</script>

<template>
  <section class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Logs del sistema</h1>
        <p class="text-sm text-muted-foreground mt-1">Errores, interacciones LLM, duplicados y predicciones</p>
      </div>
      <Button variant="outline" size="sm" class="gap-2" @click="fetchAll" :disabled="loading">
        <i class="fa-solid fa-rotate" :class="loading ? 'animate-spin' : ''"></i>
        Actualizar
      </Button>
    </div>

    <Tabs v-model="activeTab">
      <TabsList class="mb-4">
        <TabsTrigger value="errors" class="gap-2">
          <i class="fa-solid fa-triangle-exclamation text-xs"></i>
          Errores
          <Badge v-if="errors.length" variant="destructive" class="text-[10px] px-1.5 py-0 ml-1">{{ errors.length }}</Badge>
        </TabsTrigger>
        <TabsTrigger value="llm" class="gap-2">
          <i class="fa-solid fa-brain text-xs"></i>
          LLM
          <Badge v-if="llmErrors.length" variant="destructive" class="text-[10px] px-1.5 py-0 ml-1">{{ llmErrors.length }}</Badge>
        </TabsTrigger>
        <TabsTrigger value="duplicates" class="gap-2">
          <i class="fa-solid fa-clone text-xs"></i>
          Duplicados
        </TabsTrigger>
        <TabsTrigger value="predictions" class="gap-2">
          <i class="fa-solid fa-chart-bar text-xs"></i>
          Predicciones
        </TabsTrigger>
      </TabsList>

      <!-- Errors -->
      <TabsContent value="errors">
        <div v-if="errors.length === 0" class="text-center py-12 text-muted-foreground">
          <i class="fa-solid fa-check-circle text-3xl mb-3 text-green-500"></i>
          <p class="text-sm">Sin errores registrados</p>
        </div>
        <div v-else class="space-y-2">
          <Card v-for="err in errors" :key="err.id" class="overflow-hidden border-red-500/20">
            <CardContent class="p-0">
              <div
                class="px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-muted/50 transition-colors"
                @click="toggleExpand(`err-${err.id}`)"
              >
                <i class="fa-solid fa-circle-xmark text-red-500 text-xs shrink-0"></i>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" class="text-[10px] font-mono shrink-0">{{ err.source }}</Badge>
                    <span class="text-sm truncate">{{ err.message }}</span>
                  </div>
                </div>
                <span class="text-[10px] text-muted-foreground shrink-0">{{ formatDate(err.logged_at) }}</span>
                <i class="fa-solid text-xs text-muted-foreground" :class="expandedIds.has(`err-${err.id}`) ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
              </div>
              <div v-if="expandedIds.has(`err-${err.id}`) && err.details" class="px-4 pb-3 border-t">
                <pre class="text-xs bg-muted/50 p-3 rounded-md mt-2 overflow-x-auto">{{ JSON.stringify(err.details, null, 2) }}</pre>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <!-- LLM -->
      <TabsContent value="llm">
        <div v-if="llmLogs.length === 0" class="text-center py-12 text-muted-foreground">
          <p class="text-sm">Sin logs de LLM</p>
        </div>
        <div v-else class="space-y-2">
          <Card v-for="log in llmLogs" :key="log.id" class="overflow-hidden" :class="log.error ? 'border-red-500/20' : ''">
            <CardContent class="p-0">
              <div
                class="px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-muted/50 transition-colors"
                @click="toggleExpand(`llm-${log.id}`)"
              >
                <i class="text-xs shrink-0" :class="log.error ? 'fa-solid fa-circle-xmark text-red-500' : 'fa-solid fa-circle-check text-green-500'"></i>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <Badge v-if="log.action" variant="outline" class="text-[10px] shrink-0">{{ log.action }}</Badge>
                    <Badge variant="secondary" class="text-[10px] font-mono shrink-0">{{ log.model }}</Badge>
                    <span class="text-sm truncate">{{ log.user_message.slice(0, 80) }}</span>
                  </div>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <span v-if="log.elapsed_s" class="text-[10px] text-muted-foreground">{{ log.elapsed_s }}s</span>
                  <span v-if="log.tokens_in || log.tokens_out" class="text-[10px] text-muted-foreground">
                    {{ log.tokens_in || 0 }}→{{ log.tokens_out || 0 }}t
                  </span>
                  <span class="text-[10px] text-muted-foreground">{{ formatDate(log.logged_at) }}</span>
                </div>
                <i class="fa-solid text-xs text-muted-foreground" :class="expandedIds.has(`llm-${log.id}`) ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
              </div>
              <div v-if="expandedIds.has(`llm-${log.id}`)" class="px-4 pb-3 border-t space-y-2 mt-0 pt-2">
                <div>
                  <p class="text-[10px] text-muted-foreground mb-1">Mensaje del usuario</p>
                  <pre class="text-xs bg-muted/50 p-3 rounded-md overflow-x-auto whitespace-pre-wrap">{{ log.user_message }}</pre>
                </div>
                <div v-if="log.error">
                  <p class="text-[10px] text-red-500 mb-1">Error</p>
                  <pre class="text-xs bg-red-500/10 p-3 rounded-md overflow-x-auto">{{ log.error }}</pre>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <!-- Duplicates -->
      <TabsContent value="duplicates">
        <div v-if="duplicateLogs.length === 0" class="text-center py-12 text-muted-foreground">
          <p class="text-sm">Sin decisiones de duplicados registradas</p>
        </div>
        <div v-else class="space-y-2">
          <Card v-for="log in duplicateLogs" :key="log.id" class="overflow-hidden">
            <CardContent class="px-4 py-3 flex items-center gap-3">
              <i class="text-xs shrink-0" :class="log.action === 'accepted' ? 'fa-solid fa-link text-blue-500' : 'fa-solid fa-xmark text-amber-500'"></i>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <Badge :variant="log.action === 'accepted' ? 'default' : 'outline'" class="text-[10px] shrink-0">
                    {{ log.action === 'accepted' ? 'Aceptado' : 'Rechazado' }}
                  </Badge>
                  <span v-if="log.short_text" class="text-sm font-mono truncate">{{ log.short_text }}</span>
                  <span v-if="log.selected_material_id" class="text-[10px] text-muted-foreground">→ {{ log.selected_material_id }}</span>
                </div>
              </div>
              <span class="text-[10px] text-muted-foreground shrink-0">{{ formatDate(log.logged_at) }}</span>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <!-- Predictions -->
      <TabsContent value="predictions">
        <div v-if="predictionLogs.length === 0" class="text-center py-12 text-muted-foreground">
          <p class="text-sm">Sin predicciones registradas</p>
        </div>
        <div v-else class="space-y-2">
          <Card v-for="log in predictionLogs" :key="log.id" class="overflow-hidden">
            <CardContent class="p-0">
              <div
                class="px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-muted/50 transition-colors"
                @click="toggleExpand(`pred-${log.id}`)"
              >
                <i class="fa-solid fa-chart-bar text-xs text-violet-500 shrink-0"></i>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" class="text-[10px] shrink-0">{{ log.type }}</Badge>
                    <span v-if="log.confidence" class="text-sm">{{ (log.confidence * 100).toFixed(1) }}% confianza</span>
                    <span v-if="log.input?.short_text" class="text-xs text-muted-foreground font-mono truncate">{{ log.input.short_text }}</span>
                  </div>
                </div>
                <span class="text-[10px] text-muted-foreground shrink-0">{{ formatDate(log.logged_at) }}</span>
                <i class="fa-solid text-xs text-muted-foreground" :class="expandedIds.has(`pred-${log.id}`) ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
              </div>
              <div v-if="expandedIds.has(`pred-${log.id}`)" class="px-4 pb-3 border-t space-y-2 pt-2">
                <div v-if="log.input">
                  <p class="text-[10px] text-muted-foreground mb-1">Input</p>
                  <pre class="text-xs bg-muted/50 p-3 rounded-md overflow-x-auto">{{ JSON.stringify(log.input, null, 2) }}</pre>
                </div>
                <div v-if="log.output">
                  <p class="text-[10px] text-muted-foreground mb-1">Output</p>
                  <pre class="text-xs bg-muted/50 p-3 rounded-md overflow-x-auto">{{ JSON.stringify(log.output, null, 2) }}</pre>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>
    </Tabs>
  </section>
</template>

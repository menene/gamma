<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { API_BASE } from '@/config'
import { authFetch } from '@/composables/useAuth'

const API = `${API_BASE}/api/chat`
const LOGS_API = `${API_BASE}/api/logs`

async function logAppError(source: string, message: string, details?: Record<string, any>) {
  try {
    await authFetch(`${LOGS_API}/errors`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source, message, details }),
    })
  } catch { /* last resort — can't log the log failure */ }
}

interface Duplicate {
  material_id: string
  short_text: string
  similarity: number
}

interface ModelPrediction {
  categoria: string
  confianza: number
  top_k: [string, number, string?][]
}

interface SelectedClass {
  code: string
  name: string
}

interface Proposal {
  request_id?: number
  short_text: string
  long_text?: string
  material_type_id: string
  duplicates: Duplicate[]
  model_prediction?: ModelPrediction
  selected_class?: SelectedClass
}

type ProcessingStep = 'llm' | 'duplicates' | 'predict'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content?: string
  llm_content?: string
  type: 'text' | 'processing' | 'proposal' | 'confirmed' | 'error' | 'duplicates_review' | 'existing_match'
  proposal?: Proposal
  processingStep?: ProcessingStep
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
  created_at: string
  updated_at: string
}

interface ConversationSummary {
  id: string
  title: string
  created_at: string
  updated_at: string
}

const WELCOME_MSG: Message = {
  id: 0,
  role: 'assistant',
  content: 'Hola! Soy el asistente de GAMMA. Describime el material que queres dar de alta y me encargo de validar duplicados, generar la descripcion y clasificarlo.',
  type: 'text',
}

const input = ref('')
const messages = ref<Message[]>([WELCOME_MSG])
const isProcessing = ref(false)
const copiedId = ref<number | null>(null)
const expandedConfirmed = ref<Set<number>>(new Set())
const classSearchOpen = ref<number | null>(null)
const classSearchQuery = ref('')
const awaitingAction = ref(false)
const classSearchResults = ref<{ code: string; name: string }[]>([])
let classSearchTimeout: ReturnType<typeof setTimeout> | null = null

function selectClass(msgId: number, code: string, name: string) {
  const msg = messages.value.find(m => m.id === msgId)
  if (msg?.proposal) {
    msg.proposal.selected_class = { code, name }
    classSearchOpen.value = null
    classSearchQuery.value = ''
    classSearchResults.value = []
  }
}

function toggleClassSearch(msgId: number) {
  if (classSearchOpen.value === msgId) {
    classSearchOpen.value = null
    classSearchQuery.value = ''
    classSearchResults.value = []
  } else {
    classSearchOpen.value = msgId
    classSearchQuery.value = ''
    classSearchResults.value = []
  }
}

function onClassSearch(q: string) {
  classSearchQuery.value = q
  if (classSearchTimeout) clearTimeout(classSearchTimeout)
  if (!q.trim()) { classSearchResults.value = []; return }
  classSearchTimeout = setTimeout(async () => {
    try {
      const res = await authFetch(`${API}/classes?q=${encodeURIComponent(q)}`)
      if (res.ok) classSearchResults.value = await res.json()
    } catch (e: any) { classSearchResults.value = []; logAppError('chat:classSearch', e.message) }
  }, 300)
}

function copyToClipboard(msgId: number, text: string) {
  navigator.clipboard.writeText(text)
  copiedId.value = msgId
  setTimeout(() => { if (copiedId.value === msgId) copiedId.value = null }, 2000)
}
const scrollRef = ref<HTMLDivElement | null>(null)

const conversations = ref<ConversationSummary[]>([])
const activeConvId = ref<string | null>(null)
const activeRequestId = ref<number | null>(null)
let nextId = 1

function scrollToBottom() {
  nextTick(() => {
    const el = scrollRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

// --- API helpers ---

async function fetchConversations() {
  try {
    const res = await authFetch(`${API}/conversations`)
    if (res.ok) conversations.value = await res.json()
    else logAppError('chat:fetchConversations', `HTTP ${res.status}`, { url: `${API}/conversations` })
  } catch (e: any) { logAppError('chat:fetchConversations', e.message) }
}

async function createConversation(): Promise<Conversation | null> {
  try {
    const res = await authFetch(`${API}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Nueva conversacion' }),
    })
    if (res.ok) return await res.json()
    logAppError('chat:createConversation', `HTTP ${res.status}`)
  } catch (e: any) { logAppError('chat:createConversation', e.message) }
  return null
}

function deriveTitle(): string {
  const saveable = messages.value.filter(m => m.type !== 'processing')

  // Prefer confirmed/existing match product name
  const confirmed = [...saveable].reverse().find(m => m.type === 'confirmed' && m.proposal?.short_text)
  if (confirmed?.proposal?.short_text) return confirmed.proposal.short_text.slice(0, 60)

  const existing = [...saveable].reverse().find(m => m.type === 'existing_match' && m.content)
  if (existing?.content) return existing.content.slice(0, 60)

  // Then proposal short_text
  const proposal = [...saveable].reverse().find(m => m.type === 'proposal' && m.proposal?.short_text)
  if (proposal?.proposal?.short_text) return proposal.proposal.short_text.slice(0, 60)

  // Fallback to first user message
  const firstUser = saveable.find(m => m.role === 'user')
  return firstUser?.content?.slice(0, 60) || 'Nueva conversacion'
}

async function saveMessages() {
  if (!activeConvId.value) return
  const saveable = messages.value.filter(m => m.type !== 'processing')
  try {
    const title = deriveTitle()

    const res = await authFetch(`${API}/conversations/${activeConvId.value}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: saveable, title }),
    })
    if (!res.ok) logAppError('chat:saveMessages', `HTTP ${res.status}`)
    await fetchConversations()
  } catch (e: any) { logAppError('chat:saveMessages', e.message) }
}

async function loadConversation(id: string) {
  try {
    const res = await authFetch(`${API}/conversations/${id}`)
    if (res.ok) {
      const conv: Conversation = await res.json()
      activeConvId.value = conv.id
      messages.value = conv.messages.length > 0 ? conv.messages : [WELCOME_MSG]
      nextId = Math.max(...messages.value.map(m => m.id), 0) + 1
      awaitingAction.value = messages.value.some(m => m.type === 'duplicates_review')
      scrollToBottom()
    } else {
      logAppError('chat:loadConversation', `HTTP ${res.status}`, { conversationId: id })
    }
  } catch (e: any) { logAppError('chat:loadConversation', e.message) }
}

async function deleteConversation(id: string) {
  try {
    const res = await authFetch(`${API}/conversations/${id}`, { method: 'DELETE' })
    if (!res.ok) logAppError('chat:deleteConversation', `HTTP ${res.status}`, { conversationId: id })
    if (activeConvId.value === id) {
      await startNewConversation()
    }
    await fetchConversations()
  } catch (e: any) { logAppError('chat:deleteConversation', e.message) }
}

async function startNewConversation() {
  const conv = await createConversation()
  if (conv) {
    activeConvId.value = conv.id
    activeRequestId.value = null
    messages.value = [WELCOME_MSG]
    nextId = 1
    input.value = ''
    isProcessing.value = false
    awaitingAction.value = false
    await fetchConversations()
    scrollToBottom()
  }
}

// --- Chat logic ---

function setProcessingStep(msgId: number, step: ProcessingStep) {
  const msg = messages.value.find(m => m.id === msgId)
  if (msg) msg.processingStep = step
}

function replaceProcessing(msgId: number, replacement: Message) {
  const idx = messages.value.findIndex(m => m.id === msgId)
  if (idx !== -1) messages.value[idx] = replacement
}

async function sendMessage() {
  const userText = input.value.trim()
  if (!userText || isProcessing.value) return

  if (!activeConvId.value) {
    const conv = await createConversation()
    if (!conv) return
    activeConvId.value = conv.id
    await fetchConversations()
  }

  input.value = ''
  messages.value.push({ id: nextId++, role: 'user', content: userText, type: 'text' })
  scrollToBottom()

  isProcessing.value = true
  const processingId = nextId++
  messages.value.push({ id: processingId, role: 'assistant', type: 'processing', processingStep: 'llm' })
  scrollToBottom()

  try {
    // ── Step 1: LLM ──
    const llmRes = await authFetch(`${API}/llm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: activeConvId.value, message: userText }),
    })

    if (!llmRes.ok) {
      const err = await llmRes.json().catch(() => ({ detail: 'Error desconocido' }))
      replaceProcessing(processingId, { id: processingId, role: 'assistant', content: `Error: ${err.detail}`, type: 'error' })
      isProcessing.value = false; scrollToBottom(); await saveMessages(); return
    }

    const llm = await llmRes.json()

    // If LLM needs more info or confirms existing match, we're done
    if (llm.action === 'question') {
      replaceProcessing(processingId, { id: processingId, role: 'assistant', content: llm.message, llm_content: llm.message, type: 'text' })
      isProcessing.value = false; scrollToBottom(); await saveMessages(); return
    }

    if (llm.action === 'existing_match') {
      // Patch the pending request if one exists
      if (activeRequestId.value) {
        await patchRequest(activeRequestId.value, { status: 'existing_match', material_id: llm.material_id || null })
        activeRequestId.value = null
      }
      replaceProcessing(processingId, { id: processingId, role: 'assistant', content: llm.message, llm_content: llm.message, type: 'existing_match' })
      isProcessing.value = false; scrollToBottom(); await saveMessages(); return
    }

    // action === 'proposal' → continue pipeline
    const shortText = llm.short_text
    const longText = llm.long_text
    const materialTypeId = llm.material_type_id
    const llmElapsed = llm.elapsed_s || 0

    // Create pending request in DB first (so we can stamp timestamps on it)
    let requestId: number | undefined
    try {
      const reqRes = await authFetch(`${API}/requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: activeConvId.value,
          short_text: shortText,
          long_text: longText,
          material_type_id: materialTypeId,
          llm_elapsed_s: llmElapsed,
        }),
      })
      if (reqRes.ok) {
        const reqData = await reqRes.json()
        requestId = reqData.request_id
        activeRequestId.value = requestId
      }
    } catch (e: any) { logAppError('chat:createRequest', e.message) }

    // ── Step 2: Duplicates ──
    setProcessingStep(processingId, 'duplicates')
    scrollToBottom()

    const dupRes = await authFetch(`${API}/duplicates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: activeConvId.value,
        short_text: shortText,
        request_id: requestId || null,
        user_message: userText,
        llm_raw: JSON.stringify(llm),
      }),
    })

    if (dupRes.ok) {
      const dupData = await dupRes.json()
      if (dupData.has_duplicates) {
        // Show duplicates review — stop pipeline here
        replaceProcessing(processingId, {
          id: processingId, role: 'assistant',
          content: dupData.message, llm_content: dupData.message,
          type: 'duplicates_review',
          proposal: { request_id: requestId, short_text: shortText, long_text: longText, material_type_id: materialTypeId, duplicates: dupData.duplicates },
        })
        isProcessing.value = false; awaitingAction.value = true; scrollToBottom(); await saveMessages(); return
      }
    }

    // ── Step 3: ML Prediction ──
    setProcessingStep(processingId, 'predict')
    scrollToBottom()

    let modelPrediction: ModelPrediction | undefined
    const predRes = await authFetch(`${API}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: activeConvId.value, request_id: requestId || null, short_text: shortText }),
    })

    if (predRes.ok) {
      const predData = await predRes.json()
      if (predData.prediction) modelPrediction = predData.prediction
    }

    // Show final proposal
    replaceProcessing(processingId, {
      id: processingId, role: 'assistant', type: 'proposal',
      llm_content: JSON.stringify(llm),
      proposal: {
        request_id: requestId, short_text: shortText, long_text: longText, material_type_id: materialTypeId,
        duplicates: [], model_prediction: modelPrediction,
        selected_class: modelPrediction ? { code: modelPrediction.top_k[0][0], name: modelPrediction.top_k[0][2] || '' } : undefined,
      },
    })

  } catch (e: any) {
    replaceProcessing(processingId, { id: processingId, role: 'assistant', content: `Error de conexion: ${e.message}`, type: 'error' })
  }

  isProcessing.value = false
  scrollToBottom()
  await saveMessages()
}

async function patchRequest(requestId: number, payload: Record<string, any>): Promise<boolean> {
  try {
    const res = await authFetch(`${API}/requests/${requestId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) logAppError('chat:patchRequest', `HTTP ${res.status}`, { requestId, payload })
    return res.ok
  } catch (e: any) { logAppError('chat:patchRequest', e.message, { requestId }); return false }
}

async function confirmProposal(msgId: number) {
  const msg = messages.value.find(m => m.id === msgId)
  if (!msg?.proposal || !activeConvId.value) return

  const proposal = msg.proposal
  const rid = proposal.request_id

  if (rid) {
    const ok = await patchRequest(rid, {
      short_text: proposal.short_text,
      long_text: proposal.long_text || null,
      material_type_id: proposal.material_type_id,
      class_code: proposal.selected_class?.code || null,
      category: proposal.model_prediction?.categoria || null,
      confidence: proposal.model_prediction?.confianza || null,
      alternatives: proposal.model_prediction?.top_k || null,
      duplicates: proposal.duplicates.length > 0 ? proposal.duplicates : null,
      status: 'confirmed',
    })

    if (!ok) {
      messages.value.push({ id: nextId++, role: 'assistant', content: 'Error al confirmar la solicitud.', type: 'error' })
      scrollToBottom(); return
    }
  }

  msg.type = 'confirmed'
  activeRequestId.value = null
  messages.value.push({
    id: nextId++, role: 'assistant',
    content: `Material confirmado y registrado${rid ? ` (solicitud #${rid})` : ''}. Podes seguir con otro material.`,
    type: 'text',
  })
  scrollToBottom()
  await saveMessages()
}

async function rejectProposal(msgId: number) {
  const msg = messages.value.find(m => m.id === msgId)
  if (!msg?.proposal) return

  if (msg.proposal.request_id) {
    await patchRequest(msg.proposal.request_id, { status: 'discarded' })
  }
  activeRequestId.value = null

  const idx = messages.value.findIndex(m => m.id === msgId)
  if (idx !== -1) messages.value.splice(idx, 1)

  messages.value.push({
    id: nextId++, role: 'assistant',
    content: 'Solicitud descartada. Podes intentar de nuevo con mas detalle o especificaciones diferentes.',
    type: 'text',
  })
  scrollToBottom()
  await saveMessages()
}

async function acceptDuplicate(msgId: number, dup: Duplicate) {
  const msg = messages.value.find(m => m.id === msgId)
  if (!msg?.proposal || !activeConvId.value) return
  awaitingAction.value = false

  try {
    await authFetch(`${API}/duplicates/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: activeConvId.value,
        request_id: msg.proposal.request_id || null,
        action: 'accepted',
        short_text: msg.proposal.short_text,
        selected_material_id: dup.material_id,
        duplicates: msg.proposal.duplicates,
      }),
    })
  } catch (e: any) { logAppError('chat:acceptDuplicate', e.message) }

  if (msg.proposal.request_id) {
    await patchRequest(msg.proposal.request_id, { status: 'existing_match', material_id: dup.material_id })
  }

  msg.type = 'existing_match'
  msg.content = `Material existente seleccionado: ${dup.short_text} (${dup.material_id})`
  activeRequestId.value = null

  messages.value.push({
    id: nextId++, role: 'assistant',
    content: `Se selecciono el material existente ${dup.material_id}. Si necesitas dar de alta otro material, seguimos.`,
    type: 'text',
  })
  scrollToBottom()
  await saveMessages()
}

async function rejectDuplicates(msgId: number) {
  const msg = messages.value.find(m => m.id === msgId)
  if (!msg?.proposal || !activeConvId.value) return
  awaitingAction.value = false

  const proposal = msg.proposal

  try {
    await authFetch(`${API}/duplicates/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: activeConvId.value,
        request_id: proposal.request_id || null,
        action: 'rejected',
        short_text: proposal.short_text,
        duplicates: proposal.duplicates,
      }),
    })
  } catch (e: any) { logAppError('chat:rejectDuplicates', e.message) }

  // Continue pipeline — run ML prediction
  isProcessing.value = true
  msg.type = 'processing'
  msg.processingStep = 'predict'
  msg.content = undefined
  scrollToBottom()

  let modelPrediction: ModelPrediction | undefined
  try {
    const predRes = await authFetch(`${API}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: activeConvId.value, request_id: proposal.request_id || null, short_text: proposal.short_text }),
    })
    if (predRes.ok) {
      const predData = await predRes.json()
      if (predData.prediction) modelPrediction = predData.prediction
    } else {
      logAppError('chat:rejectDuplicates:predict', `HTTP ${predRes.status}`)
    }
  } catch (e: any) { logAppError('chat:rejectDuplicates:predict', e.message) }

  // Show proposal with prediction
  const replacement: Message = {
    id: msg.id, role: 'assistant', type: 'proposal',
    proposal: {
      ...proposal,
      model_prediction: modelPrediction,
      selected_class: modelPrediction
        ? { code: modelPrediction.top_k[0][0], name: modelPrediction.top_k[0][2] || '' }
        : undefined,
    },
  }
  const idx = messages.value.findIndex(m => m.id === msgId)
  if (idx !== -1) messages.value[idx] = replacement

  isProcessing.value = false
  scrollToBottom()
  await saveMessages()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// --- Init ---

onMounted(async () => {
  await fetchConversations()
  if (conversations.value.length > 0) {
    await loadConversation(conversations.value[0].id)
  } else {
    await startNewConversation()
  }
})
</script>

<template>
  <section class="h-[calc(100vh-4.0625rem)] flex overflow-hidden">

    <!-- Sidebar -->
    <aside class="hidden lg:flex w-64 border-r flex-col bg-muted/30 shrink-0">
      <div class="h-12 border-b flex items-center px-4">
        <h2 class="font-semibold text-sm flex items-center gap-2">
          <i class="fa-solid fa-clock-rotate-left text-muted-foreground"></i>
          Historial
        </h2>
      </div>
      <div class="flex-1 p-3 space-y-1 overflow-y-auto">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="w-full text-left px-3 py-2 rounded-md text-sm flex items-center gap-2 group transition-colors cursor-pointer"
          :class="conv.id === activeConvId ? 'bg-primary/10 font-medium' : 'hover:bg-muted'"
          @click="loadConversation(conv.id)"
        >
          <i class="fa-solid fa-message text-xs shrink-0" :class="conv.id === activeConvId ? 'text-primary' : 'text-muted-foreground'"></i>
          <span class="truncate flex-1">{{ conv.title }}</span>
          <button
            class="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity shrink-0"
            @click.stop="deleteConversation(conv.id)"
          >
            <i class="fa-solid fa-trash text-xs"></i>
          </button>
        </div>
        <p v-if="conversations.length === 0" class="text-xs text-muted-foreground text-center py-4">Sin conversaciones</p>
      </div>
      <div class="p-3 border-t">
        <Button variant="ghost" class="w-full justify-start gap-2 text-sm" @click="startNewConversation">
          <i class="fa-solid fa-plus"></i>
          Nueva conversacion
        </Button>
      </div>
    </aside>

    <!-- Chat principal -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">

      <!-- Header -->
      <div class="h-12 border-b flex items-center justify-between px-4 shrink-0">
        <div class="flex items-center gap-2 text-sm">
          <div class="w-2 h-2 rounded-full bg-green-500"></div>
          <span class="text-muted-foreground">GAMMA Asistente</span>
        </div>
        <Button variant="ghost" size="sm" class="lg:hidden" @click="startNewConversation">
          <i class="fa-solid fa-plus"></i>
        </Button>
      </div>

      <!-- Mensajes -->
      <div ref="scrollRef" class="flex-1 overflow-y-auto min-h-0">
        <div class="max-w-3xl mx-auto py-6 px-4 space-y-6">
          <template v-for="msg in messages" :key="msg.id">

            <!-- Mensaje de texto -->
            <div v-if="msg.type === 'text'" class="flex gap-3" :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
              <Avatar class="w-8 h-8 shrink-0">
                <AvatarFallback :class="msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'">
                  <i :class="msg.role === 'user' ? 'fa-solid fa-user' : 'fa-solid fa-robot'" class="text-xs"></i>
                </AvatarFallback>
              </Avatar>
              <div class="max-w-[80%] group/msg">
                <div
                  class="px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-line"
                  :class="msg.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-tr-sm'
                    : 'bg-muted rounded-tl-sm'"
                >
                  {{ msg.content }}
                </div>
                <button
                  v-if="msg.role === 'assistant' && msg.content"
                  class="mt-1 text-xs text-muted-foreground hover:text-foreground transition-colors opacity-0 group-hover/msg:opacity-100 flex items-center gap-1"
                  @click="copyToClipboard(msg.id, msg.content!)"
                >
                  <i :class="copiedId === msg.id ? 'fa-solid fa-check text-green-500' : 'fa-regular fa-copy'" class="text-xs"></i>
                  {{ copiedId === msg.id ? 'Copiado' : 'Copiar' }}
                </button>
              </div>
            </div>

            <!-- Error -->
            <div v-if="msg.type === 'error'" class="flex gap-3">
              <Avatar class="w-8 h-8 shrink-0">
                <AvatarFallback class="bg-red-500/10">
                  <i class="fa-solid fa-triangle-exclamation text-xs text-red-500"></i>
                </AvatarFallback>
              </Avatar>
              <div class="max-w-[80%] px-4 py-3 rounded-2xl rounded-tl-sm bg-red-500/10 border border-red-500/20 text-sm text-red-600 dark:text-red-400">
                {{ msg.content }}
              </div>
            </div>

            <!-- Processing -->
            <div v-if="msg.type === 'processing'" class="flex gap-3">
              <Avatar class="w-8 h-8 shrink-0">
                <AvatarFallback class="bg-muted">
                  <i class="fa-solid fa-robot text-xs"></i>
                </AvatarFallback>
              </Avatar>
              <div class="bg-muted rounded-2xl rounded-tl-sm px-4 py-3">
                <div class="flex items-center gap-3 text-sm text-muted-foreground mb-2">
                  <div class="flex gap-1">
                    <span class="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:0ms]"></span>
                    <span class="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:150ms]"></span>
                    <span class="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:300ms]"></span>
                  </div>
                  <span>{{
                    msg.processingStep === 'llm' ? 'Generando descripcion...' :
                    msg.processingStep === 'duplicates' ? 'Buscando duplicados...' :
                    'Clasificando material...'
                  }}</span>
                </div>
                <div class="flex gap-2">
                  <Badge
                    :variant="msg.processingStep === 'llm' ? 'default' : 'outline'"
                    class="text-xs gap-1 transition-all"
                    :class="msg.processingStep === 'llm' ? '' : (msg.processingStep === 'duplicates' || msg.processingStep === 'predict' ? 'opacity-50' : 'opacity-30')"
                  >
                    <i class="fa-solid fa-pen-nib" :class="msg.processingStep === 'llm' ? 'animate-pulse' : ''"></i> Descripcion
                  </Badge>
                  <Badge
                    :variant="msg.processingStep === 'duplicates' ? 'default' : 'outline'"
                    class="text-xs gap-1 transition-all"
                    :class="msg.processingStep === 'duplicates' ? '' : (msg.processingStep === 'predict' ? 'opacity-50' : 'opacity-30')"
                  >
                    <i class="fa-solid fa-magnifying-glass" :class="msg.processingStep === 'duplicates' ? 'animate-pulse' : ''"></i> Duplicados
                  </Badge>
                  <Badge
                    :variant="msg.processingStep === 'predict' ? 'default' : 'outline'"
                    class="text-xs gap-1 transition-all"
                    :class="msg.processingStep === 'predict' ? '' : 'opacity-30'"
                  >
                    <i class="fa-solid fa-brain" :class="msg.processingStep === 'predict' ? 'animate-pulse' : ''"></i> Clasificacion
                  </Badge>
                </div>
              </div>
            </div>

            <!-- Propuesta -->
            <div v-if="msg.type === 'proposal' && msg.proposal" class="flex gap-3">
              <Avatar class="w-8 h-8 shrink-0">
                <AvatarFallback class="bg-muted">
                  <i class="fa-solid fa-robot text-xs"></i>
                </AvatarFallback>
              </Avatar>
              <Card class="w-full max-w-2xl overflow-hidden">
                <CardContent class="p-0">
                  <div class="px-4 py-3 bg-muted/50 border-b flex items-center gap-2">
                    <i class="fa-solid fa-clipboard-check text-primary"></i>
                    <span class="text-sm font-medium">Propuesta de material</span>
                  </div>

                  <div class="p-4 space-y-4">
                    <div>
                      <p class="text-xs text-muted-foreground mb-1">Descripcion corta (SAP) <span class="text-[10px]">— max 40 caracteres</span></p>
                      <input
                        type="text"
                        :value="msg.proposal.short_text"
                        @input="msg.proposal!.short_text = ($event.target as HTMLInputElement).value"
                        maxlength="40"
                        class="w-full text-sm font-mono bg-muted/50 px-3 py-2 rounded-md border border-transparent focus:border-border focus:outline-none focus:ring-2 focus:ring-ring"
                      />
                    </div>

                    <div>
                      <p class="text-xs text-muted-foreground mb-1">Descripcion larga</p>
                      <textarea
                        :value="msg.proposal.long_text || ''"
                        @input="msg.proposal!.long_text = ($event.target as HTMLTextAreaElement).value"
                        rows="3"
                        class="w-full text-sm bg-muted/50 px-3 py-2 rounded-md border border-transparent focus:border-border focus:outline-none focus:ring-2 focus:ring-ring resize-y leading-relaxed"
                      ></textarea>
                    </div>

                    <div>
                      <p class="text-xs text-muted-foreground mb-1">Tipo de material (LLM)</p>
                      <Badge class="bg-amber-500/10 text-amber-600 hover:bg-amber-500/10">{{ msg.proposal.material_type_id }}</Badge>
                    </div>

                    <template v-if="msg.proposal.model_prediction">
                      <Separator />
                      <div>
                        <p class="text-xs text-muted-foreground mb-2">
                          <i class="fa-solid fa-brain text-violet-500 mr-1"></i>
                          Clasificacion
                          <span v-if="msg.proposal.selected_class" class="text-foreground font-medium ml-1">
                            — {{ msg.proposal.selected_class.code }}
                            <span v-if="msg.proposal.selected_class.name" class="font-normal"> ({{ msg.proposal.selected_class.name }})</span>
                          </span>
                        </p>
                        <div class="space-y-1.5">
                          <div
                            v-for="(pred, i) in msg.proposal.model_prediction.top_k"
                            :key="i"
                            class="flex items-center justify-between px-3 py-1.5 rounded-md text-sm cursor-pointer transition-all"
                            :class="msg.proposal.selected_class?.code === pred[0]
                              ? 'bg-violet-500/15 border border-violet-500/30 font-medium ring-1 ring-violet-500/20'
                              : 'bg-muted/50 hover:bg-muted'"
                            @click="selectClass(msg.id, pred[0], pred[2] || '')"
                          >
                            <div class="flex items-center gap-2">
                              <i
                                class="text-xs"
                                :class="msg.proposal.selected_class?.code === pred[0]
                                  ? 'fa-solid fa-circle-check text-violet-500'
                                  : 'fa-regular fa-circle text-muted-foreground'"
                              ></i>
                              <div class="flex flex-col">
                                <span class="font-mono text-xs">{{ pred[0] }}</span>
                                <span v-if="pred[2]" class="text-[10px] text-muted-foreground">{{ pred[2] }}</span>
                              </div>
                            </div>
                            <Badge variant="outline" class="text-xs ml-2 shrink-0">{{ (pred[1] * 100).toFixed(0) }}%</Badge>
                          </div>

                          <!-- Otros -->
                          <div class="mt-1">
                            <button
                              class="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm w-full transition-all"
                              :class="classSearchOpen === msg.id
                                ? 'bg-muted border border-border'
                                : (msg.proposal.selected_class && !msg.proposal.model_prediction.top_k.some((p: any) => p[0] === msg.proposal!.selected_class!.code))
                                  ? 'bg-violet-500/15 border border-violet-500/30 font-medium'
                                  : 'bg-muted/50 hover:bg-muted'"
                              @click="toggleClassSearch(msg.id)"
                            >
                              <i class="fa-solid fa-ellipsis text-xs text-muted-foreground"></i>
                              <span class="text-xs">
                                <template v-if="msg.proposal.selected_class && !msg.proposal.model_prediction.top_k.some((p: any) => p[0] === msg.proposal!.selected_class!.code)">
                                  {{ msg.proposal.selected_class.code }} — {{ msg.proposal.selected_class.name }}
                                </template>
                                <template v-else>Otra clase...</template>
                              </span>
                            </button>
                            <div v-if="classSearchOpen === msg.id" class="mt-2 space-y-2">
                              <input
                                type="text"
                                :value="classSearchQuery"
                                @input="onClassSearch(($event.target as HTMLInputElement).value)"
                                placeholder="Buscar por codigo o nombre..."
                                class="w-full text-sm px-3 py-2 rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                              />
                              <div v-if="classSearchResults.length" class="max-h-40 overflow-y-auto space-y-1">
                                <div
                                  v-for="cls in classSearchResults"
                                  :key="cls.code"
                                  class="flex items-center justify-between px-3 py-1.5 rounded-md text-sm cursor-pointer hover:bg-muted transition-colors"
                                  @click="selectClass(msg.id, cls.code, cls.name)"
                                >
                                  <div class="flex flex-col">
                                    <span class="font-mono text-xs">{{ cls.code }}</span>
                                    <span class="text-[10px] text-muted-foreground">{{ cls.name }}</span>
                                  </div>
                                </div>
                              </div>
                              <p v-else-if="classSearchQuery.length > 0" class="text-xs text-muted-foreground text-center py-2">Sin resultados</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </template>

                    <template v-if="msg.proposal.duplicates.length > 0">
                      <Separator />

                      <div>
                        <p class="text-xs text-muted-foreground mb-2">
                          <i class="fa-solid fa-triangle-exclamation text-amber-500 mr-1"></i>
                          Posibles duplicados encontrados
                        </p>
                        <div class="space-y-2">
                          <div
                            v-for="dup in msg.proposal.duplicates"
                            :key="dup.material_id"
                            class="flex items-center justify-between px-3 py-2 rounded-md bg-muted/50 text-sm"
                          >
                            <div class="flex flex-col">
                              <span class="font-mono text-xs">{{ dup.short_text }}</span>
                              <span class="text-[10px] text-muted-foreground">{{ dup.material_id }}</span>
                            </div>
                            <Badge variant="outline" class="text-xs ml-2 shrink-0">{{ (dup.similarity * 100).toFixed(0) }}%</Badge>
                          </div>
                        </div>
                      </div>
                    </template>
                  </div>

                  <div class="px-4 py-3 border-t bg-muted/30 flex gap-2 justify-end">
                    <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive gap-1" @click="rejectProposal(msg.id)">
                      <i class="fa-solid fa-xmark"></i>
                      Descartar
                    </Button>
                    <Button size="sm" class="gap-1" @click="confirmProposal(msg.id)">
                      <i class="fa-solid fa-check"></i>
                      Confirmar
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            <!-- Duplicates review -->
            <div v-if="msg.type === 'duplicates_review'" class="flex gap-3">
              <Avatar class="w-8 h-8 shrink-0">
                <AvatarFallback class="bg-muted">
                  <i class="fa-solid fa-robot text-xs"></i>
                </AvatarFallback>
              </Avatar>
              <Card class="w-full max-w-2xl overflow-hidden">
                <CardContent class="p-0">
                  <div class="px-4 py-3 bg-amber-500/10 border-b flex items-center gap-2">
                    <i class="fa-solid fa-triangle-exclamation text-amber-500"></i>
                    <span class="text-sm font-medium">Posibles duplicados encontrados</span>
                  </div>

                  <div class="p-4 space-y-3">
                    <div v-if="msg.content" class="text-sm leading-relaxed whitespace-pre-line text-muted-foreground">
                      {{ msg.content }}
                    </div>

                    <div v-if="msg.proposal?.duplicates?.length" class="space-y-2">
                      <div
                        v-for="dup in msg.proposal.duplicates"
                        :key="dup.material_id"
                        class="flex items-center justify-between px-3 py-2 rounded-md border bg-amber-500/5 border-amber-500/20 text-sm cursor-pointer hover:bg-amber-500/10 transition-colors"
                        @click="acceptDuplicate(msg.id, dup)"
                      >
                        <div class="flex flex-col">
                          <span class="font-mono text-xs">{{ dup.short_text }}</span>
                          <span class="text-[10px] text-muted-foreground">ID: {{ dup.material_id }}</span>
                        </div>
                        <div class="flex items-center gap-2 shrink-0">
                          <Badge variant="outline" class="text-xs">{{ (dup.similarity * 100).toFixed(0) }}%</Badge>
                          <i class="fa-solid fa-arrow-right text-xs text-muted-foreground"></i>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="px-4 py-3 border-t bg-muted/30 flex gap-2 justify-between items-center">
                    <p class="text-xs text-muted-foreground">Selecciona un duplicado o continua con material nuevo</p>
                    <Button size="sm" variant="outline" class="gap-1 shrink-0" @click="rejectDuplicates(msg.id)">
                      <i class="fa-solid fa-arrow-right text-xs"></i>
                      Ninguno, continuar
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            <!-- Confirmado -->
            <div v-if="msg.type === 'confirmed' && msg.proposal" class="flex gap-3">
              <Avatar class="w-8 h-8 shrink-0">
                <AvatarFallback class="bg-muted">
                  <i class="fa-solid fa-robot text-xs"></i>
                </AvatarFallback>
              </Avatar>
              <Card class="max-w-[90%] overflow-hidden border-green-500/20">
                <CardContent class="p-0">
                  <div
                    class="px-4 py-3 bg-green-500/10 flex items-center justify-between cursor-pointer"
                    @click="expandedConfirmed.has(msg.id) ? expandedConfirmed.delete(msg.id) : expandedConfirmed.add(msg.id)"
                  >
                    <div class="flex items-center gap-2 text-sm text-green-600 dark:text-green-400 font-medium">
                      <i class="fa-solid fa-circle-check"></i>
                      Material confirmado
                    </div>
                    <i
                      class="fa-solid text-xs text-muted-foreground transition-transform"
                      :class="expandedConfirmed.has(msg.id) ? 'fa-chevron-up' : 'fa-chevron-down'"
                    ></i>
                  </div>

                  <div class="px-4 py-2 flex items-center gap-2 flex-wrap">
                    <p class="text-xs font-mono text-muted-foreground">{{ msg.proposal.short_text }}</p>
                    <Badge class="text-xs bg-amber-500/10 text-amber-600 hover:bg-amber-500/10 shrink-0">{{ msg.proposal.material_type_id }}</Badge>
                    <Badge v-if="msg.proposal.selected_class" class="text-xs bg-violet-500/10 text-violet-600 hover:bg-violet-500/10 shrink-0">
                      {{ msg.proposal.selected_class.code }} — {{ msg.proposal.selected_class.name }}
                    </Badge>
                  </div>

                  <div v-if="expandedConfirmed.has(msg.id)" class="px-4 pb-4 space-y-3 border-t pt-3">
                    <div v-if="msg.proposal.long_text">
                      <p class="text-xs text-muted-foreground mb-1">Descripcion larga</p>
                      <p class="text-sm bg-muted/50 px-3 py-2 rounded-md leading-relaxed">{{ msg.proposal.long_text }}</p>
                    </div>
                    <template v-if="msg.proposal.model_prediction">
                      <div>
                        <p class="text-xs text-muted-foreground mb-2">
                          <i class="fa-solid fa-brain text-violet-500 mr-1"></i>
                          Clasificacion del modelo ML
                        </p>
                        <div class="space-y-1.5">
                          <div
                            v-for="(pred, i) in msg.proposal.model_prediction.top_k"
                            :key="i"
                            class="flex items-center justify-between px-3 py-1.5 rounded-md text-sm"
                            :class="msg.proposal.selected_class?.code === pred[0]
                              ? 'bg-violet-500/15 border border-violet-500/30 font-medium'
                              : 'bg-muted/50'"
                          >
                            <div class="flex items-center gap-2">
                              <i
                                class="text-xs"
                                :class="msg.proposal.selected_class?.code === pred[0]
                                  ? 'fa-solid fa-circle-check text-violet-500'
                                  : 'fa-regular fa-circle text-muted-foreground'"
                              ></i>
                              <div class="flex flex-col">
                                <span class="font-mono text-xs">{{ pred[0] }}</span>
                                <span v-if="pred[2]" class="text-[10px] text-muted-foreground">{{ pred[2] }}</span>
                              </div>
                            </div>
                            <Badge variant="outline" class="text-xs ml-2 shrink-0">{{ (pred[1] * 100).toFixed(0) }}%</Badge>
                          </div>
                        </div>
                      </div>
                    </template>
                  </div>
                </CardContent>
              </Card>
            </div>

            <!-- Existing match -->
            <div v-if="msg.type === 'existing_match'" class="flex gap-3">
              <Avatar class="w-8 h-8 shrink-0">
                <AvatarFallback class="bg-muted">
                  <i class="fa-solid fa-robot text-xs"></i>
                </AvatarFallback>
              </Avatar>
              <div class="max-w-[90%] px-4 py-3 rounded-2xl rounded-tl-sm bg-blue-500/10 border border-blue-500/20">
                <div class="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 font-medium mb-1">
                  <i class="fa-solid fa-link"></i>
                  Material existente
                </div>
                <p class="text-xs text-muted-foreground">{{ msg.content }}</p>
              </div>
            </div>

          </template>
        </div>
      </div>

      <!-- Input -->
      <div class="border-t p-4 shrink-0">
        <div class="max-w-3xl mx-auto">
          <div class="flex gap-2">
            <div class="flex-1 relative">
              <textarea
                v-model="input"
                @keydown="handleKeydown"
                :placeholder="awaitingAction ? 'Selecciona una opcion arriba para continuar...' : 'Describe el material que queres dar de alta...'"
                class="w-full resize-none rounded-xl border bg-background px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[48px] max-h-[120px]"
                rows="1"
                :disabled="isProcessing || awaitingAction"
              ></textarea>
              <Button
                size="sm"
                class="absolute right-2 bottom-2 h-8 w-8 p-0 rounded-lg"
                :disabled="!input.trim() || isProcessing || awaitingAction"
                @click="sendMessage"
              >
                <i class="fa-solid fa-arrow-up text-xs"></i>
              </Button>
            </div>
          </div>
          <p class="text-xs text-muted-foreground mt-2 text-center">
            GAMMA procesa cada solicitud con tres servicios: duplicados, descripcion y categorizacion.
          </p>
        </div>
      </div>
    </div>
  </section>
</template>

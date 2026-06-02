<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { API_BASE } from '@/config'
import { authFetch } from '@/composables/useAuth'

const API = `${API_BASE}/api/chat`

interface Duplicate {
  material_id: string
  short_text: string
  similarity: number
}

interface Proposal {
  short_text: string
  material_type_id: string
  confidence: number
  duplicates: Duplicate[]
}

interface Message {
  id: number
  role: 'user' | 'assistant'
  content?: string
  llm_content?: string
  type: 'text' | 'processing' | 'proposal' | 'confirmed' | 'error' | 'duplicates_review' | 'existing_match'
  proposal?: Proposal
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
const scrollRef = ref<InstanceType<typeof ScrollArea> | null>(null)

const conversations = ref<ConversationSummary[]>([])
const activeConvId = ref<string | null>(null)
let nextId = 1

function scrollToBottom() {
  nextTick(() => {
    const viewport = scrollRef.value?.$el?.querySelector('[data-radix-scroll-area-viewport]')
    if (viewport) viewport.scrollTop = viewport.scrollHeight
  })
}

// --- API helpers ---

async function fetchConversations() {
  try {
    const res = await authFetch(`${API}/conversations`)
    if (res.ok) conversations.value = await res.json()
  } catch { /* silently fail */ }
}

async function createConversation(): Promise<Conversation | null> {
  try {
    const res = await authFetch(`${API}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Nueva conversacion' }),
    })
    if (res.ok) return await res.json()
  } catch { /* silently fail */ }
  return null
}

async function saveMessages() {
  if (!activeConvId.value) return
  const saveable = messages.value.filter(m => m.type !== 'processing')
  try {
    const firstUser = saveable.find(m => m.role === 'user')
    const title = firstUser?.content?.slice(0, 60) || 'Nueva conversacion'

    await authFetch(`${API}/conversations/${activeConvId.value}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: saveable, title }),
    })
    await fetchConversations()
  } catch { /* silently fail */ }
}

async function loadConversation(id: string) {
  try {
    const res = await authFetch(`${API}/conversations/${id}`)
    if (res.ok) {
      const conv: Conversation = await res.json()
      activeConvId.value = conv.id
      messages.value = conv.messages.length > 0 ? conv.messages : [WELCOME_MSG]
      nextId = Math.max(...messages.value.map(m => m.id), 0) + 1
      scrollToBottom()
    }
  } catch { /* silently fail */ }
}

async function deleteConversation(id: string) {
  try {
    await authFetch(`${API}/conversations/${id}`, { method: 'DELETE' })
    if (activeConvId.value === id) {
      await startNewConversation()
    }
    await fetchConversations()
  } catch { /* silently fail */ }
}

async function startNewConversation() {
  const conv = await createConversation()
  if (conv) {
    activeConvId.value = conv.id
    messages.value = [WELCOME_MSG]
    nextId = 1
    input.value = ''
    isProcessing.value = false
    await fetchConversations()
    scrollToBottom()
  }
}

// --- Chat logic ---

async function sendMessage() {
  const text = input.value.trim()
  if (!text || isProcessing.value) return

  // Si no hay conversación activa, crear una
  if (!activeConvId.value) {
    const conv = await createConversation()
    if (!conv) return
    activeConvId.value = conv.id
    await fetchConversations()
  }

  input.value = ''
  messages.value.push({ id: nextId++, role: 'user', content: text, type: 'text' })
  scrollToBottom()

  isProcessing.value = true

  const processingId = nextId++
  messages.value.push({ id: processingId, role: 'assistant', type: 'processing' })
  scrollToBottom()

  try {
    const res = await authFetch(`${API}/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: activeConvId.value, message: text }),
    })

    const idx = messages.value.findIndex(m => m.id === processingId)

    if (res.ok) {
      const data = await res.json()

      if (data.action === 'proposal') {
        if (idx !== -1) {
          messages.value[idx] = {
            id: processingId,
            role: 'assistant',
            type: 'proposal',
            llm_content: JSON.stringify(data),
            proposal: {
              short_text: data.short_text,
              material_type_id: data.material_type_id,
              confidence: data.confidence,
              duplicates: data.duplicates || [],
            },
          }
        }
      } else if (data.action === 'duplicates_review') {
        // LLM found duplicates and is presenting them conversationally
        if (idx !== -1) {
          messages.value[idx] = {
            id: processingId,
            role: 'assistant',
            content: data.message,
            llm_content: data.message,
            type: 'duplicates_review',
            proposal: {
              short_text: data.short_text,
              material_type_id: data.material_type_id,
              confidence: data.confidence,
              duplicates: data.duplicates || [],
            },
          }
        }
      } else if (data.action === 'existing_match') {
        if (idx !== -1) {
          messages.value[idx] = {
            id: processingId,
            role: 'assistant',
            content: data.message,
            llm_content: data.message,
            type: 'existing_match',
          }
        }
      } else {
        // question or other text response
        if (idx !== -1) {
          messages.value[idx] = {
            id: processingId,
            role: 'assistant',
            content: data.message,
            llm_content: data.message,
            type: 'text',
          }
        }
      }
    } else {
      const err = await res.json().catch(() => ({ detail: 'Error desconocido' }))
      if (idx !== -1) {
        messages.value[idx] = {
          id: processingId,
          role: 'assistant',
          content: `Error: ${err.detail}`,
          type: 'error',
        }
      }
    }
  } catch (e: any) {
    const idx = messages.value.findIndex(m => m.id === processingId)
    if (idx !== -1) {
      messages.value[idx] = {
        id: processingId,
        role: 'assistant',
        content: `Error de conexion: ${e.message}`,
        type: 'error',
      }
    }
  }

  isProcessing.value = false
  scrollToBottom()
  await saveMessages()
}

function confirmProposal(msgId: number) {
  const idx = messages.value.findIndex(m => m.id === msgId)
  if (idx !== -1) {
    messages.value[idx].type = 'confirmed'
  }
  messages.value.push({
    id: nextId++,
    role: 'assistant',
    content: 'Material confirmado y registrado. Podes exportarlo a Excel desde el historial o seguir con otro material.',
    type: 'text',
  })
  scrollToBottom()
  saveMessages()
}

function rejectProposal(msgId: number) {
  const idx = messages.value.findIndex(m => m.id === msgId)
  if (idx !== -1) {
    messages.value.splice(idx, 1)
  }
  messages.value.push({
    id: nextId++,
    role: 'assistant',
    content: 'Entendido, descarte la propuesta. Podes intentar de nuevo con mas detalle o especificaciones diferentes.',
    type: 'text',
  })
  scrollToBottom()
  saveMessages()
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
  <section class="h-[calc(100vh-4.0625rem)] flex">

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
    <div class="flex-1 flex flex-col min-w-0">

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
      <ScrollArea ref="scrollRef" class="flex-1">
        <div class="max-w-3xl mx-auto py-6 px-4 space-y-6">
          <template v-for="msg in messages" :key="msg.id">

            <!-- Mensaje de texto -->
            <div v-if="msg.type === 'text'" class="flex gap-3" :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
              <Avatar class="w-8 h-8 shrink-0">
                <AvatarFallback :class="msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'">
                  <i :class="msg.role === 'user' ? 'fa-solid fa-user' : 'fa-solid fa-robot'" class="text-xs"></i>
                </AvatarFallback>
              </Avatar>
              <div
                class="max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed"
                :class="msg.role === 'user'
                  ? 'bg-primary text-primary-foreground rounded-tr-sm'
                  : 'bg-muted rounded-tl-sm'"
              >
                {{ msg.content }}
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
                <div class="flex items-center gap-3 text-sm text-muted-foreground">
                  <div class="flex gap-1">
                    <span class="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:0ms]"></span>
                    <span class="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:150ms]"></span>
                    <span class="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:300ms]"></span>
                  </div>
                  <span>Procesando solicitud...</span>
                </div>
                <div class="flex gap-2 mt-2">
                  <Badge variant="outline" class="text-xs gap-1">
                    <i class="fa-solid fa-magnifying-glass text-blue-500"></i> Duplicados
                  </Badge>
                  <Badge variant="outline" class="text-xs gap-1">
                    <i class="fa-solid fa-pen-nib text-violet-500"></i> Descripcion
                  </Badge>
                  <Badge variant="outline" class="text-xs gap-1">
                    <i class="fa-solid fa-tags text-amber-500"></i> Categoria
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
              <Card class="max-w-[90%] overflow-hidden">
                <CardContent class="p-0">
                  <div class="px-4 py-3 bg-muted/50 border-b flex items-center gap-2">
                    <i class="fa-solid fa-clipboard-check text-primary"></i>
                    <span class="text-sm font-medium">Propuesta de material</span>
                  </div>

                  <div class="p-4 space-y-4">
                    <div>
                      <p class="text-xs text-muted-foreground mb-1">Descripcion corta (SAP)</p>
                      <p class="text-sm font-mono bg-muted/50 px-3 py-2 rounded-md">{{ msg.proposal.short_text }}</p>
                    </div>

                    <div>
                      <p class="text-xs text-muted-foreground mb-1">Tipo de material</p>
                      <div class="flex items-center gap-2">
                        <Badge class="bg-amber-500/10 text-amber-600 hover:bg-amber-500/10">{{ msg.proposal.material_type_id }}</Badge>
                        <span class="text-xs text-muted-foreground">{{ (msg.proposal.confidence * 100).toFixed(0) }}% confianza</span>
                      </div>
                    </div>

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
              <div class="max-w-[90%] space-y-3">
                <div class="px-4 py-3 rounded-2xl rounded-tl-sm bg-muted text-sm leading-relaxed">
                  {{ msg.content }}
                </div>
                <div v-if="msg.proposal?.duplicates?.length" class="space-y-2 pl-1">
                  <div
                    v-for="dup in msg.proposal.duplicates"
                    :key="dup.material_id"
                    class="flex items-center justify-between px-3 py-2 rounded-md border bg-amber-500/5 border-amber-500/20 text-sm"
                  >
                    <div class="flex flex-col">
                      <span class="font-mono text-xs">{{ dup.short_text }}</span>
                      <span class="text-[10px] text-muted-foreground">ID: {{ dup.material_id }}</span>
                    </div>
                    <Badge variant="outline" class="text-xs ml-2 shrink-0">{{ (dup.similarity * 100).toFixed(0) }}%</Badge>
                  </div>
                </div>
              </div>
            </div>

            <!-- Confirmado -->
            <div v-if="msg.type === 'confirmed' && msg.proposal" class="flex gap-3">
              <Avatar class="w-8 h-8 shrink-0">
                <AvatarFallback class="bg-muted">
                  <i class="fa-solid fa-robot text-xs"></i>
                </AvatarFallback>
              </Avatar>
              <div class="max-w-[90%] px-4 py-3 rounded-2xl rounded-tl-sm bg-green-500/10 border border-green-500/20">
                <div class="flex items-center gap-2 text-sm text-green-600 dark:text-green-400 font-medium mb-1">
                  <i class="fa-solid fa-circle-check"></i>
                  Material confirmado
                </div>
                <p class="text-xs font-mono text-muted-foreground">{{ msg.proposal.short_text }}</p>
                <Badge class="mt-1 text-xs bg-amber-500/10 text-amber-600 hover:bg-amber-500/10">{{ msg.proposal.material_type_id }}</Badge>
              </div>
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
      </ScrollArea>

      <!-- Input -->
      <div class="border-t p-4 shrink-0">
        <div class="max-w-3xl mx-auto">
          <div class="flex gap-2">
            <div class="flex-1 relative">
              <textarea
                v-model="input"
                @keydown="handleKeydown"
                placeholder="Describe el material que queres dar de alta..."
                class="w-full resize-none rounded-xl border bg-background px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[48px] max-h-[120px]"
                rows="1"
                :disabled="isProcessing"
              ></textarea>
              <Button
                size="sm"
                class="absolute right-2 bottom-2 h-8 w-8 p-0 rounded-lg"
                :disabled="!input.trim() || isProcessing"
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

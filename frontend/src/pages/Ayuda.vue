<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { API_BASE } from '@/config'
import { authFetch } from '@/composables/useAuth'

interface ManualItem {
  slug: string
  titulo: string
  descripcion: string
  solo_admin: boolean
  disponible: boolean
  size_bytes: number | null
}

// El API entrega solo los manuales que el rol permite: a un gestor ni siquiera
// le llegan los restringidos.
const manuales = ref<ManualItem[]>([])
const cargandoManuales = ref(true)
const descargando = ref<string | null>(null)
const errorManual = ref<string | null>(null)

async function cargarManuales() {
  try {
    const r = await authFetch(`${API_BASE}/api/manuales`)
    if (r.ok) manuales.value = await r.json()
  } catch {
    // Sin conexion la seccion queda vacia; el resto de la ayuda sigue sirviendo.
  } finally {
    cargandoManuales.value = false
  }
}

// La descarga pasa por el API y necesita el token, asi que no puede ser un
// enlace directo: se pide el archivo y se entrega al navegador como blob.
async function descargar(m: ManualItem) {
  descargando.value = m.slug
  errorManual.value = null
  try {
    const r = await authFetch(`${API_BASE}/api/manuales/${m.slug}`)
    if (!r.ok) throw new Error('No se pudo descargar el manual')
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `GAMMA - ${m.titulo}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch (e: unknown) {
    errorManual.value = e instanceof Error ? e.message : 'Error de conexion'
  } finally {
    descargando.value = null
  }
}

function mb(bytes: number | null): string {
  if (!bytes) return ''
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

onMounted(cargarManuales)

// Flujo real de una solicitud, tal como lo implementa el asistente.
const pasos = [
  {
    n: 1,
    icono: 'fa-solid fa-comment-dots',
    titulo: 'Describa el material',
    texto: 'Escriba en lenguaje natural lo que necesita dar de alta. No hace falta usar abreviaturas ni el formato de SAP: el asistente se encarga de normalizarlo.',
  },
  {
    n: 2,
    icono: 'fa-solid fa-list-check',
    titulo: 'Complete lo que falte',
    texto: 'Si la descripcion es insuficiente, el asistente responde con la lista puntual de datos pendientes. Nunca inventa una especificacion que usted no haya dado.',
  },
  {
    n: 3,
    icono: 'fa-solid fa-clone',
    titulo: 'Revise los duplicados',
    texto: 'El sistema compara la descripcion contra el catalogo y muestra los materiales parecidos. Usted decide si alguno le sirve o si el suyo es distinto.',
  },
  {
    n: 4,
    icono: 'fa-solid fa-tags',
    titulo: 'Confirme la categoria',
    texto: 'Se sugieren las tres clases mas probables con su nivel de confianza. Puede aceptar una, elegir otra o buscarla manualmente antes de confirmar.',
  },
  {
    n: 5,
    icono: 'fa-solid fa-file-export',
    titulo: 'Exporte a SAP',
    texto: 'Las solicitudes confirmadas se descargan en un archivo de hoja de calculo, que es el insumo con el que el material se registra en SAP.',
  },
]

const faqs = [
  {
    q: '¿GAMMA crea el material directamente en SAP?',
    a: 'No. GAMMA es una herramienta de asistencia: normaliza, alerta de duplicados y sugiere la categoria, pero la creacion final del material la realiza usted. Las solicitudes ya validadas se entregan en un archivo de hoja de calculo con el que se hace el registro en SAP.',
  },
  {
    q: '¿Por que a veces el asistente me pide mas datos en lugar de proponer una descripcion?',
    a: 'Porque prefiere quedarse corto antes que inventar. Si falta un dato relevante —el material de fabricacion, una medida, una norma— lo solicita de forma explicita. El listado que devuelve esta redactado para que pueda copiarlo y enviarlo al solicitante original.',
  },
  {
    q: 'El sistema me muestra duplicados que no se parecen a mi material. ¿Es un error?',
    a: 'No. El umbral de alerta esta deliberadamente abierto: es preferible que revise una sugerencia de mas a que se cree un duplicado en el catalogo. Si ninguno corresponde, indiquelo y el flujo continua.',
  },
  {
    q: '¿Que tan confiable es la categoria que sugiere?',
    a: 'El modelo acierta en cerca del 85 % de los casos en su primera sugerencia, y la categoria correcta aparece entre las tres primeras en mas del 94 %. Cuando su confianza es alta la sugerencia se marca como resuelta; cuando no, se le pide revision explicita.',
  },
  {
    q: 'Busque un material y no aparecio, pero si existe en SAP. ¿Por que?',
    a: 'La plataforma trabaja sobre una copia del maestro que se actualiza de forma periodica, no sobre SAP en tiempo real. Un material creado despues de la ultima carga no se vera hasta la siguiente actualizacion del catalogo.',
  },
  {
    q: 'Me equivoque al confirmar una solicitud. ¿Puedo corregirla?',
    a: 'Si. Mientras la solicitud no se haya exportado puede volver a abrirla desde la conversacion y ajustar la descripcion o la categoria. Si ya se exporto, la correccion se hace directamente en SAP.',
  },
]
</script>

<template>
  <section class="max-w-6xl mx-auto px-6 py-8">
    <div class="mb-8">
      <h1 class="text-2xl font-bold tracking-tight">Ayuda</h1>
      <p class="text-sm text-muted-foreground mt-1">
        Guia de uso del asistente para la creacion de materiales
      </p>
    </div>

    <!-- Manuales -->
    <Card class="mb-8">
      <CardHeader class="pb-3">
        <CardTitle class="text-base flex items-center gap-2">
          <i class="fa-solid fa-book text-sm text-muted-foreground"></i>
          Documentacion
        </CardTitle>
        <CardDescription>
          Los manuales del proyecto en PDF. Se descargan segun los permisos de su cuenta.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="errorManual" class="mb-4 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm">
          <i class="fa-solid fa-triangle-exclamation mr-2"></i>{{ errorManual }}
        </div>

        <p v-if="cargandoManuales" class="text-sm text-muted-foreground">
          <i class="fa-solid fa-spinner fa-spin mr-2"></i>Consultando la documentacion disponible...
        </p>

        <div v-else-if="manuales.length" class="grid sm:grid-cols-2 gap-3">
          <div
            v-for="m in manuales"
            :key="m.slug"
            class="p-4 rounded-md border bg-card flex flex-col"
          >
            <div class="flex items-start justify-between gap-2 mb-1">
              <p class="text-sm font-medium leading-tight">{{ m.titulo }}</p>
              <Badge v-if="m.solo_admin" variant="secondary" class="text-xs shrink-0">Admin</Badge>
            </div>
            <p class="text-xs text-muted-foreground flex-1">{{ m.descripcion }}</p>
            <Separator class="my-3" />
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs text-muted-foreground">
                {{ m.disponible ? `PDF · ${mb(m.size_bytes)}` : 'Aun no compilado' }}
              </span>
              <Button
                size="sm" variant="outline" class="gap-2 text-xs h-8"
                :disabled="!m.disponible || descargando === m.slug"
                @click="descargar(m)"
              >
                <i
                  :class="descargando === m.slug ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-download'"
                  class="text-xs"
                ></i>
                Descargar
              </Button>
            </div>
          </div>
        </div>

        <div
          v-else
          class="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground"
        >
          <i class="fa-regular fa-file-lines text-xl mb-2 block opacity-60"></i>
          La documentacion todavia no esta disponible.
          <span class="block mt-1 text-xs">
            Mientras tanto, la guia rapida y las preguntas frecuentes cubren el flujo completo.
          </span>
        </div>
      </CardContent>
    </Card>

    <!-- Guia rapida -->
    <div class="flex items-baseline justify-between mb-4">
      <h2 class="text-base font-semibold tracking-tight">Guia rapida</h2>
      <span class="text-xs text-muted-foreground">{{ pasos.length }} pasos</span>
    </div>
    <div class="grid sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-10">
      <div
        v-for="p in pasos"
        :key="p.n"
        class="p-4 rounded-md border bg-card hover:shadow-sm transition-shadow flex flex-col"
      >
        <div class="flex items-center gap-2 mb-2">
          <span
            class="w-6 h-6 shrink-0 rounded-full bg-primary text-primary-foreground
                   text-xs font-semibold flex items-center justify-center"
          >{{ p.n }}</span>
          <i :class="p.icono" class="text-xs text-muted-foreground"></i>
        </div>
        <p class="text-sm font-medium leading-tight mb-1">{{ p.titulo }}</p>
        <p class="text-xs text-muted-foreground flex-1">{{ p.texto }}</p>
      </div>
    </div>

    <!-- Preguntas frecuentes -->
    <h2 class="text-base font-semibold tracking-tight mb-4">Preguntas frecuentes</h2>
    <Card class="mb-8">
      <CardContent class="pt-2 pb-2">
        <Accordion type="single" collapsible class="w-full">
          <AccordionItem v-for="(f, i) in faqs" :key="i" :value="`faq-${i}`">
            <AccordionTrigger class="text-sm text-left">{{ f.q }}</AccordionTrigger>
            <AccordionContent class="text-sm text-muted-foreground">
              {{ f.a }}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>

    <!-- Soporte -->
    <Card>
      <CardContent class="py-5">
        <div class="flex flex-col sm:flex-row sm:items-center gap-4">
          <div class="flex-1">
            <p class="text-sm font-medium mb-1">¿No encontro lo que buscaba?</p>
            <p class="text-xs text-muted-foreground">
              Escriba al equipo de datos maestros describiendo el material y el paso donde se
              quedo. Si el asistente devolvio un mensaje de error, incluyalo tal cual.
            </p>
          </div>
          <Separator orientation="vertical" class="hidden sm:block h-10" />
          <Button as-child variant="outline" class="gap-2 shrink-0">
            <RouterLink to="/chat">
              <i class="fa-solid fa-robot text-xs"></i>
              Ir al asistente
            </RouterLink>
          </Button>
        </div>
      </CardContent>
    </Card>
  </section>
</template>

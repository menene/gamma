<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { useAuth } from '@/composables/useAuth'

const { isAuthenticated } = useAuth()

// Sin sesion no tiene sentido mandar al asistente: la ruta esta protegida y
// rebotaria al login. Se manda directo.
const destinoChat = computed(() => (isAuthenticated.value ? '/chat' : '/login'))

const pasos = [
  {
    num: '01',
    icon: 'fa-solid fa-pen-nib',
    titulo: 'Normaliza',
    desc: 'Convierte una descripcion escrita en lenguaje corriente al formato estandar del catalogo. Si falta un dato, lo pide en lugar de inventarlo.',
  },
  {
    num: '02',
    icon: 'fa-solid fa-clone',
    titulo: 'Detecta duplicados',
    desc: 'Compara contra el catalogo completo por similitud de texto, no por coincidencia exacta, de modo que una abreviatura distinta no esconda un material que ya existe.',
  },
  {
    num: '03',
    icon: 'fa-solid fa-tags',
    titulo: 'Clasifica',
    desc: 'Sugiere las tres clases mas probables con su nivel de confianza, a partir de como se ha clasificado el historico del catalogo.',
  },
]

const cifras = [
  { valor: '40,046', label: 'materiales gobernados' },
  { valor: '1,234', label: 'clases del catalogo' },
  { valor: '54%', label: 'menos tiempo por solicitud' },
  { valor: '0', label: 'escrituras sin revisar' },
]
</script>

<template>
  <section>

    <!-- Hero -->
    <div class="px-6 pt-20 pb-16 md:pt-28 md:pb-20">
      <div class="max-w-3xl mx-auto text-center">
        <h1 class="text-5xl md:text-7xl font-bold tracking-tighter mb-4">GAMMA</h1>
        <p class="text-lg md:text-xl text-muted-foreground mb-5">
          Gobierno Automatizado del Maestro de Materiales
        </p>
        <p class="text-base text-muted-foreground/90 max-w-xl mx-auto leading-relaxed mb-9">
          Un asistente que acompaña la creacion de materiales en SAP: redacta la
          descripcion, avisa si el material ya existe y propone su clase.
          La decision final siempre es suya.
        </p>

        <div class="flex flex-col sm:flex-row gap-3 justify-center">
          <Button as-child size="lg" class="gap-2">
            <RouterLink :to="destinoChat">
              <i class="fa-solid fa-robot text-sm"></i>
              {{ isAuthenticated ? 'Ir al asistente' : 'Iniciar sesion' }}
            </RouterLink>
          </Button>
          <Button v-if="isAuthenticated" as-child size="lg" variant="outline" class="gap-2">
            <RouterLink to="/ayuda">
              <i class="fa-solid fa-circle-question text-sm"></i>
              Como funciona
            </RouterLink>
          </Button>
        </div>
      </div>
    </div>

    <!-- Cifras -->
    <div class="px-6 pb-20">
      <div class="max-w-4xl mx-auto">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-px bg-border rounded-lg overflow-hidden border">
          <div v-for="c in cifras" :key="c.label" class="bg-background px-5 py-6 text-center">
            <p class="text-3xl font-bold tracking-tight tabular-nums">{{ c.valor }}</p>
            <p class="text-xs text-muted-foreground mt-1.5 leading-tight">{{ c.label }}</p>
          </div>
        </div>
      </div>
    </div>

    <Separator />

    <!-- Flujo -->
    <div class="px-6 py-20">
      <div class="max-w-5xl mx-auto">
        <p class="text-center text-xs text-muted-foreground uppercase tracking-widest mb-2">
          Como funciona
        </p>
        <h2 class="text-2xl md:text-3xl font-bold tracking-tight text-center mb-12">
          Tres validaciones en una sola conversacion
        </h2>

        <!-- Punto de partida: de aqui sale el catalogo contra el que se compara -->
        <div class="flex justify-center mb-8">
          <div class="flex items-center gap-3 px-5 py-3 rounded-lg border bg-card text-sm max-w-lg">
            <i class="fa-solid fa-file-arrow-up text-muted-foreground shrink-0"></i>
            <span class="text-muted-foreground">
              El catalogo se mantiene al dia cargando los archivos exportados de SAP
            </span>
          </div>
        </div>

        <div class="flex justify-center mb-8">
          <i class="fa-solid fa-arrow-down text-muted-foreground text-xs"></i>
        </div>

        <div class="grid md:grid-cols-3 gap-5">
          <Card
            v-for="paso in pasos"
            :key="paso.num"
            class="relative overflow-hidden hover:shadow-md transition-shadow"
          >
            <CardContent class="pt-6">
              <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 rounded-lg bg-muted flex items-center justify-center shrink-0">
                  <i :class="paso.icon" class="text-base text-foreground"></i>
                </div>
                <span class="text-xs font-mono text-muted-foreground">{{ paso.num }}</span>
              </div>
              <h3 class="font-semibold text-lg mb-2">{{ paso.titulo }}</h3>
              <p class="text-sm text-muted-foreground leading-relaxed">{{ paso.desc }}</p>
            </CardContent>
            <span
              class="absolute top-0 right-2 text-[7rem] leading-none font-black
                     text-foreground opacity-[0.035] pointer-events-none select-none"
            >{{ paso.num }}</span>
          </Card>
        </div>

        <!-- Cierre del flujo -->
        <div class="flex flex-col sm:flex-row items-center justify-center gap-3 mt-8">
          <div class="flex items-center gap-3 px-5 py-3 rounded-lg border bg-card text-sm w-full sm:w-auto">
            <i class="fa-solid fa-user-check text-muted-foreground"></i>
            <span class="text-muted-foreground">Usted revisa y confirma</span>
          </div>
          <i class="fa-solid fa-arrow-right text-muted-foreground text-xs rotate-90 sm:rotate-0"></i>
          <div class="flex items-center gap-3 px-5 py-3 rounded-lg border bg-card text-sm w-full sm:w-auto">
            <i class="fa-solid fa-file-export text-muted-foreground"></i>
            <span class="text-muted-foreground">Se exporta para cargar en SAP</span>
          </div>
        </div>

        <p class="text-center text-xs text-muted-foreground mt-6 max-w-lg mx-auto">
          GAMMA no escribe en SAP. Prepara y valida la solicitud; el registro final
          lo hace usted con el archivo que genera.
        </p>
      </div>
    </div>

    <Separator />

    <!-- Llamado a la accion -->
    <div class="px-6 py-16">
      <div class="max-w-3xl mx-auto">
        <Card>
          <CardContent class="py-5">
            <div class="flex flex-col sm:flex-row sm:items-center gap-4">
              <div class="flex-1">
                <p class="text-sm font-medium mb-1">
                  {{ isAuthenticated ? '¿Listo para dar de alta un material?' : '¿Ya tiene cuenta?' }}
                </p>
                <p class="text-xs text-muted-foreground">
                  {{ isAuthenticated
                    ? 'Describa lo que necesita con sus palabras. El asistente se encarga del formato, los duplicados y la clase.'
                    : 'Inicie sesion para usar el asistente. Las cuentas las crea el area de datos maestros.' }}
                </p>
              </div>
              <Separator orientation="vertical" class="hidden sm:block h-10" />
              <Button as-child variant="outline" class="gap-2 shrink-0">
                <RouterLink :to="destinoChat">
                  <i class="fa-solid fa-robot text-xs"></i>
                  {{ isAuthenticated ? 'Ir al asistente' : 'Iniciar sesion' }}
                </RouterLink>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </section>
</template>

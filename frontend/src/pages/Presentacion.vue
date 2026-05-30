<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

const pasos = [
  {
    num: '01',
    icon: 'fa-solid fa-magnifying-glass',
    titulo: 'Validacion',
    desc: 'Detecta duplicados en el maestro existente usando fuzzy search con pg_trgm. Evita registros redundantes antes de crear.',
    color: 'text-blue-500',
    bg: 'bg-blue-500/10',
  },
  {
    num: '02',
    icon: 'fa-solid fa-pen-nib',
    titulo: 'Descripcion',
    desc: 'Genera el texto breve estandarizado con LLM, respetando el formato SAP: palabra clave, abreviaturas y separadores.',
    color: 'text-violet-500',
    bg: 'bg-violet-500/10',
  },
  {
    num: '03',
    icon: 'fa-solid fa-tags',
    titulo: 'Categorizacion',
    desc: 'Clasifica automaticamente el material con modelo ML. Devuelve categoria, confianza y alternativas top-K.',
    color: 'text-amber-500',
    bg: 'bg-amber-500/10',
  },
]

const cifras = [
  { valor: '3', label: 'Servicios de procesamiento', icon: 'fa-solid fa-gears' },
  { valor: '1', label: 'Instancia PostgreSQL', icon: 'fa-solid fa-database' },
  { valor: '0', label: 'Escrituras sin confirmacion', icon: 'fa-solid fa-shield-halved' },
]
</script>

<template>
  <section class="relative overflow-hidden">
    <!-- Hero -->
    <div class="py-28 px-6">
      <div class="max-w-4xl mx-auto text-center">
        <Badge variant="secondary" class="mb-6 text-xs tracking-widest uppercase">v0.1.0</Badge>
        <h1 class="text-5xl md:text-7xl font-bold tracking-tighter mb-4">
          GAMMA
        </h1>
        <p class="text-xl md:text-2xl text-muted-foreground font-medium mb-3">
          Gobierno Automatizado del Maestro de Materiales
        </p>
        <p class="text-base text-muted-foreground max-w-2xl mx-auto mb-10">
          Plataforma que automatiza el gobierno de datos del maestro de materiales de SAP:
          valida duplicados, clasifica la categoria y genera la descripcion
          estandarizada — con confirmacion humana obligatoria antes de persistir.
        </p>

        <!-- Cifras -->
        <div class="flex justify-center gap-10 mb-6">
          <div v-for="c in cifras" :key="c.label" class="text-center">
            <div class="flex items-center justify-center gap-2 mb-1">
              <i :class="c.icon" class="text-muted-foreground text-sm"></i>
              <span class="text-3xl font-bold tracking-tight">{{ c.valor }}</span>
            </div>
            <p class="text-xs text-muted-foreground">{{ c.label }}</p>
          </div>
        </div>
      </div>
    </div>

    <Separator />

    <!-- Pasos -->
    <div class="py-20 px-6">
      <div class="max-w-5xl mx-auto">
        <p class="text-center text-sm text-muted-foreground uppercase tracking-widest mb-2">Flujo de procesamiento</p>
        <h2 class="text-3xl font-bold tracking-tight text-center mb-12">Tres servicios, una solicitud</h2>

        <div class="grid md:grid-cols-3 gap-6">
          <Card v-for="paso in pasos" :key="paso.num" class="relative overflow-hidden hover:shadow-lg transition-shadow">
            <CardContent class="pt-6">
              <div class="flex items-center gap-3 mb-4">
                <div :class="[paso.bg, paso.color]" class="w-10 h-10 rounded-lg flex items-center justify-center">
                  <i :class="paso.icon" class="text-lg"></i>
                </div>
                <span class="text-xs font-mono text-muted-foreground">{{ paso.num }}</span>
              </div>
              <h3 class="font-semibold text-lg mb-2">{{ paso.titulo }}</h3>
              <p class="text-sm text-muted-foreground leading-relaxed">{{ paso.desc }}</p>
            </CardContent>
            <div :class="paso.color" class="absolute top-0 right-0 opacity-[0.03] text-[8rem] leading-none font-black pointer-events-none select-none">
              {{ paso.num }}
            </div>
          </Card>
        </div>

        <!-- Pasos finales -->
        <div class="flex justify-center mt-10 gap-4">
          <div class="flex items-center gap-3 px-5 py-3 rounded-lg border bg-card text-sm">
            <div class="w-8 h-8 rounded-md bg-green-500/10 text-green-500 flex items-center justify-center">
              <i class="fa-solid fa-user-check"></i>
            </div>
            <span class="text-muted-foreground">Confirmacion humana</span>
          </div>
          <div class="hidden md:flex items-center text-muted-foreground">
            <i class="fa-solid fa-arrow-right"></i>
          </div>
          <div class="flex items-center gap-3 px-5 py-3 rounded-lg border bg-card text-sm">
            <div class="w-8 h-8 rounded-md bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
              <i class="fa-solid fa-file-export"></i>
            </div>
            <span class="text-muted-foreground">Exportacion Excel para SAP</span>
          </div>
        </div>
      </div>
    </div>

    <Separator />

    <!-- Chatbot -->
    <div class="py-20 px-6">
      <div class="max-w-3xl mx-auto text-center">
        <div class="bg-primary/10 text-primary w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
          <i class="fa-solid fa-robot text-2xl"></i>
        </div>
        <h2 class="text-3xl font-bold tracking-tight mb-3">Todo desde un chatbot</h2>
        <p class="text-muted-foreground max-w-xl mx-auto">
          El usuario interactua con un asistente conversacional que orquesta
          validacion, descripcion y categorizacion de forma transparente —
          sin formularios, sin navegacion compleja.
        </p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
</script>

<template>
  <section class="py-24 px-6">
    <div class="max-w-4xl mx-auto text-center">
      <Badge variant="secondary" class="mb-4">v0.1.0</Badge>
      <h1 class="text-4xl md:text-6xl font-bold tracking-tight mb-6">
        GAMMA
      </h1>
      <p class="text-lg text-muted-foreground mb-4">
        Gobierno Automatizado del Maestro de Materiales
      </p>
      <p class="text-base text-muted-foreground max-w-2xl mx-auto mb-12">
        Plataforma que automatiza el gobierno de datos del maestro de materiales de SAP:
        valida duplicados, clasifica la categoria del material y genera la descripcion
        estandarizada, con confirmacion humana antes de escribir y exportacion a Excel
        para carga masiva en SAP.
      </p>

      <div class="grid md:grid-cols-3 gap-6 text-left max-w-3xl mx-auto">
        <div class="p-6 rounded-lg border bg-card">
          <div class="text-2xl mb-2">1</div>
          <h3 class="font-semibold mb-1">Validacion</h3>
          <p class="text-sm text-muted-foreground">Detecta duplicados en el maestro existente usando similitud difusa.</p>
        </div>
        <div class="p-6 rounded-lg border bg-card">
          <div class="text-2xl mb-2">2</div>
          <h3 class="font-semibold mb-1">Categorizacion</h3>
          <p class="text-sm text-muted-foreground">Clasifica automaticamente el material con modelo ML y umbral de confianza.</p>
        </div>
        <div class="p-6 rounded-lg border bg-card">
          <div class="text-2xl mb-2">3</div>
          <h3 class="font-semibold mb-1">Descripcion</h3>
          <p class="text-sm text-muted-foreground">Genera el texto breve estandarizado con LLM, respetando formato SAP.</p>
        </div>
      </div>
    </div>
  </section>
</template>

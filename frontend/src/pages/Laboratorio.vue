<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { LAB_URL as labUrl } from '@/config'

const notebooks = [
  {
    file: '01_eda.ipynb',
    title: 'Exploracion del Maestro',
    badge: 'EDA',
    desc: 'Explora la estructura del maestro de materiales en silver.maestro. Analiza la distribucion de categorias, longitud de descripciones y detecta materiales potencialmente duplicados.',
    tags: ['silver.maestro', 'pandas', 'matplotlib'],
  },
  {
    file: '02_evaluacion_modelos.ipynb',
    title: 'Evaluacion de Modelos',
    badge: 'ML',
    desc: 'Evalua el rendimiento del modelo de categorizacion. Genera matriz de confusion, metricas de precision/recall/F1 por categoria y analiza errores en funcion del umbral de confianza.',
    tags: ['sklearn', 'silver.dataset_test', 'metricas'],
  },
  {
    file: '03_monetizacion.ipynb',
    title: 'Dashboard de Monetizacion',
    badge: 'KPI',
    desc: 'Visualiza los indicadores de ahorro. Calcula horas-hombre ahorradas por semana, ahorro acumulado en quetzales y la tasa de auto-resolucion vs correccion manual.',
    tags: ['gold.monetizacion', 'gold.kpi_tiempos', 'plotly'],
  },
]
</script>

<template>
  <section class="py-20 px-6">
    <div class="max-w-5xl mx-auto">
      <div class="flex items-center justify-between mb-2">
        <h1 class="text-3xl font-bold tracking-tight">Laboratorio</h1>
        <Button as="a" :href="labUrl" target="_blank" rel="noopener">
          <i class="fa-solid fa-book mr-2"></i>
          Abrir Jupyter Lab
        </Button>
      </div>
      <p class="text-muted-foreground mb-10">
        Notebooks de experimentacion conectados a la base de datos del proyecto.
        Cada notebook aborda un aspecto clave del sistema.
      </p>

      <div class="grid md:grid-cols-2 gap-6">
        <Card v-for="nb in notebooks" :key="nb.file" class="hover:shadow-md transition-shadow">
          <CardHeader class="pb-2">
            <CardTitle class="text-base flex items-center gap-2">
              <Badge>{{ nb.badge }}</Badge>
              {{ nb.title }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-sm text-muted-foreground mb-3">{{ nb.desc }}</p>
            <div class="flex flex-wrap gap-1.5">
              <Badge v-for="tag in nb.tags" :key="tag" variant="secondary" class="text-xs">
                {{ tag }}
              </Badge>
            </div>
            <Separator class="my-3" />
            <p class="text-xs text-muted-foreground font-mono">{{ nb.file }}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { LAB_URL as labUrl, PLANKA_URL as plankaUrl } from '@/config'
import LogsContent from '@/pages/LogsContent.vue'

const activeTab = ref('notebooks')

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
  <section class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Lab</h1>
        <p class="text-sm text-muted-foreground mt-1">Notebooks de experimentacion y logs del sistema</p>
      </div>
      <div class="flex items-center gap-2">
        <Button as="a" :href="plankaUrl" target="_blank" rel="noopener" variant="outline" class="gap-2">
          <i class="fa-solid fa-table-columns text-xs"></i>
          Planka
        </Button>
        <Button as="a" :href="labUrl" target="_blank" rel="noopener" variant="outline" class="gap-2">
          <i class="fa-solid fa-arrow-up-right-from-square text-xs"></i>
          Jupyter
        </Button>
      </div>
    </div>

    <Tabs v-model="activeTab">
      <TabsList class="mb-6">
        <TabsTrigger value="notebooks" class="gap-2">
          <i class="fa-solid fa-flask text-xs"></i>
          Notebooks
        </TabsTrigger>
        <TabsTrigger value="logs" class="gap-2">
          <i class="fa-solid fa-list-check text-xs"></i>
          Logs
        </TabsTrigger>
      </TabsList>

      <!-- Notebooks -->
      <TabsContent value="notebooks">
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
                <Badge v-for="tag in nb.tags" :key="tag" variant="secondary" class="text-xs">{{ tag }}</Badge>
              </div>
              <Separator class="my-3" />
              <p class="text-xs text-muted-foreground font-mono">{{ nb.file }}</p>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <!-- Logs -->
      <TabsContent value="logs">
        <LogsContent />
      </TabsContent>
    </Tabs>
  </section>
</template>

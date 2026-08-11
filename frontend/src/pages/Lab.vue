<script setup lang="ts">
import { ref } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { LAB_URL as labUrl } from '@/config'
import LogsContent from '@/pages/LogsContent.vue'

const activeTab = ref('notebooks')

// ── Analisis exploratorio ────────────────────────────────────────────────
// Vistas consolidadas del maestro, transversales a los tipos de material.
const edaConsolidados = [
  {
    file: 'eda/EDA_Unificado_M402_GAMMA.ipynb',
    title: 'EDA Unificado M402',
    desc: 'Consolidado de los once tipos del mandante 402: 43,177 registros, con duplicidad exacta, registros bloqueados y adherencia al separador estandar por tipo.',
  },
  {
    file: 'eda/EDA_COMBINADO.ipynb',
    title: 'EDA Combinado',
    desc: 'Comparativo transversal entre tipos: tamano del catalogo, tasa de duplicados y proporcion de registros sin separador estandar.',
  },
  {
    file: '01_eda.ipynb',
    title: 'Exploracion del Maestro',
    desc: 'Exploracion sobre silver.materials: distribucion de categorias, longitud de descripciones y deteccion de duplicados potenciales.',
  },
]

// EDA por tipo de material — misma plantilla aplicada a cada catalogo.
// Cifras tomadas de la ejecucion sobre el corte del 29 de mayo de 2026.
const edaTipos = [
  { tipo: 'ZRPI', nombre: 'Repuestos industriales', registros: '15,861', dup: '6.1%' },
  { tipo: 'ZSUM', nombre: 'Suministros', registros: '13,399', dup: '3.4%' },
  { tipo: 'ZQUI', nombre: 'Quimicos', registros: '5,667', dup: '5.5%' },
  { tipo: 'ZSEG', nombre: 'Seguridad', registros: '2,626', dup: '8.7%' },
  { tipo: 'ZMER MOB OFI VEH TUB', nombre: 'Mercancia general', registros: '2,552', dup: '1.7%' },
  { tipo: 'ZHER', nombre: 'Herramientas', registros: '2,033', dup: '0.2%' },
  { tipo: 'ZHAR', nombre: 'Hardware y electronica', registros: '384', dup: '3.4%' },
  { tipo: 'ZRPA', nombre: 'Repuestos automotriz', registros: '337', dup: '0.6%' },
  { tipo: 'ZEQU', nombre: 'Equipos', registros: '145', dup: '35.2%' },
  { tipo: 'ZMAQ', nombre: 'Maquinaria', registros: '93', dup: '0.0%' },
  { tipo: 'ZMAF', nombre: 'Maquinaria y fabricacion', registros: '80', dup: '5.0%' },
]

// ── Modelado y analitica de negocio ──────────────────────────────────────
const notebooks = [
  {
    file: '02_evaluacion_modelos.ipynb',
    title: 'Competencia de Modelos',
    badge: 'ML',
    desc: 'Evalua cuatro configuraciones de clasificacion sobre el historico del catalogo. Genera matriz de confusion, metricas por categoria y el analisis de exactitud frente a cobertura por umbral de confianza.',
    tags: ['sklearn', 'LinearSVC', 'TF-IDF', 'metricas'],
  },
  {
    file: '03_modelos_candidatos_v2.ipynb',
    title: 'Candidatos Adicionales',
    badge: 'ML',
    desc: 'Segunda ronda de la competencia: XGBoost, fastText y un transformer multilingue con ajuste fino, contrastados contra el ganador de la primera ronda.',
    tags: ['XGBoost', 'fastText', 'transformers'],
  },
  {
    file: '04_monetizacion.ipynb',
    title: 'Monetizacion y ROI',
    badge: 'KPI',
    desc: 'Cuantifica el ahorro en horas-gestor y el retorno de la inversion. Recalcula los tiempos post-GAMMA desde el registro individual, los contrasta contra la linea base y valida la diferencia estadisticamente.',
    tags: ['costo-hora', 'ahorro anual', 'ROI', 'Mann-Whitney'],
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

        <!-- Analisis exploratorio — tarjeta a todo el ancho -->
        <Card class="mb-8">
          <CardHeader class="pb-3">
            <CardTitle class="text-base flex items-center gap-2">
              <Badge>EDA</Badge>
              Analisis Exploratorio de Datos
              <span class="ml-auto text-xs font-normal text-muted-foreground">
                {{ edaConsolidados.length + edaTipos.length }} notebooks
              </span>
            </CardTitle>
            <CardDescription>
              Caracterizacion del maestro de materiales del mandante 402: completitud de campos,
              duplicidad exacta, grupos de articulos, unidades de medida, materiales bloqueados y
              patrones de texto breve.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <!-- Vistas consolidadas -->
            <p class="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
              Vistas consolidadas
            </p>
            <div class="grid md:grid-cols-3 gap-3">
              <div
                v-for="e in edaConsolidados"
                :key="e.file"
                class="p-3 rounded-md border bg-muted/40 hover:shadow-sm transition-shadow flex flex-col"
              >
                <p class="text-sm font-medium leading-tight mb-1">{{ e.title }}</p>
                <p class="text-xs text-muted-foreground flex-1">{{ e.desc }}</p>
                <Separator class="my-2" />
                <p class="text-xs text-muted-foreground font-mono break-all">{{ e.file }}</p>
              </div>
            </div>

            <Separator class="my-5" />

            <!-- Por tipo de material -->
            <div class="flex items-baseline justify-between mb-3">
              <p class="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Por tipo de material
              </p>
              <span class="text-xs text-muted-foreground">{{ edaTipos.length }} catalogos</span>
            </div>
            <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div
                v-for="t in edaTipos"
                :key="t.tipo"
                class="p-3 rounded-md border bg-card hover:shadow-sm transition-shadow"
              >
                <div class="flex items-center justify-between gap-2 mb-1">
                  <Badge variant="secondary" class="font-mono text-xs">{{ t.tipo }}</Badge>
                  <span class="text-xs text-muted-foreground shrink-0">{{ t.registros }}</span>
                </div>
                <p class="text-sm font-medium leading-tight">{{ t.nombre }}</p>
                <p class="text-xs text-muted-foreground mt-1">Duplicados: {{ t.dup }}</p>
                <Separator class="my-2" />
                <p class="text-xs text-muted-foreground font-mono break-all">eda/EDA_{{ t.tipo }}.ipynb</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Modelado y analitica de negocio -->
        <div class="flex items-baseline justify-between mb-4">
          <h2 class="text-base font-semibold tracking-tight">Modelado y analitica de negocio</h2>
          <span class="text-xs text-muted-foreground">{{ notebooks.length }} notebooks</span>
        </div>
        <div class="grid md:grid-cols-3 gap-6">
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

<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import ArchitectureDiagram from '@/components/ArchitectureDiagram.vue'

import dockerLogo from '@/assets/logos/docker.svg'
import postgresqlLogo from '@/assets/logos/postgresql.svg'
import pythonLogo from '@/assets/logos/python.svg'
import fastapiLogo from '@/assets/logos/fastapi.svg'
import geminiLogo from '@/assets/logos/gemini.svg'
import pandasLogo from '@/assets/logos/pandas.svg'
import excelLogo from '@/assets/logos/excel.svg'
import jupyterLogo from '@/assets/logos/jupyter.svg'
import vueLogo from '@/assets/logos/vue.svg'
import tailwindLogo from '@/assets/logos/tailwind.svg'
import shadcnLogo from '@/assets/logos/shadcn.svg'
import powerbiLogo from '@/assets/logos/powerbi.svg'
import sqlalchemyLogo from '@/assets/logos/sqlalchemy.svg'
import pydanticLogo from '@/assets/logos/pydantic.svg'
import nginxLogo from '@/assets/logos/nginx.svg'
import jwtLogo from '@/assets/logos/jwt.svg'
import viteLogo from '@/assets/logos/vite.svg'
import plankaLogo from '@/assets/logos/planka.svg'

const servicios = [
  {
    nombre: 'Chatbot',
    badge: 'Entrada',
    desc: 'Interfaz conversacional donde el usuario describe el material. El LLM normaliza la descripcion, busca duplicados y guia al usuario hasta la confirmacion.',
  },
  {
    nombre: 'Autenticacion',
    badge: 'Seguridad',
    desc: 'Login con JWT y bcrypt. Todas las rutas del API (excepto health) requieren token. El frontend gestiona la sesion y protege las paginas.',
  },
  {
    nombre: 'API REST (FastAPI)',
    badge: 'Backend',
    desc: 'Orquesta todo el flujo. Recibe la solicitud, coordina normalizacion, duplicados y categorizacion. Escribe en silver y registra logs en bronze.',
  },
  {
    nombre: 'Normalizacion (LLM)',
    badge: 'Servicio',
    desc: 'Google Gemini normaliza la descripcion al formato SAP. Aplica reglas de abreviaturas, separadores y palabras clave. Presenta duplicados conversacionalmente.',
  },
  {
    nombre: 'Duplicados',
    badge: 'Servicio',
    desc: 'Consulta el maestro en silver usando pg_trgm de PostgreSQL. Calcula similitud difusa y presenta candidatos al usuario para decidir.',
  },
  {
    nombre: 'Categorizacion',
    badge: 'Servicio',
    desc: 'Modelo ML que predice la clase del material. Devuelve categoria, confianza y top-K alternativas.',
  },
  {
    nombre: 'Confirmacion humana',
    badge: 'Validacion',
    desc: 'Dentro del chatbot, el usuario revisa la propuesta. Puede aceptar, explicar diferencias con duplicados, o descartar. Las decisiones alimentan los KPIs en gold.',
  },
  {
    nombre: 'ETL',
    badge: 'Ingesta',
    desc: 'Importador de archivos Excel para cargar maestros de materiales, clases y UNSPSC. Usa UPSERT para actualizaciones idempotentes.',
  },
  {
    nombre: 'Exportador',
    badge: 'Salida',
    desc: 'Desde el frontend se consultan registros confirmados en la base de datos y se exportan como .xlsx para carga masiva en SAP.',
  },
]

const stack = [
  {
    layer: 'Orquestacion',
    tech: 'Docker + Docker Compose',
    desc: 'Todos los servicios en una red interna con Nginx como reverse proxy',
    logos: [dockerLogo, nginxLogo],
  },
  {
    layer: 'Base de datos',
    tech: 'PostgreSQL 16',
    desc: 'Arquitectura medallon, pg_trgm para similitud difusa',
    logos: [postgresqlLogo],
  },
  {
    layer: 'API / Backend',
    tech: 'FastAPI + SQLAlchemy',
    desc: 'Python 3.12, Pydantic v2, Uvicorn',
    logos: [pythonLogo, fastapiLogo, sqlalchemyLogo, pydanticLogo],
  },
  {
    layer: 'Autenticacion',
    tech: 'JWT + bcrypt',
    desc: 'Login con tokens, rutas protegidas, sesiones seguras',
    logos: [jwtLogo, pythonLogo],
  },
  {
    layer: 'LLM',
    tech: 'Google Gemini',
    desc: 'Normalizacion de descripciones y deteccion conversacional de duplicados',
    logos: [geminiLogo],
  },
  {
    layer: 'Modelo',
    tech: 'Integrado en API',
    desc: 'Endpoint /api/model/predict para categorizacion',
    logos: [pythonLogo, fastapiLogo],
  },
  {
    layer: 'ETL',
    tech: 'pandas + openpyxl',
    desc: 'Importacion de maestros Excel con UPSERT y logs de ingesta',
    logos: [pandasLogo, excelLogo],
  },
  {
    layer: 'Laboratorio',
    tech: 'Jupyter Lab',
    desc: 'Experimentacion con datasets, protegido con token',
    logos: [jupyterLogo, pythonLogo],
  },
  {
    layer: 'Frontend',
    tech: 'Vue 3 + Vite + Tailwind + shadcn',
    desc: 'SPA con chatbot, ETL, docs y Swagger integrado',
    logos: [vueLogo, viteLogo, tailwindLogo, shadcnLogo],
  },
  {
    layer: 'Gestion',
    tech: 'Planka',
    desc: 'Tablero Kanban para gestion de tareas del equipo',
    logos: [plankaLogo],
  },
  {
    layer: 'Analitica',
    tech: 'Power BI',
    desc: 'Conectado al esquema gold para dashboards',
    logos: [powerbiLogo],
  },
]

const medallon = [
  {
    capa: 'Bronze',
    color: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
    desc: 'Datos crudos y trazabilidad. Almacena los CSV de SAP tal cual se importan (maestro y categorias) con timestamp de ingesta, y los logs de cada prediccion del sistema con la decision del usuario.',
  },
  {
    capa: 'Silver',
    color: 'bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-200',
    desc: 'Capa operacional y de referencia. Maestro normalizado con indice trigram, solicitudes con su ciclo de vida completo, y datasets de entrenamiento y prueba. El API lee y escribe directamente aqui.',
  },
  {
    capa: 'Gold',
    color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    desc: 'Vistas exclusivas para dashboard. KPIs de tiempos, calidad y monetizacion. No almacena datos — lee de silver en tiempo real. Power BI se conecta a este esquema.',
  },
]
</script>

<template>
  <section class="py-20 px-6">
    <div class="max-w-5xl mx-auto">
      <h1 class="text-3xl font-bold tracking-tight mb-2">Arquitectura</h1>
      <p class="text-muted-foreground mb-10">
        Arquitectura medallon de tres capas (bronze, silver, gold) sobre una sola instancia de PostgreSQL.
        Bronze ingesta los CSV de SAP y registra la actividad del sistema. Silver es la capa de trabajo donde
        el API opera. Gold expone vistas agregadas exclusivamente para Power BI.
      </p>

      <!-- Diagrama -->
      <Card class="mb-12">
        <CardContent class="pt-6">
          <ArchitectureDiagram />
        </CardContent>
      </Card>

      <!-- Plano operacional -->
      <h2 class="text-2xl font-bold tracking-tight mb-2">Plano operacional</h2>
      <p class="text-muted-foreground mb-6">
        Flujo de creacion de un material, desde la captura hasta la exportacion a SAP.
      </p>

      <div class="grid md:grid-cols-2 gap-4 mb-12">
        <Card v-for="s in servicios" :key="s.nombre">
          <CardHeader class="pb-2">
            <CardTitle class="text-base flex items-center gap-2">
              <Badge variant="outline" class="text-xs">{{ s.badge }}</Badge>
              {{ s.nombre }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-sm text-muted-foreground">{{ s.desc }}</p>
          </CardContent>
        </Card>
      </div>

      <Separator class="my-10" />

      <!-- Plano analitico -->
      <h2 class="text-2xl font-bold tracking-tight mb-2">Plano analitico</h2>
      <p class="text-muted-foreground mb-6">
        Arquitectura medallon dentro de PostgreSQL. Los CSV de SAP se ingestan en bronze, se normalizan en silver
        y gold expone vistas calculadas en tiempo real sobre silver.
      </p>

      <div class="grid md:grid-cols-3 gap-4 mb-12">
        <Card v-for="m in medallon" :key="m.capa">
          <CardHeader class="pb-2">
            <CardTitle class="text-base flex items-center gap-2">
              <span :class="['px-2 py-0.5 rounded text-xs font-medium', m.color]">{{ m.capa }}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-sm text-muted-foreground">{{ m.desc }}</p>
          </CardContent>
        </Card>
      </div>

      <Separator class="my-10" />

      <!-- Stack tecnologico -->
      <h2 class="text-2xl font-bold tracking-tight mb-2">Stack tecnologico</h2>
      <p class="text-muted-foreground mb-6">Cada eleccion optimiza la productividad del equipo y la integracion con SAP.</p>

      <div class="grid md:grid-cols-3 gap-4">
        <Card v-for="item in stack" :key="item.layer" class="hover:shadow-md transition-shadow">
          <CardContent class="pt-6">
            <div class="flex items-center gap-2 mb-3">
              <img
                v-for="(logo, i) in item.logos"
                :key="i"
                :src="logo"
                :alt="item.tech"
                class="h-5 w-5"
              />
            </div>
            <Badge variant="outline" class="mb-2">{{ item.layer }}</Badge>
            <h3 class="font-semibold text-sm mb-1">{{ item.tech }}</h3>
            <p class="text-xs text-muted-foreground">{{ item.desc }}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  </section>
</template>

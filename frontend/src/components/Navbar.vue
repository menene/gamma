<script setup lang="ts">
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'

const links = [
  { label: 'Arquitectura', to: '/arquitectura', icon: 'fa-solid fa-cubes' },
  { label: 'Laboratorio', to: '/laboratorio', icon: 'fa-solid fa-flask' },
  { label: 'ETL', to: '/etl', icon: 'fa-solid fa-file-import' },
  { label: 'API', to: '/api', icon: 'fa-solid fa-plug' },
  { label: 'Docs', to: '/docs', icon: 'fa-solid fa-book' },
]
</script>

<template>
  <nav class="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
    <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
      <RouterLink to="/" class="font-bold text-xl tracking-tight">GAMMA</RouterLink>
      <div class="hidden md:flex items-center gap-1">
        <RouterLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="px-3 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-muted flex items-center gap-2"
          active-class="text-foreground bg-muted"
        >
          <i :class="link.icon" class="text-xs"></i>
          {{ link.label }}
        </RouterLink>
        <Button as-child class="ml-2 px-3 py-2 h-auto">
          <a href="/chat" rel="noopener" class="flex items-center gap-2 text-sm">
            <i class="fa-solid fa-robot"></i>
            Chat
          </a>
        </Button>
      </div>
    </div>
    <Separator />
  </nav>
</template>

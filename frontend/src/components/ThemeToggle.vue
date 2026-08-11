<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from '@/composables/useTheme'

const { isDark, toggleTheme } = useTheme()

// La etiqueta describe la accion, no el estado actual.
const label = computed(() => (isDark.value ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'))
</script>

<template>
  <button
    type="button"
    :title="label"
    :aria-label="label"
    class="w-8 h-8 flex items-center justify-center rounded-md text-muted-foreground
           hover:text-foreground hover:bg-muted transition-colors"
    @click="toggleTheme"
  >
    <i :class="isDark ? 'fa-solid fa-sun' : 'fa-solid fa-moon'" class="text-xs"></i>
  </button>
</template>

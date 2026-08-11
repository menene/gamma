<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { refreshUser } from '@/composables/useAuth'

const route = useRoute()

// Revalida la sesion al cargar: el usuario guardado puede traer datos viejos,
// entre ellos el rol con el que se decide mostrar la seccion de administracion.
onMounted(refreshUser)
</script>

<template>
  <div class="min-h-screen bg-background text-foreground">
    <Navbar v-if="route.path !== '/login'" />
    <main>
      <RouterView />
    </main>
  </div>
</template>

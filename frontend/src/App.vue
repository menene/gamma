<script setup lang="ts">
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'

const route = useRoute()
</script>

<template>
  <div class="min-h-screen bg-background text-foreground">
    <Navbar v-if="route.path !== '/login'" />
    <main>
      <RouterView />
    </main>
  </div>
</template>

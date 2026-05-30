<script setup lang="ts">
import Navbar from '@/components/Navbar.vue'
</script>

<template>
  <div class="min-h-screen bg-background text-foreground">
    <Navbar />
    <main>
      <RouterView />
    </main>
  </div>
</template>

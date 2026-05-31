<script setup lang="ts">
import { API_BASE } from '@/config'

const docsUrl = `${API_BASE}/docs`
</script>

<template>
  <section class="h-[calc(100vh-4rem)]">
    <iframe
      :src="docsUrl"
      class="w-full h-full border-0"
      title="Swagger UI"
    />
  </section>
</template>

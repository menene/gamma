<script setup lang="ts">
import { API_BASE } from '@/config'

const isLocal = window.location.hostname === 'localhost'
const docsUrl = isLocal ? `${API_BASE}/docs` : '/swagger-ui'
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

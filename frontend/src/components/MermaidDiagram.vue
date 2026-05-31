<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import mermaid from 'mermaid'

const props = defineProps<{ chart: string }>()

const el = ref<HTMLDivElement | null>(null)
const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`

mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  fontFamily: 'inherit',
})

async function render() {
  if (!el.value) return
  const { svg } = await mermaid.render(id, props.chart)
  el.value.innerHTML = svg
}

onMounted(render)
watch(() => props.chart, render)
</script>

<template>
  <div ref="el" class="overflow-x-auto [&_svg]:max-w-full [&_svg]:h-auto"></div>
</template>

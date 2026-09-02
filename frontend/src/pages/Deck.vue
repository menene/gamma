<script setup lang="ts">
import { Button } from '@/components/ui/button'

// El deck no se compila con el frontend: vive en docs/presentation y se monta
// como volumen, de modo que editar el HTML se refleja recargando la pagina, sin
// reconstruir la imagen. Por eso se referencia por URL y no por import.
const DECK_URL = '/deck/presentation.html'

function abrirAparte() {
  window.open(DECK_URL, '_blank', 'noopener')
}
</script>

<template>
  <section class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex items-start justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Presentacion</h1>
        <p class="text-sm text-muted-foreground mt-1">
          Modelos, experimento y modelo ganador
        </p>
      </div>

      <Button variant="outline" class="shrink-0" @click="abrirAparte">
        <i class="fa-solid fa-up-right-from-square mr-2"></i>
        Abrir aparte
      </Button>
    </div>

    <div class="rounded-lg border border-border overflow-hidden bg-white">
      <iframe
        :src="DECK_URL"
        title="Presentacion GAMMA"
        class="w-full block"
        style="height: calc(100vh - 260px); min-height: 460px"
        allowfullscreen
      ></iframe>
    </div>

    <p class="text-xs text-muted-foreground mt-3">
      Dentro del deck: <span class="font-medium">flechas</span> para navegar,
      <span class="font-medium">F</span> pantalla completa,
      <span class="font-medium">Esc</span> vista general.
      Para el modo presentador con las notas hay que abrirlo aparte y pulsar
      <span class="font-medium">S</span>: la ventana de notas no puede abrirse desde el marco incrustado.
    </p>
  </section>
</template>

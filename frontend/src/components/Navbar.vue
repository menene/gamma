<script setup lang="ts">
import { computed, ref, watch, useTemplateRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const route = useRoute()
const { user, isAuthenticated, isAdmin, logout } = useAuth()

// Orden fijo de la barra. `admin` marca los que solo ve un administrador;
// ocultarlos es comodidad de interfaz, porque la ruta y el API validan el rol
// por su cuenta.
const navLinks = [
  { label: 'Arquitectura', to: '/arquitectura', icon: 'fa-solid fa-cubes', admin: true },
  { label: 'Referencia', to: '/referencia', icon: 'fa-solid fa-book', admin: true },
  { label: 'Datos', to: '/datos', icon: 'fa-solid fa-database', admin: false },
  { label: 'Lab', to: '/lab', icon: 'fa-solid fa-flask', admin: true },
  { label: 'Modelo', to: '/modelo', icon: 'fa-solid fa-brain', admin: true },
]

const links = computed(() => {
  if (!isAuthenticated.value) return []
  return navLinks.filter(l => !l.admin || isAdmin.value)
})

// ── Menu de la cuenta ───────────────────────────────────────────────────────
const menuAbierto = ref(false)
const menuRef = useTemplateRef<HTMLElement>('menuRef')
onClickOutside(menuRef, () => { menuAbierto.value = false })

function irA(destino: string) {
  menuAbierto.value = false
  router.push(destino)
}

// ── Menu movil ──────────────────────────────────────────────────────────────
// Debajo de 768 px la barra horizontal no cabe, asi que se colapsa en un panel.
const movilAbierto = ref(false)

// Navegar debe cerrarlo: si no, el panel tapa la pagina recien abierta.
watch(() => route.fullPath, () => { movilAbierto.value = false })

function handleLogout() {
  menuAbierto.value = false
  movilAbierto.value = false
  logout()
  router.push('/login')
}
</script>

<template>
  <nav class="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
    <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
      <RouterLink to="/" class="font-bold text-xl tracking-tight">GAMMA</RouterLink>

      <!-- Controles compactos: debajo de md la barra horizontal no cabe -->
      <div class="flex md:hidden items-center gap-1">
        <ThemeToggle />
        <button
          type="button"
          class="w-9 h-9 flex items-center justify-center rounded-md text-muted-foreground
                 hover:text-foreground hover:bg-muted transition-colors"
          :aria-expanded="movilAbierto"
          aria-label="Menu"
          @click="movilAbierto = !movilAbierto"
        >
          <i :class="movilAbierto ? 'fa-solid fa-xmark' : 'fa-solid fa-bars'"></i>
        </button>
      </div>

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

        <template v-if="isAuthenticated">
          <Button as-child class="ml-2 px-3 py-2 h-auto">
            <a href="/chat" rel="noopener" class="flex items-center gap-2 text-sm">
              <i class="fa-solid fa-robot"></i>
              Chat
            </a>
          </Button>

          <Separator orientation="vertical" class="mx-2 h-6" />

          <!-- Ayuda: disponible para cualquier usuario, como icono -->
          <RouterLink
            to="/ayuda"
            title="Ayuda"
            aria-label="Ayuda"
            class="w-8 h-8 flex items-center justify-center rounded-md text-muted-foreground
                   hover:text-foreground hover:bg-muted transition-colors"
            active-class="text-foreground bg-muted"
          >
            <i class="fa-solid fa-circle-question text-xs"></i>
          </RouterLink>

          <ThemeToggle />

          <!-- Menu de la cuenta -->
          <div ref="menuRef" class="relative ml-1">
            <button
              type="button"
              class="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs text-muted-foreground
                     hover:text-foreground hover:bg-muted transition-colors"
              :aria-expanded="menuAbierto"
              aria-haspopup="menu"
              @click="menuAbierto = !menuAbierto"
            >
              {{ user?.name }}
              <i
                class="fa-solid fa-chevron-down text-[9px] transition-transform"
                :class="{ 'rotate-180': menuAbierto }"
              ></i>
            </button>

            <div
              v-if="menuAbierto"
              role="menu"
              class="absolute right-0 mt-1.5 w-52 rounded-md border bg-popover shadow-md py-1 z-50"
            >
              <div class="px-3 py-2">
                <p class="text-sm font-medium leading-tight truncate">{{ user?.name }}</p>
                <p class="text-xs text-muted-foreground truncate">{{ user?.email }}</p>
              </div>

              <Separator />

              <button
                v-if="isAdmin"
                type="button"
                role="menuitem"
                class="w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors flex items-center gap-2"
                @click="irA('/usuarios')"
              >
                <i class="fa-solid fa-users text-xs text-muted-foreground w-4"></i>
                Administrar
              </button>

              <button
                type="button"
                role="menuitem"
                class="w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors flex items-center gap-2"
                @click="handleLogout"
              >
                <i class="fa-solid fa-right-from-bracket text-xs text-muted-foreground w-4"></i>
                Cerrar sesion
              </button>
            </div>
          </div>
        </template>

        <template v-else>
          <ThemeToggle class="ml-2" />
          <Button as-child variant="outline" class="ml-2 px-3 py-2 h-auto">
            <RouterLink to="/login" class="flex items-center gap-2 text-sm">
              <i class="fa-solid fa-right-to-bracket"></i>
              Iniciar sesion
            </RouterLink>
          </Button>
        </template>
      </div>
    </div>

    <!-- Panel movil -->
    <div v-if="movilAbierto" class="md:hidden border-t border-border bg-background">
      <div class="px-4 py-3 space-y-1">
        <template v-if="isAuthenticated">
          <a
            href="/chat"
            rel="noopener"
            class="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium
                   bg-primary text-primary-foreground"
          >
            <i class="fa-solid fa-robot w-4 text-center"></i>
            Chat
          </a>

          <RouterLink
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-muted-foreground
                   hover:text-foreground hover:bg-muted transition-colors"
            active-class="text-foreground bg-muted"
          >
            <i :class="link.icon" class="w-4 text-center text-xs"></i>
            {{ link.label }}
          </RouterLink>

          <RouterLink
            to="/ayuda"
            class="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-muted-foreground
                   hover:text-foreground hover:bg-muted transition-colors"
            active-class="text-foreground bg-muted"
          >
            <i class="fa-solid fa-circle-question w-4 text-center text-xs"></i>
            Ayuda
          </RouterLink>

          <Separator class="my-2" />

          <div class="px-3 py-1">
            <p class="text-sm font-medium leading-tight truncate">{{ user?.name }}</p>
            <p class="text-xs text-muted-foreground truncate">{{ user?.email }}</p>
          </div>

          <RouterLink
            v-if="isAdmin"
            to="/usuarios"
            class="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-muted-foreground
                   hover:text-foreground hover:bg-muted transition-colors"
            active-class="text-foreground bg-muted"
          >
            <i class="fa-solid fa-users w-4 text-center text-xs"></i>
            Administrar
          </RouterLink>

          <button
            type="button"
            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-muted-foreground
                   hover:text-foreground hover:bg-muted transition-colors"
            @click="handleLogout"
          >
            <i class="fa-solid fa-right-from-bracket w-4 text-center text-xs"></i>
            Cerrar sesion
          </button>
        </template>

        <RouterLink
          v-else
          to="/login"
          class="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium
                 bg-primary text-primary-foreground"
        >
          <i class="fa-solid fa-right-to-bracket w-4 text-center"></i>
          Iniciar sesion
        </RouterLink>
      </div>
    </div>
  </nav>
</template>

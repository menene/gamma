<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { login, register } = useAuth()

const isRegister = ref(false)
const email = ref('')
const name = ref('')
const password = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  success.value = ''
  loading.value = true

  const result = isRegister.value
    ? await register(email.value, name.value, password.value)
    : await login(email.value, password.value)

  loading.value = false

  if (result.ok) {
    if (isRegister.value) {
      success.value = result.message || 'Cuenta creada. Un administrador debe activar tu cuenta.'
      isRegister.value = false
      email.value = ''
      name.value = ''
      password.value = ''
    } else {
      router.push('/')
    }
  } else {
    error.value = result.error || 'Error desconocido'
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-background px-4">
    <Card class="w-full max-w-sm">
      <CardContent class="pt-6 space-y-6">
        <div class="text-center space-y-1">
          <h1 class="text-2xl font-bold tracking-tight">GAMMA</h1>
          <p class="text-sm text-muted-foreground">
            {{ isRegister ? 'Crear cuenta' : 'Iniciar sesion' }}
          </p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div v-if="isRegister" class="space-y-1">
            <label class="text-sm font-medium">Nombre</label>
            <input
              v-model="name"
              type="text"
              required
              placeholder="Tu nombre"
              class="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div class="space-y-1">
            <label class="text-sm font-medium">Email</label>
            <input
              v-model="email"
              type="email"
              required
              placeholder="email@ejemplo.com"
              class="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div class="space-y-1">
            <label class="text-sm font-medium">Password</label>
            <input
              v-model="password"
              type="password"
              required
              placeholder="********"
              class="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div v-if="success" class="text-sm text-green-600 bg-green-500/10 border border-green-500/20 rounded-md px-3 py-2">
            <i class="fa-solid fa-circle-check mr-1"></i>
            {{ success }}
          </div>

          <div v-if="error" class="text-sm text-red-500 bg-red-500/10 border border-red-500/20 rounded-md px-3 py-2">
            {{ error }}
          </div>

          <Button type="submit" class="w-full" :disabled="loading">
            <i v-if="loading" class="fa-solid fa-spinner fa-spin mr-2"></i>
            {{ isRegister ? 'Registrarse' : 'Iniciar sesion' }}
          </Button>
        </form>

        <div class="text-center">
          <button
            type="button"
            class="text-sm text-muted-foreground hover:text-foreground transition-colors"
            @click="isRegister = !isRegister; error = ''"
          >
            {{ isRegister ? 'Ya tengo cuenta' : 'Crear cuenta nueva' }}
          </button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { API_BASE } from '@/config'
import { authFetch, useAuth } from '@/composables/useAuth'

interface Usuario {
  id: number
  email: string
  name: string
  admin: boolean
  is_active: boolean
  created_at: string | null
  deleted_at: string | null
}

const { user: actual } = useAuth()
const API = `${API_BASE}/api/users`

const usuarios = ref<Usuario[]>([])
const incluirBajas = ref(false)
const cargando = ref(false)
const error = ref<string | null>(null)
const aviso = ref<string | null>(null)

// null = ninguno abierto · 'nuevo' = alta · number = edicion de esa cuenta
const editando = ref<number | 'nuevo' | null>(null)
const confirmandoBaja = ref<number | null>(null)

const form = ref({ email: '', name: '', password: '', admin: false, is_active: true })

const vigentes = computed(() => usuarios.value.filter(u => !u.deleted_at))
const bajas = computed(() => usuarios.value.filter(u => u.deleted_at))

function fecha(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-GT', { day: '2-digit', month: 'short', year: 'numeric' })
}

function limpiar() {
  form.value = { email: '', name: '', password: '', admin: false, is_active: true }
  editando.value = null
}

async function cargar() {
  cargando.value = true
  error.value = null
  try {
    const r = await authFetch(`${API}?include_deleted=${incluirBajas.value}`)
    if (!r.ok) throw new Error('No se pudo consultar el listado de cuentas')
    usuarios.value = await r.json()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error de conexion'
  } finally {
    cargando.value = false
  }
}

function abrirNuevo() {
  limpiar()
  editando.value = 'nuevo'
}

function abrirEdicion(u: Usuario) {
  // La contrasena se deja en blanco: solo se envia si el administrador escribe una.
  form.value = { email: u.email, name: u.name, password: '', admin: u.admin, is_active: u.is_active }
  editando.value = u.id
}

async function guardar() {
  cargando.value = true
  error.value = null
  aviso.value = null
  try {
    const esNuevo = editando.value === 'nuevo'
    const cuerpo: Record<string, unknown> = {
      email: form.value.email,
      name: form.value.name,
      admin: form.value.admin,
      is_active: form.value.is_active,
    }
    if (form.value.password) cuerpo.password = form.value.password

    const r = await authFetch(esNuevo ? API : `${API}/${editando.value}`, {
      method: esNuevo ? 'POST' : 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cuerpo),
    })
    const data = await r.json()
    if (!r.ok) throw new Error(detalle(data))
    aviso.value = esNuevo ? `Cuenta de ${data.name} creada` : `Cuenta de ${data.name} actualizada`
    limpiar()
    await cargar()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error de conexion'
  } finally {
    cargando.value = false
  }
}

async function darDeBaja(u: Usuario) {
  confirmandoBaja.value = null
  cargando.value = true
  error.value = null
  aviso.value = null
  try {
    const r = await authFetch(`${API}/${u.id}`, { method: 'DELETE' })
    const data = await r.json()
    if (!r.ok) throw new Error(detalle(data))
    aviso.value = data.message
    await cargar()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error de conexion'
  } finally {
    cargando.value = false
  }
}

async function restaurar(u: Usuario) {
  cargando.value = true
  error.value = null
  aviso.value = null
  try {
    const r = await authFetch(`${API}/${u.id}/restore`, { method: 'POST' })
    const data = await r.json()
    if (!r.ok) throw new Error(detalle(data))
    aviso.value = `Cuenta de ${data.name} restaurada`
    await cargar()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Error de conexion'
  } finally {
    cargando.value = false
  }
}

// El API devuelve el motivo en `detail`; Pydantic lo entrega como lista.
function detalle(data: unknown): string {
  const d = (data as { detail?: unknown })?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d) && d.length) return String((d[0] as { msg?: string })?.msg ?? d[0])
  return 'No se pudo completar la operacion'
}

const formValido = computed(() => {
  const f = form.value
  if (!f.email.trim() || !f.name.trim()) return false
  if (editando.value === 'nuevo' && f.password.length < 8) return false
  if (f.password && f.password.length < 8) return false
  return true
})

onMounted(cargar)
</script>

<template>
  <section class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex items-start justify-between mb-8 gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Usuarios</h1>
        <p class="text-sm text-muted-foreground mt-1">
          Alta, modificacion y baja de cuentas de acceso
        </p>
      </div>
      <Button v-if="editando === null" class="gap-2 shrink-0" @click="abrirNuevo">
        <i class="fa-solid fa-plus text-xs"></i>
        Nueva cuenta
      </Button>
    </div>

    <div v-if="error" class="mb-6 rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm">
      <i class="fa-solid fa-triangle-exclamation mr-2"></i>{{ error }}
    </div>
    <div v-if="aviso" class="mb-6 rounded-md border px-4 py-3 text-sm text-muted-foreground">
      <i class="fa-solid fa-circle-check mr-2"></i>{{ aviso }}
    </div>

    <!-- Formulario de alta / edicion -->
    <Card v-if="editando !== null" class="mb-8">
      <CardHeader class="pb-3">
        <CardTitle class="text-base">
          {{ editando === 'nuevo' ? 'Nueva cuenta' : 'Editar cuenta' }}
        </CardTitle>
        <CardDescription v-if="editando !== 'nuevo'">
          Deje la contrasena en blanco para conservar la actual.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div class="grid sm:grid-cols-2 gap-4">
          <div>
            <label class="text-xs font-medium text-muted-foreground block mb-1.5">Nombre</label>
            <Input v-model="form.name" placeholder="Nombre completo" />
          </div>
          <div>
            <label class="text-xs font-medium text-muted-foreground block mb-1.5">Correo</label>
            <Input v-model="form.email" type="email" placeholder="persona@empresa.com" />
          </div>
          <div class="sm:col-span-2">
            <label class="text-xs font-medium text-muted-foreground block mb-1.5">
              Contrasena
              <span class="font-normal">({{ editando === 'nuevo' ? 'minimo 8 caracteres' : 'dejar en blanco para no cambiarla' }})</span>
            </label>
            <Input v-model="form.password" type="password" placeholder="••••••••" autocomplete="new-password" />
          </div>
        </div>

        <Separator class="my-4" />

        <div class="flex flex-col sm:flex-row sm:items-center gap-4">
          <label class="flex items-center gap-2 text-sm cursor-pointer">
            <input v-model="form.admin" type="checkbox" class="rounded" />
            <span>Administrador</span>
          </label>
          <label class="flex items-center gap-2 text-sm cursor-pointer">
            <input v-model="form.is_active" type="checkbox" class="rounded" />
            <span>Cuenta habilitada</span>
          </label>
        </div>
        <p class="text-xs text-muted-foreground mt-2">
          Un administrador ve las secciones tecnicas y de administracion. Su actividad se
          excluye de los indicadores, por lo que no conviene usar cuentas administrativas
          para la gestion diaria de materiales.
        </p>

        <div class="flex gap-2 mt-5">
          <Button :disabled="cargando || !formValido" @click="guardar">
            {{ editando === 'nuevo' ? 'Crear cuenta' : 'Guardar cambios' }}
          </Button>
          <Button variant="outline" :disabled="cargando" @click="limpiar">Cancelar</Button>
        </div>
      </CardContent>
    </Card>

    <!-- Listado -->
    <div class="flex items-baseline justify-between mb-4">
      <h2 class="text-base font-semibold tracking-tight">
        Cuentas vigentes
        <span class="text-xs font-normal text-muted-foreground ml-1">{{ vigentes.length }}</span>
      </h2>
      <label class="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
        <input v-model="incluirBajas" type="checkbox" class="rounded" @change="cargar" />
        Mostrar cuentas dadas de baja
      </label>
    </div>

    <Card>
      <CardContent class="pt-5">
        <p v-if="!usuarios.length && !cargando" class="text-sm text-muted-foreground">
          No hay cuentas registradas.
        </p>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-xs text-muted-foreground border-b">
                <th class="text-left font-medium py-2">Nombre</th>
                <th class="text-left font-medium py-2">Correo</th>
                <th class="text-left font-medium py-2">Rol</th>
                <th class="text-left font-medium py-2">Estado</th>
                <th class="text-left font-medium py-2">Alta</th>
                <th class="text-right font-medium py-2"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="u in vigentes"
                :key="u.id"
                class="border-b last:border-0"
              >
                <td class="py-2.5">
                  {{ u.name }}
                  <span v-if="u.id === actual?.id" class="text-xs text-muted-foreground ml-1">(usted)</span>
                </td>
                <td class="py-2.5 text-muted-foreground">{{ u.email }}</td>
                <td class="py-2.5">
                  <Badge v-if="u.admin" class="text-xs">Administrador</Badge>
                  <span v-else class="text-xs text-muted-foreground">Gestor</span>
                </td>
                <td class="py-2.5">
                  <span v-if="u.is_active" class="text-xs text-muted-foreground">Habilitada</span>
                  <Badge v-else variant="secondary" class="text-xs">Deshabilitada</Badge>
                </td>
                <td class="py-2.5 text-xs text-muted-foreground">{{ fecha(u.created_at) }}</td>
                <td class="py-2.5 text-right whitespace-nowrap">
                  <template v-if="confirmandoBaja !== u.id">
                    <Button size="sm" variant="ghost" class="text-xs h-7" @click="abrirEdicion(u)">
                      Editar
                    </Button>
                    <Button
                      v-if="u.id !== actual?.id"
                      size="sm" variant="ghost" class="text-xs h-7 text-destructive"
                      :disabled="cargando"
                      @click="confirmandoBaja = u.id"
                    >Dar de baja</Button>
                  </template>
                  <span v-else class="inline-flex gap-1 items-center">
                    <span class="text-xs text-muted-foreground mr-1">¿Confirma?</span>
                    <Button size="sm" class="text-xs h-7" :disabled="cargando" @click="darDeBaja(u)">Si</Button>
                    <Button size="sm" variant="ghost" class="text-xs h-7" @click="confirmandoBaja = null">No</Button>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Cuentas dadas de baja -->
        <template v-if="incluirBajas && bajas.length">
          <Separator class="my-5" />
          <p class="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
            Dadas de baja · {{ bajas.length }}
          </p>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <tbody>
                <tr v-for="u in bajas" :key="u.id" class="border-b last:border-0 text-muted-foreground">
                  <td class="py-2.5">{{ u.name }}</td>
                  <td class="py-2.5">{{ u.email }}</td>
                  <td class="py-2.5 text-xs">Baja el {{ fecha(u.deleted_at) }}</td>
                  <td class="py-2.5 text-right">
                    <Button size="sm" variant="outline" class="text-xs h-7"
                            :disabled="cargando" @click="restaurar(u)">Restaurar</Button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="text-xs text-muted-foreground mt-3">
            Las cuentas dadas de baja no pueden iniciar sesion, pero su historial de
            solicitudes se conserva. El correo queda libre para volver a usarse.
          </p>
        </template>
      </CardContent>
    </Card>
  </section>
</template>

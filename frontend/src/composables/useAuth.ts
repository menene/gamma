import { ref, computed } from 'vue'
import { API_BASE } from '@/config'

interface User {
  id: number
  email: string
  name: string
}

const token = ref<string | null>(localStorage.getItem('gamma_token'))
const user = ref<User | null>(JSON.parse(localStorage.getItem('gamma_user') || 'null'))

export const isAuthenticated = computed(() => !!token.value)

export function getToken() {
  return token.value
}

export function authHeaders(): Record<string, string> {
  if (!token.value) return {}
  return { Authorization: `Bearer ${token.value}` }
}

export async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers)
  if (token.value) headers.set('Authorization', `Bearer ${token.value}`)
  const res = await fetch(url, { ...options, headers })
  if (res.status === 401 || res.status === 403) {
    logout()
    window.location.href = '/login'
  }
  return res
}

export async function login(email: string, password: string): Promise<{ ok: boolean; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({ detail: 'Error de conexion' }))
      return { ok: false, error: data.detail }
    }
    const data = await res.json()
    token.value = data.token
    user.value = data.user
    localStorage.setItem('gamma_token', data.token)
    localStorage.setItem('gamma_user', JSON.stringify(data.user))
    return { ok: true }
  } catch {
    return { ok: false, error: 'Error de conexion con el servidor' }
  }
}

export async function register(email: string, name: string, password: string): Promise<{ ok: boolean; error?: string; message?: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, name, password }),
    })
    const data = await res.json().catch(() => ({ detail: 'Error de conexion' }))
    if (!res.ok) {
      return { ok: false, error: data.detail }
    }
    return { ok: true, message: data.message }
  } catch {
    return { ok: false, error: 'Error de conexion con el servidor' }
  }
}

export function logout() {
  token.value = null
  user.value = null
  localStorage.removeItem('gamma_token')
  localStorage.removeItem('gamma_user')
}

export function useAuth() {
  return { token, user, isAuthenticated, login, register, logout, authFetch, authHeaders, getToken }
}

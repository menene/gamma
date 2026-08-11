import { ref, computed, watch } from 'vue'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'gamma_theme'

/**
 * Tema inicial: la preferencia guardada si existe, y si no la del sistema
 * operativo. La clase se aplica sobre <html>, que es donde la espera el
 * `@custom-variant dark` definido en style.css.
 */
function initialTheme(): Theme {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(value: Theme) {
  document.documentElement.classList.toggle('dark', value === 'dark')
}

const theme = ref<Theme>(initialTheme())

export const isDark = computed(() => theme.value === 'dark')

applyTheme(theme.value)

watch(theme, (value) => {
  applyTheme(value)
  localStorage.setItem(STORAGE_KEY, value)
})

export function setTheme(value: Theme) {
  theme.value = value
}

export function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
}

// Sigue los cambios del sistema mientras el usuario no haya elegido de forma
// explicita. Una vez que elige, su preferencia manda.
window.matchMedia?.('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  if (!localStorage.getItem(STORAGE_KEY)) {
    theme.value = e.matches ? 'dark' : 'light'
  }
})

export function useTheme() {
  return { theme, isDark, setTheme, toggleTheme }
}

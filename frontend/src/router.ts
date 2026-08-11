import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated, isAdmin, refreshUser } from '@/composables/useAuth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/pages/Login.vue'), meta: { public: true } },
    { path: '/', component: () => import('@/pages/Presentacion.vue'), meta: { public: true } },
    { path: '/arquitectura', component: () => import('@/pages/Arquitectura.vue'), meta: { public: true } },
    { path: '/datos', component: () => import('@/pages/Datos.vue') },
    { path: '/referencia', component: () => import('@/pages/Referencia.vue') },
    { path: '/lab', component: () => import('@/pages/Lab.vue') },
    { path: '/ayuda', component: () => import('@/pages/Ayuda.vue') },
    { path: '/chat', component: () => import('@/pages/Chat.vue') },
    { path: '/admin', component: () => import('@/pages/Admin.vue'), meta: { admin: true } },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  if (!isAuthenticated.value) return '/login'

  if (to.meta.admin) {
    // El rol guardado en el navegador puede estar desfasado, de modo que se
    // revalida contra el API antes de conceder el paso. Aun asi, esta
    // comprobacion es solo de navegacion: cada ruta de administracion del API
    // vuelve a validar el rol del lado del servidor, por lo que entrar por URL
    // directa no da acceso a nada.
    await refreshUser()
    if (!isAdmin.value) return '/'
  }

  return true
})

export default router

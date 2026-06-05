import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '@/composables/useAuth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/pages/Login.vue'), meta: { public: true } },
    { path: '/', component: () => import('@/pages/Presentacion.vue'), meta: { public: true } },
    { path: '/arquitectura', component: () => import('@/pages/Arquitectura.vue'), meta: { public: true } },
    { path: '/datos', component: () => import('@/pages/Datos.vue') },
    { path: '/referencia', component: () => import('@/pages/Referencia.vue') },
    { path: '/lab', component: () => import('@/pages/Lab.vue') },
    { path: '/chat', component: () => import('@/pages/Chat.vue') },
  ],
})

router.beforeEach((to) => {
  if (to.meta.public) return true
  if (!isAuthenticated.value) return '/login'
  return true
})

export default router

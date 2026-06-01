import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '@/composables/useAuth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/pages/Login.vue'), meta: { public: true } },
    { path: '/', component: () => import('@/pages/Presentacion.vue'), meta: { public: true } },
    { path: '/arquitectura', component: () => import('@/pages/Arquitectura.vue'), meta: { public: true } },
    { path: '/laboratorio', component: () => import('@/pages/Laboratorio.vue') },
    { path: '/swagger', component: () => import('@/pages/Api.vue') },
    { path: '/etl', component: () => import('@/pages/Etl.vue') },
    { path: '/docs', component: () => import('@/pages/Docs.vue') },
    { path: '/chat', component: () => import('@/pages/Chat.vue') },
  ],
})

router.beforeEach((to) => {
  if (to.meta.public) return true
  if (!isAuthenticated.value) return '/login'
  return true
})

export default router

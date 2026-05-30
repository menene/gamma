import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('@/pages/Presentacion.vue') },
    { path: '/arquitectura', component: () => import('@/pages/Arquitectura.vue') },
    { path: '/laboratorio', component: () => import('@/pages/Laboratorio.vue') },
    { path: '/api', component: () => import('@/pages/Api.vue') },
    { path: '/docs', component: () => import('@/pages/Docs.vue') },
    { path: '/chat', component: () => import('@/pages/Chat.vue') },
  ],
})

export default router

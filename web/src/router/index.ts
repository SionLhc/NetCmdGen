import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/Home.vue'),
    },
    {
      path: '/generate',
      name: 'Generator',
      component: () => import('@/views/Generator.vue'),
    },
    {
      path: '/topology',
      name: 'Topology',
      component: () => import('@/views/TopologyEditor.vue'),
    },
    {
      path: '/tools',
      name: 'Tools',
      component: () => import('@/views/Tools.vue'),
    },
    {
      path: '/diagnostics',
      name: 'Diagnostics',
      component: () => import('@/views/Diagnostics.vue'),
    },
    {
      path: '/manual',
      name: 'Manual',
      component: () => import('@/views/Manual.vue'),
    },
  ],
})

export default router

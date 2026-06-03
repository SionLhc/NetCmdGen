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
      component: () => import('@/views/Diagnostics.vue'),
      children: [
        {
          path: '',
          name: 'Diagnostics',
          component: () => import('@/views/diagnostics/Index.vue'),
        },
        {
          path: 'ping',
          name: 'DiagnosticsPing',
          component: () => import('@/views/diagnostics/PingDiagnostic.vue'),
        },
        {
          path: 'traceroute',
          name: 'DiagnosticsTrace',
          component: () => import('@/views/diagnostics/TraceDiagnostic.vue'),
        },
        // ── 以下功能开发中，路由守卫阻止直接访问 ──────────────
        {
          path: 'dns',
          name: 'DiagnosticsDns',
          component: () => import('@/views/diagnostics/DnsDiagnostic.vue'),
          beforeEnter: () => { return { path: '/diagnostics', query: { unavailable: 'dns' } } },
        },
        {
          path: 'tcp-port',
          name: 'DiagnosticsTcpPort',
          component: () => import('@/views/diagnostics/TcpPortDiagnostic.vue'),
          beforeEnter: () => { return { path: '/diagnostics', query: { unavailable: 'tcp-port' } } },
        },
        {
          path: 'http',
          name: 'DiagnosticsHttp',
          component: () => import('@/views/diagnostics/HttpDiagnostic.vue'),
          beforeEnter: () => { return { path: '/diagnostics', query: { unavailable: 'http' } } },
        },
        {
          path: 'mtu',
          name: 'DiagnosticsMtu',
          component: () => import('@/views/diagnostics/MtuDiagnostic.vue'),
          beforeEnter: () => { return { path: '/diagnostics', query: { unavailable: 'mtu' } } },
        },
        {
          path: 'jitter',
          name: 'DiagnosticsJitter',
          component: () => import('@/views/diagnostics/JitterDiagnostic.vue'),
          beforeEnter: () => { return { path: '/diagnostics', query: { unavailable: 'jitter' } } },
        },
        {
          path: 'history',
          name: 'DiagnosticsHistory',
          component: () => import('@/views/diagnostics/HistoryDiagnostic.vue'),
          beforeEnter: () => { return { path: '/diagnostics', query: { unavailable: 'history' } } },
        },
      ],
    },
    {
      path: '/manual',
      name: 'Manual',
      component: () => import('@/views/Manual.vue'),
    },
  ],
})

export default router

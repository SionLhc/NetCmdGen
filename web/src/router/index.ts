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
        {
          path: 'dns',
          name: 'DiagnosticsDns',
          component: () => import('@/views/diagnostics/DnsDiagnostic.vue'),
        },
        {
          path: 'tcp-port',
          name: 'DiagnosticsTcpPort',
          component: () => import('@/views/diagnostics/TcpPortDiagnostic.vue'),
        },
        {
          path: 'http',
          name: 'DiagnosticsHttp',
          component: () => import('@/views/diagnostics/HttpDiagnostic.vue'),
        },
        {
          path: 'mtu',
          name: 'DiagnosticsMtu',
          component: () => import('@/views/diagnostics/MtuDiagnostic.vue'),
        },
        {
          path: 'jitter',
          name: 'DiagnosticsJitter',
          component: () => import('@/views/diagnostics/JitterDiagnostic.vue'),
        },
        {
          path: 'history',
          name: 'DiagnosticsHistory',
          component: () => import('@/views/diagnostics/HistoryDiagnostic.vue'),
        },
      ],
    },
    {
      path: '/manual',
      name: 'Manual',
      component: () => import('@/views/Manual.vue'),
    },
    {
      path: '/ssh',
      name: 'SshTerminal',
      component: () => import('@/views/SshTerminal.vue'),
    },
  ],
})

export default router

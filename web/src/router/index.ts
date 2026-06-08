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
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
    },
    {
      path: '/ipam',
      name: 'Ipam',
      component: () => import('@/views/Ipam.vue'),
    },
    {
      path: '/batch',
      name: 'BatchCmd',
      component: () => import('@/views/BatchCmd.vue'),
    },
    {
      path: '/backup',
      name: 'Backup',
      component: () => import('@/views/Backup.vue'),
    },
    {
      path: '/health',
      name: 'Health',
      component: () => import('@/views/Health.vue'),
    },
    {
      path: '/scheduler',
      name: 'Scheduler',
      component: () => import('@/views/Scheduler.vue'),
    },
    {
      path: '/alert',
      name: 'Alert',
      component: () => import('@/views/Alert.vue'),
    },
    {
      path: '/bigscreen',
      name: 'BigScreen',
      component: () => import('@/views/BigScreen.vue'),
    },
    {
      path: '/security',
      name: 'Security',
      component: () => import('@/views/Security.vue'),
    },
    {
      path: '/rack',
      name: 'Rack',
      component: () => import('@/views/Rack.vue'),
    },
    {
      path: '/switch-protect',
      redirect: '/health',  // 交换机防护合并到网络巡检
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
    {
      path: '/ros',
      redirect: '/bigscreen',  // SNMP 监控已深度整合到态势大屏
    },
  ],
})

export default router

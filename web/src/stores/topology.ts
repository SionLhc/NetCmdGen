import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface DeviceType {
  type: string
  name: string
  icon: string
  color: string
  role: string
}

export interface NodeData {
  id: string
  type: string
  vendor: string
  hostname: string
  role: string
  mgmtSubnet?: string
  mgmtIp?: string
  stpPriority?: number
  ospfRouterId?: string
  uplinkPorts?: number
  downlinkPorts?: number
  accessPorts?: number
  defaultVlan?: number
  poeEnabled?: boolean
}

export interface LinkData {
  id: string
  source: string
  target: string
  sourcePort?: string
  targetPort?: string
  linkType: 'access' | 'trunk' | 'hybrid'
  vlanId?: number
  allowedVlans?: number[]
  bandwidth?: string
}

export const useTopologyStore = defineStore('topology', () => {
  // 设备类型定义
  const deviceTypes = ref<DeviceType[]>([
    { type: 'core-switch', name: '核心交换机', icon: '🔷', color: '#409eff', role: 'core-switch' },
    { type: 'agg-switch', name: '汇聚交换机', icon: '🔶', color: '#e6a23c', role: 'agg-switch' },
    { type: 'access-switch', name: '接入交换机', icon: '🟢', color: '#67c23a', role: 'access-switch' },
    { type: 'router', name: '路由器', icon: '🔴', color: '#f56c6c', role: 'router' },
    { type: 'firewall', name: '防火墙', icon: '🛡️', color: '#909399', role: 'firewall' },
    { type: 'server', name: '服务器', icon: '🖥️', color: '#606266', role: 'server' },
    { type: 'pc', name: '终端PC', icon: '💻', color: '#c0c4cc', role: 'pc' },
  ])

  // 当前选中的节点
  const selectedNode = ref<any>(null)
  
  // 当前选中的连线
  const selectedEdge = ref<any>(null)

  // 生成的配置输出
  const configOutput = ref('')

  // 是否正在生成配置
  const generating = ref(false)

  return {
    deviceTypes,
    selectedNode,
    selectedEdge,
    configOutput,
    generating,
  }
})

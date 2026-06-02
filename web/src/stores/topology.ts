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

/** 设备级配置输出项 */
export interface DeviceOutput {
  device: string
  vendor: string
  vendorName: string
  output: string
  lines: number
  error?: boolean
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

  // 生成的配置输出（兼容旧版单文本）
  const configOutput = ref('')

  // 是否正在生成配置
  const generating = ref(false)

  /** 设备级输出列表：每台设备一行 */
  const deviceOutputs = ref<DeviceOutput[]>([])
  /** 当前选中的输出设备 Tab 索引 */
  const activeOutputDevice = ref(0)
  /** 当前选择的厂商 */
  const outputVendor = ref('huawei')

  /** 从拓扑画布导出的设备列表（供命令工作台消费） */
  const exportedDevices = ref<TopologyDevice[]>([])
  /** 从拓扑画布导出的连线列表 */
  const exportedEdges = ref<TopologyEdgeExport[]>([])

  return {
    deviceTypes,
    selectedNode,
    selectedEdge,
    configOutput,
    generating,
    deviceOutputs,
    activeOutputDevice,
    outputVendor,
    exportedDevices,
    exportedEdges,
  }
})

/** 拓扑设备快照，供命令工作台导入 */
export interface TopologyDevice {
  id: string
  type: string
  typeName: string
  hostname: string
  mgmtIp: string
  vlans: string
  description: string
  /** 从连线收集的端口信息：{ interface, remoteDevice, linkType, vlanId, ipNetwork }[] */
  ports: TopologyPort[]
  /** 拓扑画布中的坐标（供拓扑图模式还原布局） */
  x?: number
  y?: number
}

/** 设备端口连接信息 */
export interface TopologyPort {
  interface: string
  remoteDevice: string
  remotePort: string
  linkType: string
  vlanId?: number
  allowedVlans?: number[]
  ipNetwork?: string
  bandwidth?: string
  /** 该端口是上行(uplink)还是下行(downlink) */
  direction: 'uplink' | 'downlink'
}

/** 拓扑连线导出数据 */
export interface TopologyEdgeExport {
  source: string    // 源设备 hostname
  target: string    // 目标设备 hostname
  linkType: string
  vlanId?: number
  bandwidth?: string
  sourcePort?: string
  targetPort?: string
}

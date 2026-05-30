/**
 * 配置生成器（前端组装）
 * 将拓扑分析结果转换为后端 API 所需的参数格式
 */

import type { TopologyNode, TopologyEdge, TopologyAnalysis } from './topologyAnalyzer'

export interface DeviceConfigParams {
  deviceId: string
  vendor: string
  hostname: string
  role: string
  mgmtIp: string
  vlans: Array<{ id: number; name: string }>
  interfaces: Array<{
    interface: string
    description: string
    linkType: string
    vlanId?: number
    allowedVlans?: number[]
  }>
  routing?: {
    type: 'static' | 'ospf'
    routes?: Array<{ dest: string; mask: string; nexthop: string }>
    ospf?: {
      processId: number
      routerId: string
      networks: Array<{ network: string; wildcard: string; area: string }>
    }
  }
  stp?: {
    mode: 'stp' | 'rstp' | 'mstp'
    priority: number
  }
}

/**
 * 收集网络中所有 VLAN
 */
function collectVlans(edges: TopologyEdge[]): Array<{ id: number; name: string }> {
  const vlanSet = new Set<number>()
  
  edges.forEach(edge => {
    if (edge.vlanId) vlanSet.add(edge.vlanId)
    if (edge.allowedVlans) {
      edge.allowedVlans.forEach(vlan => vlanSet.add(vlan))
    }
  })

  return Array.from(vlanSet).map(vlanId => ({
    id: vlanId,
    name: `VLAN${vlanId}`,
  }))
}

/**
 * 推导路由配置
 */
function deriveRouting(node: TopologyNode, analysis: TopologyAnalysis) {
  // 核心交换机：配置 OSPF
  if (node.role === 'core-switch') {
    return {
      type: 'ospf' as const,
      ospf: {
        processId: 1,
        routerId: analysis.ipPlan[node.id] || '1.1.1.1',
        networks: [
          {
            network: node.mgmtSubnet?.split('/')[0] || '192.168.1.0',
            wildcard: '0.0.0.255',
            area: '0.0.0.0',
          },
        ],
      },
    }
  }

  // 接入交换机：配置默认路由指向核心
  if (node.role === 'access-switch') {
    const coreNode = Object.entries(analysis.hierarchy)
      .find(([_, children]) => children.includes(node.id))
    
    if (coreNode) {
      const coreIp = analysis.ipPlan[coreNode[0]]
      return {
        type: 'static' as const,
        routes: [
          {
            dest: '0.0.0.0',
            mask: '0.0.0.0',
            nexthop: coreIp || '192.168.1.1',
          },
        ],
      }
    }
  }

  return undefined
}

/**
 * 推导 STP 配置
 */
function deriveSTP(node: TopologyNode) {
  if (node.role === 'core-switch') {
    return {
      mode: 'mstp' as const,
      priority: 4096,
    }
  }
  
  if (node.role === 'agg-switch') {
    return {
      mode: 'mstp' as const,
      priority: 8192,
    }
  }

  return {
    mode: 'mstp' as const,
    priority: 32768,
  }
}

/**
 * 为所有设备生成配置参数
 */
export function buildConfigParams(
  nodes: TopologyNode[],
  edges: TopologyEdge[],
  analysis: TopologyAnalysis
): DeviceConfigParams[] {
  const vlans = collectVlans(edges)

  return nodes.map(node => ({
    deviceId: node.id,
    vendor: node.vendor || 'huawei',
    hostname: node.hostname || node.id,
    role: node.role,
    mgmtIp: analysis.ipPlan[node.id] || '192.168.1.1',
    vlans,
    interfaces: analysis.interfaceMap[node.id] || [],
    routing: deriveRouting(node, analysis),
    stp: deriveSTP(node),
  }))
}

/**
 * 格式化配置输出
 */
export function formatConfigOutput(
  configs: Array<{ device: string; vendor: string; output: string }>
): string {
  const sections: string[] = []

  configs.forEach((config, index) => {
    sections.push(`# ========================================`)
    sections.push(`# 设备: ${config.device}`)
    sections.push(`# 厂商: ${config.vendor}`)
    sections.push(`# 生成时间: ${new Date().toLocaleString('zh-CN')}`)
    sections.push(`# ========================================`)
    sections.push('')
    sections.push(config.output)
    sections.push('')
  })

  return sections.join('\n')
}

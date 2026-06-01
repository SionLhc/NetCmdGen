/**
 * 网络拓扑分析引擎
 * 负责：IP自动分配、层次关系构建、接口配置推导
 */

export interface TopologyNode {
  id: string
  type: string
  role: string
  vendor: string
  hostname: string
  mgmtSubnet?: string
}

export interface TopologyEdge {
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

export interface IPAssignment {
  [nodeId: string]: string
}

export interface InterfaceConfig {
  interface: string
  description: string
  linkType: string
  vlanId?: number
  allowedVlans?: number[]
}

export interface TopologyAnalysis {
  ipPlan: IPAssignment
  hierarchy: Record<string, string[]> // nodeId -> children nodeIds
  interfaceMap: Record<string, InterfaceConfig[]>
}

/**
 * IP 地址计数器
 */
class IPCounter {
  private baseIP: number[]
  private counter: number

  constructor(cidr: string) {
    const [ip, prefix] = cidr.split('/')
    this.baseIP = ip.split('.').map(Number)
    this.counter = 1 // 从 .1 开始分配
  }

  next(): string {
    const ip = [...this.baseIP]
    ip[3] = this.counter++
    return ip.join('.')
  }
}

/**
 * 自动分配 IP 地址
 * 算法：广度优先遍历，核心层先分配，然后汇聚层，最后接入层
 */
export function assignIPs(nodes: TopologyNode[], edges: TopologyEdge[], coreSubnet: string): IPAssignment {
  const ipPlan: IPAssignment = {}
  const ipCounter = new IPCounter(coreSubnet)

  // 1. 找出所有核心交换机
  const coreNodes = nodes.filter(n => n.role === 'core-switch')
  
  // 2. 为核心交换机分配 IP（.1, .2, ...）
  coreNodes.forEach(node => {
    ipPlan[node.id] = ipCounter.next()
  })

  // 3. 广度优先遍历分配其他层
  const queue = [...coreNodes]
  const visited = new Set(coreNodes.map(n => n.id))

  while (queue.length > 0) {
    const current = queue.shift()!
    
    // 找出所有与当前节点相连的未访问节点
    const neighbors = edges
      .filter(e => e.source === current.id || e.target === current.id)
      .map(e => e.source === current.id ? e.target : e.source)
      .filter(id => !visited.has(id))

    // 按角色优先级排序（汇聚 > 接入 > 其他）
    const rolePriority: Record<string, number> = {
      'agg-switch': 1,
      'access-switch': 2,
      'router': 3,
      'firewall': 4,
    }

    const neighborNodes = neighbors
      .map(id => nodes.find(n => n.id === id)!)
      .sort((a, b) => (rolePriority[a.role] || 99) - (rolePriority[b.role] || 99))

    // 为邻居节点分配 IP
    neighborNodes.forEach(node => {
      visited.add(node.id)
      ipPlan[node.id] = ipCounter.next()
      queue.push(node)
    })
  }

  return ipPlan
}

/**
 * 构建层次关系（父节点 -> 子节点列表）
 */
export function buildHierarchy(nodes: TopologyNode[], edges: TopologyEdge[]): Record<string, string[]> {
  const hierarchy: Record<string, string[]> = {}

  // 初始化所有节点的子节点列表
  nodes.forEach(node => {
    hierarchy[node.id] = []
  })

  // 根据连线建立父子关系
  edges.forEach(edge => {
    const sourceNode = nodes.find(n => n.id === edge.source)
    const targetNode = nodes.find(n => n.id === edge.target)

    if (!sourceNode || !targetNode) return

    // 判断哪个是父节点（角色优先级高的为父）
    const rolePriority: Record<string, number> = {
      'core-switch': 1,
      'agg-switch': 2,
      'access-switch': 3,
      'router': 4,
      'firewall': 5,
    }

    const sourcePriority = rolePriority[sourceNode.role] || 99
    const targetPriority = rolePriority[targetNode.role] || 99

    if (sourcePriority < targetPriority) {
      // source 是父节点
      hierarchy[sourceNode.id].push(targetNode.id)
    } else if (targetPriority < sourcePriority) {
      // target 是父节点
      hierarchy[targetNode.id].push(sourceNode.id)
    } else {
      // 同层级，双向连接
      hierarchy[sourceNode.id].push(targetNode.id)
      hierarchy[targetNode.id].push(sourceNode.id)
    }
  })

  return hierarchy
}

/**
 * 推导接口配置
 * 根据连线和设备角色，自动生成接口配置
 */
export function deriveInterfaces(nodes: TopologyNode[], edges: TopologyEdge[]): Record<string, InterfaceConfig[]> {
  const interfaceMap: Record<string, InterfaceConfig[]> = {}

  // 初始化所有节点的接口列表
  nodes.forEach(node => {
    interfaceMap[node.id] = []
  })

  // 为每条连线推导接口配置
  edges.forEach((edge, index) => {
    const sourceNode = nodes.find(n => n.id === edge.source)
    const targetNode = nodes.find(n => n.id === edge.target)

    if (!sourceNode || !targetNode) return

    // 推导源设备接口
    const sourcePort = edge.sourcePort || `GigabitEthernet0/0/${index + 1}`
    const targetHostname = targetNode.hostname || targetNode.id
    const sourceDesc = edge.linkType === 'trunk' 
      ? `Uplink to ${targetHostname} (Trunk)`
      : `Uplink to ${targetHostname} (Access VLAN ${edge.vlanId})`

    if (!interfaceMap[sourceNode.id]) interfaceMap[sourceNode.id] = []
    interfaceMap[sourceNode.id].push({
      interface: sourcePort,
      description: sourceDesc,
      linkType: edge.linkType,
      vlanId: edge.linkType === 'access' ? edge.vlanId : undefined,
      allowedVlans: edge.linkType === 'trunk' ? edge.allowedVlans : undefined,
    })

    // 推导目标设备接口
    const targetPort = edge.targetPort || `GigabitEthernet0/0/${index + 1}`
    const sourceHostname = sourceNode.hostname || sourceNode.id
    const targetDesc = edge.linkType === 'trunk'
      ? `Downlink to ${sourceHostname} (Trunk)`
      : `Downlink to ${sourceHostname} (Access VLAN ${edge.vlanId})`

    if (!interfaceMap[targetNode.id]) interfaceMap[targetNode.id] = []
    interfaceMap[targetNode.id].push({
      interface: targetPort,
      description: targetDesc,
      linkType: edge.linkType,
      vlanId: edge.linkType === 'access' ? edge.vlanId : undefined,
      allowedVlans: edge.linkType === 'trunk' ? edge.allowedVlans : undefined,
    })
  })

  return interfaceMap
}

/**
 * 完整拓扑分析
 */
export function analyzeTopology(
  nodes: TopologyNode[],
  edges: TopologyEdge[],
  coreSubnet: string = '192.168.1.0/24'
): TopologyAnalysis {
  const ipPlan = assignIPs(nodes, edges, coreSubnet)
  const hierarchy = buildHierarchy(nodes, edges)
  const interfaceMap = deriveInterfaces(nodes, edges)

  return { ipPlan, hierarchy, interfaceMap }
}

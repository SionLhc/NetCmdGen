import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// ── 厂商 ─────────────────────────────────────────────
export interface VendorInfo {
  code: string
  name: string
  features: string[]
}

export const getVendors = () =>
  api.get<{ vendors: VendorInfo[] }>('/vendors').then((r) => r.data.vendors)

// ── 命令生成 ─────────────────────────────────────────
export interface GenerateReq {
  vendor: string
  feature: string
  params: Record<string, unknown>
}

export interface GenerateFullReq {
  vendor: string
  config: Record<string, unknown>
  vrp_version?: 'v5' | 'v8' | 'v300' | 'v7' | 'v6'  // v5/v8/v300=华为, v7=华三, v6/v7=RouterOS
  topology_context?: Record<string, unknown>
  scene?: 'campus_core' | 'campus_access' | 'campus_agg'
}

export interface GenerateResp {
  vendor: string
  feature?: string
  output: string
}

export const generate = (req: GenerateReq) =>
  api.post<GenerateResp>('/generate', req).then((r) => r.data)

export const generateFull = (req: GenerateFullReq) =>
  api.post<GenerateResp>('/generate/full', req).then((r) => r.data)

// ── 园区网配置生成 ──────────────────────────────
export interface CampusGenerateReq {
  vendor: string
  hostname: string
  mgmt_ip: string
  vlans: Array<{ id: number; name: string }>
  interfaces: Array<{
    interface: string
    description: string
    linkType: string
    vlanId?: number
    allowedVlans?: number[]
  }>
  routing?: {
    type: string
    routes?: Array<{ dest: string; mask: string; nexthop: string }>
    ospf?: {
      processId: number
      routerId: string
      networks: Array<{ network: string; wildcard: string; area: string }>
    }
  }
  stp?: {
    mode: string
    priority: number
  }
  scene: 'campus_core' | 'campus_access' | 'campus_agg'
}

export const generateCampusConfig = (req: CampusGenerateReq) => {
  const { scene, ...rest } = req
  return generateFull({
    vendor: req.vendor,
    config: rest,
    scene,
  })
}

// ── 命令速查 ─────────────────────────────────────────
export interface ManualItem {
  category: string
  name: string
  command: string
  description: string
  example: string
  versions?: string[]  // 版本标记，undefined 表示全版本通用
}

export interface ManualVersion {
  code: string
  name: string
}

export const getManualList = (vendor: string, keyword = '', version = 'all') =>
  api
    .get<{ items: ManualItem[]; total: number; version: string }>(`/manual/${vendor}`, {
      params: { keyword, version },
    })
    .then((r) => r.data)

export const getManualVersions = (vendor: string) =>
  api
    .get<{ vendor: string; versions: ManualVersion[] }>(`/manual/${vendor}/versions`)
    .then((r) => r.data.versions)

export const getManualTree = (vendor: string) =>
  api.get<{ tree: Record<string, unknown> }>(`/manual/${vendor}/tree`).then((r) => r.data.tree)

// ── 网络工具 ──────────────────────────────────────────
export const calcSubnet = (ip: string, mask: string) =>
  api.get('/tools/subnet', { params: { ip, mask } }).then((r) => r.data)

export const splitSubnet = (network: string, prefix: number, newPrefix: number) =>
  api.get('/tools/subnet/split', { params: { network, prefix, new_prefix: newPrefix } }).then((r) => r.data)

export const rangeToCidr = (start: string, end: string) =>
  api.get('/tools/subnet/range-to-cidr', { params: { start, end } }).then((r) => r.data)

// ─── 网络工具（新版 /net/* API）────────────────────────
export const doPing = (host: string, count = 4, timeout = 2) =>
  api.get('/net/ping', { params: { target: host, count, timeout } }).then((r) => r.data)

export const doPortScan = (host: string, ports: string, timeout = 1.0) =>
  api.get('/net/portscan', { params: { target: host, ports, timeout } }).then((r) => r.data)

export const doTrace = (host: string, maxHops = 30, timeout = 2) =>
  api.get('/net/traceroute', { params: { target: host, max_hops: maxHops, timeout } }).then((r) => r.data)

export const doDns = (domain: string, recordType = 'A') =>
  api.get('/net/dns', { params: { domain, record_type: recordType } }).then((r) => r.data)

export const doWhois = (domain: string) =>
  api.get('/tools/whois', { params: { domain } }).then((r) => r.data)

/** 流式 Ping — 每包实时推送，返回 AbortController 用于取消 */
export const doPingStream = (
  target: string, count: number, timeout: number,
  onProgress: (data: any) => void,
  onDone: (data: any) => void,
  onError: (err: any) => void,
): AbortController => {
  const controller = new AbortController()
  const params = new URLSearchParams({ target, count: String(count), timeout: String(timeout) })
  fetch(`/api/net/ping/stream?${params}`, { signal: controller.signal })
    .then(async (res) => {
      const reader = res.body?.getReader()
      if (!reader) { onError(new Error('无法读取流')); return }
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          const match = line.match(/^data: (.+)$/m)
          if (match) {
            try {
              const data = JSON.parse(match[1])
              if (data.progress) onProgress(data)
              else onDone(data)
            } catch {}
          }
        }
      }
    })
    .catch((e) => { if (e.name !== 'AbortError') onError(e) })
  return controller
}

/** 流式 Traceroute — 逐跳实时推送，返回 AbortController 用于取消 */
export const doTraceStream = (
  target: string, maxHops: number, timeout: number, probesPerHop: number,
  onProgress: (data: any) => void,
  onDone: (data: any) => void,
  onError: (err: any) => void,
): AbortController => {
  const controller = new AbortController()
  const params = new URLSearchParams({
    target,
    max_hops: String(maxHops),
    timeout: String(timeout),
    probes_per_hop: String(probesPerHop),
  })
  fetch(`/api/net/traceroute/stream?${params}`, { signal: controller.signal })
    .then(async (res) => {
      const reader = res.body?.getReader()
      if (!reader) { onError(new Error('无法读取流')); return }
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          const match = line.match(/^data: (.+)$/m)
          if (match) {
            try {
              const data = JSON.parse(match[1])
              if (data.progress) onProgress(data)
              else onDone(data)
            } catch {}
          }
        }
      }
    })
    .catch((e) => { if (e.name !== 'AbortError') onError(e) })
  return controller
}

// ─── 拓扑持久化（服务器文件存储）───────────────────────
export interface TopoItem {
  id: string
  name: string
  created_at?: string
  updated_at?: string
}
export const getTopoList = () =>
  api.get<{ items: TopoItem[] }>('/topologies').then(r => r.data.items)
export const createTopo = (name: string) =>
  api.post<{ id: string; name: string }>('/topologies', { name }).then(r => r.data)
export const getTopoData = (id: string) =>
  api.get<{ id: string; data: any }>(`/topologies/${id}`).then(r => r.data)
export const saveTopoData = (id: string, data: any) =>
  api.put(`/topologies/${id}`, { data }).then(r => r.data)
export const renameTopo = (id: string, new_name: string) =>
  api.patch(`/topologies/${id}/rename`, null, { params: { new_name } }).then(r => r.data)
export const deleteTopo = (id: string) =>
  api.delete(`/topologies/${id}`).then(r => r.data)
export const importTopo = (data: any) =>
  api.post<{ id: string; name: string }>('/topologies/import', { data }).then(r => r.data)

export default api

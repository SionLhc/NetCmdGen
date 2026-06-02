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

export default api

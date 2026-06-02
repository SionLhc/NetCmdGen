<template>
  <div class="project-page">
    <!-- 顶部工具栏 -->
    <div class="pj-toolbar">
      <span class="pj-title">📁 拓扑项目管理</span>
      <el-input v-model="searchText" placeholder="搜索项目或设备名..." clearable size="default" style="width:220px" />
      <!-- 视图切换 -->
      <el-radio-group v-model="viewMode" size="default" style="margin-left:8px">
        <el-radio-button value="list">📋 列表</el-radio-button>
        <el-radio-button value="topo">🗺 拓扑图</el-radio-button>
      </el-radio-group>
      <div style="margin-left:auto;display:flex;gap:8px">
        <el-button type="primary" size="default" @click="handleExportAll" :disabled="!hasAnyCommand">导出 MD</el-button>
        <el-button size="default" plain @click="handleImportFromTopo" :disabled="topoStore.exportedDevices.length===0">从拓扑导入({{ topoStore.exportedDevices.length }})</el-button>
      </div>
    </div>

    <!-- 列表视图 -->
    <div v-if="viewMode==='list'" class="pj-body">
      <div v-if="filteredProjects.length===0" class="pj-empty">📋<p>暂无项目</p></div>
      <div v-for="proj in filteredProjects" :key="proj.id" class="pj-card">
        <div class="pj-card-header" @click="proj.expanded=!proj.expanded">
          <div class="pj-card-info">
            <span class="pj-card-name">📁 {{ proj.name }}</span>
            <span class="pj-card-meta">{{ proj.createdAt }} · {{ proj.devices.length }}台 · {{ doneCount(proj) }}/{{ proj.devices.length }}已生成</span>
          </div>
          <div class="pj-card-actions" @click.stop>
            <el-button link size="small" type="primary" @click="openTopoProject(proj)">🗺 拓扑图</el-button>
            <el-button link size="small" type="danger" @click="handleDeleteProject(proj.id)">删除</el-button>
            <span style="color:#909399;font-size:12px">{{ proj.expanded?'▲':'▼' }}</span>
          </div>
        </div>
        <div v-show="proj.expanded" class="pj-device-table">
          <el-table :data="proj.devices" size="small">
            <el-table-column prop="hostname" label="主机名" min-width="110" />
            <el-table-column label="类型" width="100"><template #default="{row}"><el-tag :type="typeTag(row.type)" size="small">{{ row.typeName }}</el-tag></template></el-table-column>
            <el-table-column label="厂商" width="90"><template #default="{row}"><span v-if="row.vendor" style="font-size:12px">{{ vendorLabel(row.vendor) }}</span><span v-else style="color:#c0c4cc">—</span></template></el-table-column>
            <el-table-column label="状态" width="100"><template #default="{row}"><el-tag v-if="row.generatedOutput" type="success" size="small">✅{{ row.generatedLines }}行</el-tag><el-tag v-else type="info" size="small">⏳</el-tag></template></el-table-column>
            <el-table-column label="操作" min-width="240"><template #default="{row,$index}">
              <div style="display:flex;align-items:center;gap:4px">
                <el-select v-model="row._vendor" size="small" style="width:85px" @click.stop><el-option v-for="v in vendors" :key="v.code" :label="v.name" :value="v.code"/></el-select>
                <el-button link type="primary" size="small" :loading="generatingKey==='${proj.id}_${$index}'" @click.stop="genOne(proj,$index)">生成</el-button>
                <el-button link size="small" v-if="row.generatedOutput" @click.stop="viewOutput(row)">查看</el-button>
                <el-button link type="danger" size="small" @click.stop="removeDevice(proj,$index)">删除</el-button>
              </div>
            </template></el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- 拓扑图视图 -->
    <div v-else class="pj-topo-body">
      <div class="pj-topo-left">
        <div class="pj-topo-bar">
          <el-select v-model="activeProjectId" size="default" placeholder="选择项目" style="width:240px" @change="onProjectChange">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id"/>
          </el-select>
          <span class="pj-topo-hint" v-if="activeProject">
            {{ activeProject.devices.length }}台 · 点击设备可多选
          </span>
          <span class="pj-topo-selected" v-if="selectedDevices.length">
            已选: {{ selectedDevices.map(d=>d.hostname).join('、') }}
          </span>
        </div>
        <ProjectCanvas
          :devices="canvasDevices"
          :edges="canvasEdges"
          :positions="canvasPositions"
          @select="onCanvasSelect"
          style="flex:1;min-height:0"
        />
      </div>
      <!-- 右侧配置面板 -->
      <div class="pj-topo-right" :class="{ active: selectedDevices.length>0 }">
        <div class="pj-config-header">
          <span>⚙ 配置参数</span>
          <el-select v-model="targetVendor" size="small" style="width:100px">
            <el-option v-for="v in vendors" :key="v.code" :label="v.name" :value="v.code"/>
          </el-select>
        </div>
        <div class="pj-config-body" v-if="selectedDevices.length>0">
          <el-tabs v-model="configTab" type="card" size="small">
            <el-tab-pane label="基础" name="basic"><BasicForm v-model="formBasic"/></el-tab-pane>
            <el-tab-pane label="VLAN" name="vlan"><VlanForm v-model="formVlan"/></el-tab-pane>
            <el-tab-pane label="路由" name="routing"><RoutingForm v-model="formRouting"/></el-tab-pane>
            <el-tab-pane label="安全" name="security"><SecurityForm v-model="formSecurity"/></el-tab-pane>
            <el-tab-pane label="接口" name="interface"><InterfaceForm v-model="formInterface"/></el-tab-pane>
          </el-tabs>
          <div class="pj-config-actions">
            <el-button type="primary" size="default" @click="genSelected" :loading="generating" style="flex:1">
              为 {{ selectedDevices.length }} 台设备生成
            </el-button>
            <el-button size="default" @click="genAllProject" :loading="generating">
              生成全部
            </el-button>
            <el-button type="danger" size="default" @click="removeSelectedDevices" v-if="selectedDevices.length>0">
              删除选中 ({{ selectedDevices.length }})
            </el-button>
          </div>
        </div>
        <div v-else class="pj-config-empty">
          <span>👆 在左侧拓扑图中选择设备</span>
          <span style="font-size:12px;color:#909399">按住 Ctrl 点击可多选，同类型设备配置一致</span>
        </div>
      </div>
    </div>

    <!-- 查看命令弹窗 -->
    <el-dialog v-model="viewVisible" title="命令预览" width="700px" top="5vh">
      <pre class="pj-output-block"><code>{{ viewingOutput }}</code></pre>
      <template #footer>
        <el-button @click="viewVisible=false">关闭</el-button>
        <el-button type="primary" @click="copyViewOutput">复制</el-button>
      </template>
    </el-dialog>

    <!-- 导出预览 -->
    <el-dialog v-model="exportVisible" title="MD导出" width="800px" top="3vh">
      <pre style="white-space:pre-wrap;font-size:12px;max-height:500px;overflow:auto;background:#fafbfc;padding:16px;border-radius:6px">{{ mdPreview }}</pre>
      <template #footer>
        <el-button @click="exportVisible=false">关闭</el-button>
        <el-button type="primary" @click="confirmExport">下载.md</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTopologyStore, type TopologyDevice, type TopologyEdgeExport } from '@/stores/topology'
import { useVendorStore } from '@/stores/vendor'
import { generateFull as apiGenerateFull } from '@/api'
import ProjectCanvas from './ProjectCanvas.vue'
import BasicForm from './BasicForm.vue'
import VlanForm from './VlanForm.vue'
import RoutingForm from './RoutingForm.vue'
import SecurityForm from './SecurityForm.vue'
import InterfaceForm from './InterfaceForm.vue'

const topoStore = useTopologyStore()
const vendorStore = useVendorStore()
const vendors = computed(() => vendorStore.vendors)

onMounted(() => { if (vendorStore.vendors.length===0) vendorStore.loadVendors() })

const viewMode = ref<'list'|'topo'>('list')

// ─── 数据结构 ──────────────────────────────
interface DeviceCmd {
  hostname: string; type: string; typeName: string; mgmtIp: string; vlans: string
  ports?: any[]; vendor?: string; generatedOutput?: string; generatedLines?: number
  generatedAt?: string; _vendor?: string
}
interface TopoProj {
  id: string; name: string; createdAt: string; devices: DeviceCmd[]; expanded: boolean
  _edges?: any[]; _positions?: Record<string, {x:number;y:number}>
}
const STORAGE_KEY = 'netcmdgen_projects'
const searchText = ref('')
const projects = ref<TopoProj[]>(loadProjects())

function loadProjects(): TopoProj[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw).map((p: any) => ({
      ...p, expanded: false,
      devices: (p.devices||[]).map((d: any) => ({...d, _vendor: d.vendor||''})),
      _edges: p._edges || [],
      _positions: p._positions || {},
    }))
  } catch { return [] }
}
function saveProjects() {
  const toSave = projects.value.map(({expanded, ...r}) => ({
    ...r,
    devices: r.devices.map(({_vendor, _showPorts, ...d}: any) => d),
  }))
  localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
}

const filteredProjects = computed(() => {
  if (!searchText.value.trim()) return projects.value
  const kw = searchText.value.toLowerCase()
  return projects.value.filter(p => p.name.toLowerCase().includes(kw)||p.devices.some(d=>d.hostname.toLowerCase().includes(kw)))
})
function doneCount(p: TopoProj) { return p.devices.filter(d=>d.generatedOutput).length }
const hasAnyCommand = computed(() => projects.value.some(p=>p.devices.some(d=>d.generatedOutput)))
function typeTag(t: string) { return t.includes('core')?'':t.includes('router')?'danger':t.includes('firewall')?'warning':'success' }
function vendorLabel(c: string) { const m: Record<string,string> = {huawei:'华为',h3c:'H3C',ruijie:'锐捷',maipu:'迈普'}; return m[c]||c }

// ─── 列表模式：生成 ──────────────────────────
const generatingKey = ref('')
async function genOne(proj: TopoProj, i: number) {
  const dev = proj.devices[i]
  const vendor = dev._vendor || 'huawei'
  generatingKey.value = `${proj.id}_${i}`
  try {
    const cfg = buildConfig(dev)
    const res = await apiGenerateFull({ vendor, config: cfg as any })
    dev.generatedOutput = res.output; dev.generatedLines = res.output.split('\n').length
    dev.vendor = vendor; dev._vendor = vendor; dev.generatedAt = new Date().toLocaleString('zh-CN')
    saveProjects(); ElMessage.success(`${dev.hostname}: ${dev.generatedLines}行`)
  } catch(e: any) {
    dev.generatedOutput = `# 失败: ${e.response?.data?.detail||e.message}`; dev.generatedLines = 1
    ElMessage.error(`${dev.hostname} 失败`)
  } finally { generatingKey.value = '' }
}

// ─── 拓扑图模式 ──────────────────────────────
const activeProjectId = ref('')
const activeProject = computed(() => projects.value.find(p=>p.id===activeProjectId.value))
const selectedIds = ref<string[]>([])
const selectedDevices = computed(() => {
  if (!activeProject.value) return []
  return activeProject.value.devices.filter(d => selectedIds.value.includes(d.hostname))
})
const canvasDevices = computed(() => activeProject.value?.devices.map(d => ({
  id: d.hostname, hostname: d.hostname, type: d.type, typeName: d.typeName,
  vendor: d.vendor||'', mgmtIp: d.mgmtIp, vlans: d.vlans,
  generatedOutput: d.generatedOutput,
})) || [])
const canvasPositions = computed(() => activeProject.value?._positions || {})
const canvasEdges = computed(() => activeProject.value?._edges || [])

const targetVendor = ref('huawei')
const configTab = ref('basic')
const formBasic = ref<Record<string,any>>({})
const formVlan = ref<Record<string,any>>({})
const formRouting = ref<Record<string,any>>({})
const formSecurity = ref<Record<string,any>>({})
const formInterface = ref<Record<string,any>>({})

function openTopoProject(proj: TopoProj) {
  activeProjectId.value = proj.id
  onProjectChange() // 确保加载边和坐标
  viewMode.value = 'topo'
  selectedIds.value = []
}
function onProjectChange() {
  selectedIds.value = []
  // canvasPositions / canvasEdges 是 computed，自动从 activeProject 读取
}
function onCanvasSelect(ids: string[]) { selectedIds.value = ids }

// ─── 拓扑图模式：生成 ────────────────────────
const generating = ref(false)
async function genSelected() {
  if (!activeProject.value || selectedDevices.value.length === 0) { ElMessage.warning('请选择设备'); return }
  generating.value = true
  const cfg = buildConfigFromForms()
  let ok = 0
  for (const dev of selectedDevices.value) {
    try {
      // 合并设备特定信息
      const devCfg: Record<string,any> = { ...cfg, basic: { ...cfg.basic, hostname: dev.hostname, mgmt_ip: dev.mgmtIp } }
      devCfg.vlan = cfg.vlan?.vlans ? {
        vlans: cfg.vlan.vlans,
        interfaces: dev.vlans ? dev.vlans.split(',').filter(Boolean).map((id: string) => (
          { interface: `GigabitEthernet0/0/${id.trim()}`, type: 'access', vlan_id: parseInt(id.trim()) }
        )) : []
      } : {}
      const res = await apiGenerateFull({ vendor: targetVendor.value, config: devCfg as any })
      dev.generatedOutput = res.output; dev.generatedLines = res.output.split('\n').length
      dev.vendor = targetVendor.value; dev._vendor = targetVendor.value
      dev.generatedAt = new Date().toLocaleString('zh-CN')
      ok++
    } catch(e: any) { dev.generatedOutput = `# 失败: ${(e as Error).message}`; dev.generatedLines = 1 }
  }
  saveProjects(); generating.value = false
  ElMessage.success(`成功生成 ${ok}/${selectedDevices.value.length} 台`)
}
async function genAllProject() {
  if (!activeProject.value) return
  generating.value = true
  const cfg = buildConfigFromForms()
  let ok = 0
  for (const dev of activeProject.value.devices) {
    try {
      const devCfg: Record<string,any> = { ...cfg, basic: { ...cfg.basic, hostname: dev.hostname, mgmt_ip: dev.mgmtIp } }
      const res = await apiGenerateFull({ vendor: targetVendor.value, config: devCfg as any })
      dev.generatedOutput = res.output; dev.generatedLines = res.output.split('\n').length
      dev.vendor = targetVendor.value; dev._vendor = targetVendor.value
      dev.generatedAt = new Date().toLocaleString('zh-CN'); ok++
    } catch(e: any) { dev.generatedOutput = `# 失败: ${(e as Error).message}`; dev.generatedLines = 1 }
  }
  saveProjects(); generating.value = false
  ElMessage.success(`成功生成 ${ok}/${activeProject.value.devices.length} 台`)
}

// ─── 工具函数 ──────────────────────────────
function buildConfig(dev: DeviceCmd): Record<string,any> {
  const vlans = dev.vlans ? dev.vlans.split(',').map(v=>parseInt(v.trim())).filter(v=>!isNaN(v)) : []
  return {
    basic: { hostname: dev.hostname, mgmt_ip: dev.mgmtIp||'', enable_ssh: true, ssh_port: 22 },
    vlan: vlans.length>0 ? { vlans: vlans.map((id:number)=>({id,name:`VLAN${id}`})), interfaces: vlans.map((id:number)=>({interface:`GigabitEthernet0/0/${id}`,type:'access',vlan_id:id})) } : {},
    routing: {}, security: {}, interface: dev.ports && dev.ports.length>0 ? {
      eth_trunks: (dev.ports||[]).filter((p:any)=>p.direction==='uplink').map((p:any,i:number)=>({trunk_id:i+1,mode:p.linkType==='trunk'?'lacp-static':'manual',member_ports:[p.interface],description:`To-${p.remoteDevice}`})),
      lldp: {enable:true}
    } : {},
  }
}
function buildConfigFromForms(): Record<string,any> {
  const cfg: Record<string,any> = {
    basic: { ...formBasic.value },
    vlan: { ...formVlan.value },
    routing: { ...formRouting.value },
    security: { ...formSecurity.value },
    interface: { ...formInterface.value },
  }
  return cfg
}

// ─── 查看/导出 ─────────────────────────────
const viewVisible = ref(false); const viewingOutput = ref('')
function viewOutput(dev: DeviceCmd) { viewingOutput.value = dev.generatedOutput || ''; viewVisible.value = true }
function copyViewOutput() { navigator.clipboard.writeText(viewingOutput.value); ElMessage.success('已复制') }

const exportVisible = ref(false); const mdPreview = ref('')
function buildMarkdown(): string {
  const lines = ['# 网络设备配置导出\n']
  for (const p of projects.value) {
    if (!p.devices.some(d=>d.generatedOutput)) continue
    lines.push(`\n## ${p.name}\n`)
    for (const d of p.devices.filter(d=>d.generatedOutput))
      lines.push(`### ${d.typeName}: ${d.hostname}\n\`\`\`\n${d.generatedOutput}\n\`\`\`\n`)
  }
  return lines.join('\n')
}
function handleExportAll() { mdPreview.value = buildMarkdown(); exportVisible.value = true }
function confirmExport() {
  const md = buildMarkdown()
  const blob = new Blob([md],{type:'text/markdown'})
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href=url; a.download=`NetCmdGen_${new Date().toISOString().slice(0,10)}.md`; a.click()
  URL.revokeObjectURL(url); exportVisible.value = false; ElMessage.success('已导出')
}

// ─── 导入/删除 ─────────────────────────────
function handleImportFromTopo() {
  const devices = topoStore.exportedDevices
  if (devices.length===0) { ElMessage.warning('请先在拓扑编辑器导出'); return }
  const projId = `proj_${Date.now()}`
  // 记录设备坐标
  const posMap: Record<string,{x:number;y:number}> = {}
  for (const d of devices) {
    if (d.x !== undefined && d.y !== undefined) {
      posMap[d.hostname] = { x: d.x, y: d.y }
    }
  }
  // 连线数据
  const importedEdges = topoStore.exportedEdges || []

  projects.value.unshift({
    id: projId, name: `拓扑项目${projects.value.length+1}`,
    createdAt: new Date().toLocaleString('zh-CN'),
    devices: devices.map(d => ({ hostname: d.hostname, type: d.type, typeName: d.typeName, mgmtIp: d.mgmtIp, vlans: d.vlans||'', ports: d.ports?.map(p=>({...p}))||[], _vendor: '' })),
    expanded: true,
    _edges: importedEdges,
    _positions: posMap,
  })
  saveProjects()
  ElMessage.success(`已导入 ${devices.length} 台设备`)
}
// 列表模式：删除单个设备
function removeDevice(proj: TopoProj, index: number) {
  const dev = proj.devices[index]
  proj.devices.splice(index, 1)
  saveProjects()
  ElMessage.success(`已删除 " ${dev.hostname}"`)
}

// 拓扑图模式：删除选中设备
function removeSelectedDevices() {
  if (!activeProject.value) return
  const ids = new Set(selectedIds.value)
  const before = activeProject.value.devices.length
  activeProject.value.devices = activeProject.value.devices.filter(d => !ids.has(d.hostname))
  // 清理相关连线和坐标
  if (activeProject.value._edges) {
    activeProject.value._edges = activeProject.value._edges.filter(
      e => !ids.has(e.source) && !ids.has(e.target)
    )
  }
  if (activeProject.value._positions) {
    for (const id of ids) delete activeProject.value._positions[id]
  }
  selectedIds.value = []
  saveProjects()
  ElMessage.success(`已删除 ${before - activeProject.value.devices.length} 台设备`)
}

function handleDeleteProject(id: string) {
  ElMessageBox.confirm('确定删除？','确认',{type:'warning'}).then(() => {
    projects.value = projects.value.filter(p=>p.id!==id)
    if (activeProjectId.value===id) { activeProjectId.value=''; viewMode.value='list' }
    saveProjects(); ElMessage.success('已删除')
  }).catch(()=>{})
}
</script>

<style scoped>
.project-page { height:100%;display:flex;flex-direction:column }
.pj-toolbar { display:flex;align-items:center;gap:12px;padding:14px 20px;background:#fff;border-bottom:1px solid #f0f0f0 }
.pj-title { font-size:17px;font-weight:700;color:#1e293b }
.pj-body { flex:1;overflow:auto;padding:16px 20px }
.pj-card { border:1px solid #ebeef5;border-radius:8px;margin-bottom:12px;overflow:hidden }
.pj-card-header { display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#fafbfc;cursor:pointer;user-select:none }
.pj-card-header:hover { background:#f0f2f5 }
.pj-card-info { display:flex;flex-direction:column;gap:4px }
.pj-card-name { font-size:15px;font-weight:600;color:#303133 }
.pj-card-meta { font-size:12px;color:#909399 }
.pj-card-actions { display:flex;align-items:center;gap:8px }
.pj-device-table { padding:8px 12px 12px }
.pj-empty { flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#94a3b8;gap:8px;font-size:14px }

/* 拓扑图视图 */
.pj-topo-body { flex:1;display:flex;overflow:hidden;min-height:0;background:#f8fafc }
.pj-topo-left { flex:1;display:flex;flex-direction:column;min-width:0;border-radius:12px 0 0 0;background:#fff;margin:12px 0 0 12px;border-radius:12px 0 0 0;box-shadow:0 1px 3px rgba(0,0,0,.04) }
.pj-topo-bar { display:flex;align-items:center;gap:12px;padding:12px 16px;background:#fff;border-bottom:1px solid #f1f5f9;border-radius:12px 0 0 0;flex-shrink:0;flex-wrap:wrap }
.pj-topo-hint { font-size:12px;color:#94a3b8 }
.pj-topo-selected { font-size:12px;color:#6366F1;font-weight:500;margin-left:auto;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap }
.pj-topo-right { width:340px;display:flex;flex-direction:column;border-left:1px solid #e2e8f0;background:#fff;overflow:hidden;margin:12px 12px 0 0;border-radius:0 12px 0 0;box-shadow:0 1px 3px rgba(0,0,0,.04);transition:border-color .2s }
.pj-topo-right.active { border-left-color:#6366F1 }
.pj-config-header { display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#fafbfc;border-bottom:1px solid #f1f5f9;font-weight:600;font-size:14px;color:#334155;flex-shrink:0 }
.pj-config-body { flex:1;overflow-y:auto;display:flex;flex-direction:column }
.pj-config-body :deep(.el-tabs__header) { margin:0;padding:0 8px;position:sticky;top:0;background:#fff;z-index:5 }
.pj-config-body :deep(.el-tabs__content) { padding:8px 12px;flex:1 }
.pj-config-actions { padding:10px 12px 16px;display:flex;gap:8px;border-top:1px solid #f1f5f9 }
.pj-config-empty { flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#94a3b8;gap:8px;font-size:14px;padding:20px }

.pj-output-block { background:#1a1b2e;color:#c9d1d9;padding:16px;margin:0;font-family:'JetBrains Mono',Consolas,monospace;font-size:12px;line-height:1.6;overflow:auto;max-height:400px;white-space:pre-wrap;border-radius:6px }
</style>

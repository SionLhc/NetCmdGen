<template>
  <div class="project-page">
    <!-- 顶部操作栏 -->
    <div class="pj-toolbar">
      <span class="pj-title">📁 拓扑项目管理</span>
      <el-input v-model="searchText" placeholder="搜索项目或设备名..." clearable size="default" style="width:260px" @input="onSearch" />
      <el-button type="primary" size="default" @click="handleExportAll" :disabled="!hasAnyCommand" style="margin-left:auto">
        一键导出全部命令 (MD)
      </el-button>
      <el-button size="default" plain @click="handleImportFromTopo" :disabled="topoStore.exportedDevices.length === 0">
        从拓扑导入 ({{ topoStore.exportedDevices.length }})
      </el-button>
    </div>

    <!-- 项目列表 -->
    <div class="pj-body" v-if="filteredProjects.length > 0">
      <div v-for="proj in filteredProjects" :key="proj.id" class="pj-card">
        <!-- 项目头 -->
        <div class="pj-card-header" @click="proj.expanded = !proj.expanded">
          <div class="pj-card-info">
            <span class="pj-card-name">📁 {{ proj.name }}</span>
            <span class="pj-card-meta">{{ proj.createdAt }} · {{ proj.devices.length }} 台设备 · {{ doneCount(proj) }}/{{ proj.devices.length }} 已生成</span>
          </div>
          <div class="pj-card-actions" @click.stop>
            <el-button link size="small" @click="handleDeleteProject(proj.id)" type="danger">删除项目</el-button>
            <span style="color:#909399;font-size:12px">{{ proj.expanded ? '▲' : '▼' }}</span>
          </div>
        </div>

        <!-- 设备表 -->
        <div v-show="proj.expanded" class="pj-device-table">
          <el-table :data="proj.devices" size="small">
            <el-table-column prop="hostname" label="主机名" min-width="120" />
            <el-table-column prop="typeName" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="typeTag(row.type)" size="small">{{ row.typeName }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="vendor" label="厂商" width="90">
              <template #default="{ row }">
                <span v-if="row.vendor" style="font-size:12px">{{ vendorLabel(row.vendor) }}</span>
                <span v-else style="color:#c0c4cc">—</span>
              </template>
            </el-table-column>
            <el-table-column label="连端口" width="80">
              <template #default="{ row }">
                <span v-if="row.ports && row.ports.length > 0" style="font-size:12px;color:#409eff;cursor:pointer" @click.stop="row._showPorts=!row._showPorts">{{ row.ports.length }} 个端口 {{ row._showPorts ? '▲' : '▼' }}</span>
                <span v-else style="color:#c0c4cc">—</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.generatedOutput" type="success" size="small">✅ {{ row.generatedLines || 0 }}行</el-tag>
                <el-tag v-else type="info" size="small">⏳ 待生成</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row, $index }">
                <el-button link type="primary" size="small"
                  @click="handleEditDevice(proj, $index)">生成命令</el-button>
                <el-button link size="small"
                  v-if="row.generatedOutput"
                  @click="handleViewOutput(row)">查看</el-button>
                <el-button link type="danger" size="small"
                  v-if="row.generatedOutput"
                  @click="handleClearDevice(proj, $index)">清空</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 端口详情 -->
          <div v-for="dev in proj.devices.filter(d => d._showPorts)" :key="'p-'+dev.hostname" style="margin:8px 12px 12px;background:#f8f9fb;border-radius:6px;padding:12px;font-size:12px">
            <div style="font-weight:600;color:#303133;margin-bottom:8px">{{ dev.hostname }} — 端口详情</div>
            <div v-if="dev.ports && dev.ports.length > 0" style="display:flex;flex-wrap:wrap;gap:6px">
              <div v-for="(p, i) in dev.ports" :key="i"
                style="flex:0 0 calc(50%-3px);background:#fff;border:1px solid #e8ecf1;border-radius:4px;padding:6px 8px;font-size:11px;line-height:1.5;min-width:200px">
                <div style="display:flex;justify-content:space-between">
                  <span><strong :style="{color: p.direction==='uplink'?'#409eff':'#e6a23c'}">{{ p.direction === 'uplink' ? '↑' : '↓' }}</strong> {{ p.interface || '—' }}</span>
                  <span style="color:#909399">{{ p.linkType }}</span>
                </div>
                <div style="color:#606266">↔ {{ p.remoteDevice }} : {{ p.remotePort || '—' }}</div>
                <div v-if="p.ipNetwork" style="color:#67c23a">IP: {{ p.ipNetwork }}</div>
                <div v-if="p.bandwidth && p.bandwidth !== '1G'" style="color:#e6a23c">{{ p.bandwidth }}</div>
              </div>
            </div>
            <div v-else style="color:#909399">无端口连接信息（未在拓扑中连线或连线未设标签）</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="pj-empty">
      <span style="font-size:48px;opacity:.3">📋</span>
      <p>暂无项目</p>
      <p style="font-size:12px;color:#909399">
        在拓扑编辑器中画好拓扑后，点击「导出到命令工作台」创建项目
      </p>
    </div>

    <!-- 查看命令弹窗 -->
    <el-dialog v-model="viewVisible" title="设备命令预览" width="700px" top="5vh">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;font-size:13px">
        <strong>{{ viewingDevice?.hostname }}</strong>
        <span style="color:#909399">{{ viewingDevice?.vendor }} — {{ viewingDevice?.generatedLines }} 行</span>
      </div>
      <pre class="pj-output-block"><code>{{ viewingDevice?.generatedOutput }}</code></pre>
      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
        <el-button type="primary" @click="copyViewOutput">复制</el-button>
      </template>
    </el-dialog>

    <!-- 导出预览 -->
    <el-dialog v-model="exportVisible" title="Markdown 导出预览" width="800px" top="3vh">
      <div style="max-height:500px;overflow:auto;border:1px solid #ebeef5;border-radius:6px;padding:16px;background:#fafbfc">
        <pre style="white-space:pre-wrap;font-size:12px;line-height:1.6;margin:0;color:#303133">{{ mdPreview }}</pre>
      </div>
      <template #footer>
        <el-button @click="exportVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleConfirmExport">下载 .md 文件</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, markRaw } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTopologyStore, type TopologyDevice } from '@/stores/topology'

const topoStore = useTopologyStore()

// ─── 项目数据结构 ──────────────────────────────────────
interface DeviceCommand {
  hostname: string
  type: string
  typeName: string
  mgmtIp: string
  vlans: string
  /** 从拓扑连线收集的端口信息 */
  ports?: Array<{
    interface: string; remoteDevice: string; remotePort: string
    linkType: string; vlanId?: number; allowedVlans?: number[]
    ipNetwork?: string; bandwidth?: string; direction: string
  }>
  vendor?: string
  generatedOutput?: string
  generatedLines?: number
  generatedAt?: string
}

interface TopologyProject {
  id: string
  name: string
  createdAt: string
  devices: DeviceCommand[]
  expanded: boolean
}

const STORAGE_KEY = 'netcmdgen_projects'
const searchText = ref('')

// 从 localStorage 加载项目
const projects = ref<TopologyProject[]>(
  markRaw(loadProjects())
)

function loadProjects(): TopologyProject[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw).map((p: any) => ({ ...p, expanded: false }))
  } catch { return [] }
}

function saveProjects() {
  // 去除 expanded 状态后再存储
  const toSave = projects.value.map(({ expanded, ...rest }) => rest)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
}

// ─── 过滤 ──────────────────────────────────────────────
const filteredProjects = computed(() => {
  if (!searchText.value.trim()) return projects.value
  const kw = searchText.value.toLowerCase()
  return projects.value.filter(p =>
    p.name.toLowerCase().includes(kw) ||
    p.devices.some(d => d.hostname.toLowerCase().includes(kw))
  )
})

function onSearch() { /* computed 自动生效 */ }

// ─── 状态计算 ──────────────────────────────────────────
function doneCount(p: TopologyProject) { return p.devices.filter(d => d.generatedOutput).length }
const hasAnyCommand = computed(() => projects.value.some(p => p.devices.some(d => d.generatedOutput)))

function typeTag(type: string) {
  if (type.includes('core')) return ''
  if (type.includes('router')) return 'danger'
  if (type.includes('firewall')) return 'warning'
  return 'success'
}

function vendorLabel(code: string) {
  const m: Record<string, string> = { huawei: '华为', h3c: 'H3C', ruijie: '锐捷', maipu: '迈普' }
  return m[code] || code
}

// ─── 从拓扑导入 ──────────────────────────────────────
const emit = defineEmits<{
  (e: 'edit-device', device: DeviceCommand): void
}>()

function handleImportFromTopo() {
  const devices = topoStore.exportedDevices
  if (devices.length === 0) { ElMessage.warning('请先在拓扑编辑器中点击「导出到命令工作台」'); return }

  const now = new Date().toLocaleString('zh-CN')
  const project: TopologyProject = {
    id: `proj_${Date.now()}`,
    name: `拓扑项目 ${projects.value.length + 1}`,
    createdAt: now,
    devices: devices.map(d => ({
      hostname: d.hostname,
      type: d.type,
      typeName: d.typeName,
      mgmtIp: d.mgmtIp,
      vlans: d.vlans || '',
      ports: d.ports?.map(p => ({
        interface: p.interface, remoteDevice: p.remoteDevice,
        remotePort: p.remotePort, linkType: p.linkType,
        vlanId: p.vlanId, allowedVlans: p.allowedVlans,
        ipNetwork: p.ipNetwork, bandwidth: p.bandwidth,
        direction: p.direction,
      })) || [],
    })),
    expanded: true,
  }
  projects.value.unshift(project)
  saveProjects()
  ElMessage.success(`已创建项目: ${project.name} (${project.devices.length} 台设备，含端口连接信息)`)
}

// ─── 编辑设备（跳转到配置生成 Tab） ──────────────────
function handleEditDevice(proj: TopologyProject, index: number) {
  const dev = proj.devices[index]
  // 触发事件，父组件切换 Tab 并加载设备参数（含端口信息）
  emit('edit-device', {
    hostname: dev.hostname,
    type: dev.type,
    typeName: dev.typeName,
    mgmtIp: dev.mgmtIp,
    vlans: dev.vlans || '',
    vendor: dev.vendor,
    ports: dev.ports || [],
  } as any)

  // 存储当前正在编辑的设备引用（生成完命令后保存回来）
  editingProject = proj
  editingIndex = index
}

// ─── 保存命令回设备 ──────────────────────────────────
let editingProject: TopologyProject | null = null
let editingIndex: number = -1

/** 由父组件在生成命令后调用，保存到对应设备 */
function saveDeviceCommand(output: string, vendor: string) {
  if (!editingProject || editingIndex < 0) return
  const dev = editingProject.devices[editingIndex]
  if (!dev) return

  dev.generatedOutput = output
  dev.generatedLines = output.split('\n').length
  dev.vendor = vendor
  dev.generatedAt = new Date().toLocaleString('zh-CN')
  saveProjects()
  editingProject = null
  editingIndex = -1
}

defineExpose({ saveDeviceCommand })

// ─── 查看/清空设备命令 ────────────────────────────────
const viewVisible = ref(false)
const viewingDevice = ref<DeviceCommand | null>(null)

function handleViewOutput(dev: DeviceCommand) {
  viewingDevice.value = dev
  viewVisible.value = true
}

function copyViewOutput() {
  if (!viewingDevice.value?.generatedOutput) return
  navigator.clipboard.writeText(viewingDevice.value.generatedOutput)
  ElMessage.success('已复制')
}

function handleClearDevice(proj: TopologyProject, index: number) {
  const dev = proj.devices[index]
  dev.generatedOutput = undefined
  dev.generatedLines = undefined
  dev.vendor = undefined
  dev.generatedAt = undefined
  saveProjects()
  ElMessage.info(`已清空 ${dev.hostname} 的命令`)
}

// ─── 删除项目 ──────────────────────────────────────────
function handleDeleteProject(id: string) {
  ElMessageBox.confirm('确定要删除此项目吗？设备命令也会一并删除。', '确认删除', { type: 'warning' })
    .then(() => {
      projects.value = projects.value.filter(p => p.id !== id)
      saveProjects()
      ElMessage.success('项目已删除')
    })
    .catch(() => {})
}

// ─── 导出 Markdown ─────────────────────────────────────
const exportVisible = ref(false)
const mdPreview = ref('')

function buildMarkdown(): string {
  const lines: string[] = ['# 网络设备配置导出\n', `> 导出时间: ${new Date().toLocaleString('zh-CN')}\n`]

  for (const proj of projects.value) {
    const hasAny = proj.devices.some(d => d.generatedOutput)
    if (!hasAny) continue

    lines.push(`\n---\n`)
    lines.push(`## 项目: ${proj.name}\n`)
    lines.push(`*创建于 ${proj.createdAt}，共 ${proj.devices.filter(d => d.generatedOutput).length}/${proj.devices.length} 台设备已生成*\n`)

    for (const dev of proj.devices) {
      if (!dev.generatedOutput) continue

      lines.push(`\n### ${dev.typeName}: ${dev.hostname}\n`)
      lines.push(`| 属性 | 值 |`)
      lines.push(`|---|---|`)
      lines.push(`| 类型 | ${dev.typeName} |`)
      lines.push(`| 厂商 | ${vendorLabel(dev.vendor || '')} |`)
      if (dev.mgmtIp) lines.push(`| 管理IP | ${dev.mgmtIp} |`)
      if (dev.vlans) lines.push(`| VLAN | ${dev.vlans} |`)
      if (dev.ports && dev.ports.length > 0) {
        lines.push(`| 端口连接 | |`)
        for (const p of dev.ports) {
          lines.push(`|   ${p.direction === 'uplink' ? '↑' : '↓'} ${p.interface} | → ${p.remoteDevice} ${p.remotePort} (${p.linkType}) ${p.ipNetwork ? '['+p.ipNetwork+']' : ''} |`)
        }
      }
      if (dev.generatedAt) lines.push(`| 生成时间 | ${dev.generatedAt} |`)
      lines.push(`\n\`\`\`\n${dev.generatedOutput}\n\`\`\``)
      lines.push('')
    }
  }

  return lines.join('\n')
}

function handleExportAll() {
  mdPreview.value = buildMarkdown()
  exportVisible.value = true
}

function handleConfirmExport() {
  const md = buildMarkdown()
  const name = projects.value[0]?.name || 'NetCmdGen'
  const filename = `${name}_配置导出_${new Date().toISOString().slice(0, 10)}.md`
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
  exportVisible.value = false
  ElMessage.success(`已导出: ${filename}`)
}
</script>

<style scoped>
.project-page { height: 100%; display: flex; flex-direction: column; }
.pj-toolbar { display: flex; align-items: center; gap: 12px; padding: 14px 20px; background: #fff; border-bottom: 1px solid #f0f0f0; }
.pj-title { font-size: 17px; font-weight: 700; color: #1e293b; }
.pj-body { flex: 1; overflow: auto; padding: 16px 20px; }
.pj-card { border: 1px solid #ebeef5; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }
.pj-card-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: #fafbfc; cursor: pointer; user-select: none; }
.pj-card-header:hover { background: #f0f2f5; }
.pj-card-info { display: flex; flex-direction: column; gap: 4px; }
.pj-card-name { font-size: 15px; font-weight: 600; color: #303133; }
.pj-card-meta { font-size: 12px; color: #909399; }
.pj-card-actions { display: flex; align-items: center; gap: 8px; }
.pj-device-table { padding: 8px 12px 12px; }
.pj-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; gap: 8px; font-size: 14px; }
.pj-output-block { background: #1a1b2e; color: #c9d1d9; padding: 16px; margin: 0; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 12px; line-height: 1.6; overflow: auto; max-height: 400px; white-space: pre-wrap; border-radius: 6px; }
</style>

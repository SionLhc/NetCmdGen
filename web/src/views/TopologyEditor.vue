<template>
  <div class="topology-container">
    <!-- 顶部工具栏行1：拓扑管理 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="title">企业园区网拓扑编辑器</span>
        <el-divider direction="vertical" />
        <el-select v-model="currentTopoId" size="small" style="width:180px" @change="switchTopo" placeholder="选择拓扑">
          <el-option v-for="t in topoList" :key="t.id" :label="t.name" :value="t.id"/>
        </el-select>
        <el-button size="small" @click="handleNewTopo">+ 新建</el-button>
        <el-button size="small" @click="handleRenameTopo" :disabled="!currentTopoId">重命名</el-button>
        <el-button size="small" @click="handleDeleteTopo" :disabled="topoList.length<=1">删除</el-button>
        <el-divider direction="vertical" />
        <el-button size="small" @click="handleAddGroup">+ 添加分组</el-button>
        <el-button size="small" @click="handleAutoLayout">自动布局</el-button>
        <el-button size="small" @click="exportReport">📄 导出报告</el-button>
        <el-button size="small" type="success" @click="showLldpDialog = true">🔍 LLDP 发现</el-button>
        <span style="margin-left:auto;display:flex;align-items:center;gap:6px" v-if="currentTopoId" :title="collabOnline>1?`${collabOnline} 人在线`:'单人模式'">
          <span class="collab-dot" :class="{ online: collabOnline > 1 }"></span>
          <span style="font-size:11px;color:#909399">{{ collabOnline > 1 ? `${collabOnline} 人在线` : '' }}</span>
        </span>
        <el-divider direction="vertical" />
        <el-button size="small" @click="handleClear">清空</el-button>
        <el-button size="small" @click="handleDeleteSelected" :disabled="!topologyStore.selectedNode && !topologyStore.selectedEdge">删除选中</el-button>
        <el-divider direction="vertical" />
        <el-button size="small" @click="handleUndo" title="Ctrl+Z">↩ 撤销</el-button>
        <el-button size="small" @click="handleRedo" title="Ctrl+Y">↪ 重做</el-button>
        <el-divider direction="vertical" />
        <TopoSearch @search="onTopoSearch" @filter="onTopoFilter" />
      </div>
    </div>

    <!-- 行2：保存 / 导入 / 导出 / 命令工作台 — 在拓扑下拉框正下方 -->
    <div class="toolbar-actions">
      <el-button type="primary" @click="handleSave" :loading="autoSaving" :disabled="!currentTopoId">💾 保存到服务器</el-button>
      <el-button @click="handleImportJson">📥 导入 JSON</el-button>
      <el-button @click="handleDownload" :disabled="!currentTopoId">📤 导出 JSON</el-button>
      <el-button @click="handleExportPng" :disabled="!currentTopoId">🖼 导出 PNG</el-button>
      <el-divider direction="vertical" />
      <el-button type="success" @click="handleExportToWorkbench" :disabled="!currentTopoId">📋 复制到命令工作台</el-button>
    </div>

    <TopoStats :nodes="topoNodeCount" :edges="topoEdgeCount" :online="topoOnline" :offline="topoOffline" />

    <div class="main-content">
      <!-- 左侧设备库 -->
      <DevicePalette />

      <!-- 中间：画布 -->
      <div class="canvas-wrapper" ref="canvasRef"></div>

      <!-- 右侧属性面板 -->
      <PropertyPanel />
    </div>

    <!-- 分组改名弹窗 -->
    <el-dialog v-model="groupRenameVisible" title="重命名分组" width="350px">
      <el-input v-model="groupRenameForm.name" placeholder="分组名称" />
      <template #footer>
        <el-button @click="groupRenameVisible = false">取消</el-button>
        <el-button type="primary" @click="handleGroupRename">确定</el-button>
      </template>
    </el-dialog>

    <!-- 连线标签编辑弹窗 -->
    <el-dialog v-model="edgeLabelVisible" title="编辑连线" width="480px">
      <!-- 设备归属提示 -->
      <div class="edge-devices-bar">
        <span class="edge-device source">{{ edgeSourceName || '源设备' }}</span>
        <span class="edge-arrow">→</span>
        <span class="edge-device target">{{ edgeTargetName || '目标设备' }}</span>
      </div>

      <el-form :model="edgeLabelForm" label-width="100px" size="small">
        <el-divider content-position="left">基本属性</el-divider>
        <el-form-item label="链路类型">
          <el-select v-model="edgeLabelForm.linkType" style="width: 100%">
            <el-option label="Trunk（透传多VLAN）" value="trunk" />
            <el-option label="Access（单个VLAN）" value="access" />
            <el-option label="Hybrid（混合模式）" value="hybrid" />
            <el-option label="专线" value="leased-line" />
            <el-option label="Internet" value="internet" />
          </el-select>
        </el-form-item>
        <el-form-item label="带宽">
          <el-select v-model="edgeLabelForm.bandwidth" style="width: 100%">
            <el-option label="100M" value="100M" />
            <el-option label="1G" value="1G" />
            <el-option label="10G" value="10G" />
            <el-option label="25G" value="25G" />
            <el-option label="40G" value="40G" />
            <el-option label="100G" value="100G" />
          </el-select>
        </el-form-item>
        <el-form-item label="显示箭头">
          <el-switch v-model="edgeLabelForm.hasArrow" />
          <span style="font-size:11px;color:#909399;margin-left:8px">源→目的方向</span>
        </el-form-item>

        <el-divider content-position="left">
          <span style="color:#409eff">源设备端口</span>
        </el-divider>
        <el-form-item label="接口名">
          <el-input v-model="edgeLabelForm.sourcePort" placeholder="例如: GigabitEthernet0/0/24" />
        </el-form-item>
        <el-form-item v-if="edgeLabelForm.linkType === 'access'" label="源 VLAN ID">
          <el-input-number v-model="edgeLabelForm.vlanId" :min="1" :max="4094" style="width:100%" />
        </el-form-item>
        <el-form-item v-if="edgeLabelForm.linkType === 'trunk' || edgeLabelForm.linkType === 'hybrid'" label="源允许VLAN">
          <el-input v-model="edgeLabelForm.allowedVlansStr" placeholder="10,20,100-200" />
        </el-form-item>

        <el-divider content-position="left">
          <span style="color:#e6a23c">目标设备端口</span>
        </el-divider>
        <el-form-item label="接口名">
          <el-input v-model="edgeLabelForm.targetPort" placeholder="例如: GigabitEthernet0/0/1" />
        </el-form-item>

        <el-divider content-position="left">接口高级配置</el-divider>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="源 MTU">
              <el-input-number v-model="edgeLabelForm.sourceMtu" :min="576" :max="9216" :step="100" style="width:100%" placeholder="1500" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标 MTU">
              <el-input-number v-model="edgeLabelForm.targetMtu" :min="576" :max="9216" :step="100" style="width:100%" placeholder="1500" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="源速率/双工">
              <el-select v-model="edgeLabelForm.sourceSpeed" style="width:100%">
                <el-option label="自动协商" value="auto" />
                <el-option label="1000M 全双工" value="1000-full" />
                <el-option label="100M 全双工" value="100-full" />
                <el-option label="10M 全双工" value="10-full" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标速率/双工">
              <el-select v-model="edgeLabelForm.targetSpeed" style="width:100%">
                <el-option label="自动协商" value="auto" />
                <el-option label="1000M 全双工" value="1000-full" />
                <el-option label="100M 全双工" value="100-full" />
                <el-option label="10M 全双工" value="10-full" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="源接口描述">
          <el-input v-model="edgeLabelForm.sourceDesc" placeholder="例如: To-Core-Uplink" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="目标接口描述">
          <el-input v-model="edgeLabelForm.targetDesc" placeholder="例如: From-Access-Downlink" maxlength="100" show-word-limit />
        </el-form-item>

        <el-divider content-position="left">三层配置</el-divider>
        <el-form-item label="互联 IP 网段">
          <el-input v-model="edgeLabelForm.ipNetwork" placeholder="例如: 10.0.0.0/30（非必填）" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="源 VLANIF IP">
              <el-input v-model="edgeLabelForm.sourceVlanifIp" placeholder="10.0.0.1/30" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标 VLANIF IP">
              <el-input v-model="edgeLabelForm.targetVlanifIp" placeholder="10.0.0.2/30" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="OSPF 区域" v-if="edgeLabelForm.ipNetwork">
          <el-input v-model="edgeLabelForm.ospfArea" placeholder="例如: 0 或 0.0.0.0" style="width:150px" />
          <span style="font-size:12px;color:#909399;margin-left:8px">填写后自动在接口启用 OSPF</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="edgeLabelVisible = false" size="small">取消</el-button>
        <el-button @click="handleClearEdgeLabel" size="small" type="danger" plain>清除标签</el-button>
        <el-button type="primary" @click="handleSaveEdgeLabel" size="small">保存</el-button>
      </template>
    </el-dialog>

    <!-- LLDP 发现对话框 -->
    <el-dialog v-model="showLldpDialog" title="LLDP 拓扑自动发现" width="420px">
      <el-form label-width="80px" size="default" @submit.prevent="handleLldpDiscover">
        <el-form-item label="种子设备">
          <el-input v-model="lldpHost" placeholder="192.168.1.1" />
        </el-form-item>
        <el-form-item label="SSH 端口">
          <el-input-number v-model="lldpPort" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="lldpUser" placeholder="admin" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="lldpPass" type="password" placeholder="****" />
        </el-form-item>
        <el-form-item label="发现深度">
          <el-input-number v-model="lldpDepth" :min="1" :max="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLldpDialog = false">取消</el-button>
        <el-button type="primary" @click="handleLldpDiscover" :loading="lldpLoading">开始扫描</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import TopoSearch from '@/components/topology/TopoSearch.vue'
import TopoStats from '@/components/topology/TopoStats.vue'
import { computed } from 'vue'
import { ref, onMounted, onBeforeUnmount, reactive } from 'vue'
import { Graph } from '@antv/x6'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTopologyStore } from '@/stores/topology'
import DevicePalette from '@/components/topology/DevicePalette.vue'
import PropertyPanel from '@/components/topology/PropertyPanel.vue'
import dagre from 'dagre'

const topologyStore = useTopologyStore()
const canvasRef = ref<HTMLDivElement>()

// 协作状态
const collabOnline = ref(1)
let collabSocket: WebSocket | null = null

/** 连接协作 WebSocket */
function connectCollab(roomId: string) {
    collabSocket?.close()
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    collabSocket = new WebSocket(`${proto}://${location.host}/api/collab/ws/${roomId}`)
    collabSocket.onmessage = (e) => {
        try {
            const msg = JSON.parse(e.data)
            if (msg.type === 'joined' || msg.type === 'join' || msg.type === 'leave') {
                collabOnline.value = msg.online || 1
            } else if (msg.type === 'update' && msg.data) {
                // 应用远程拓扑更新
                applyRemoteUpdate(msg.data)
            }
        } catch {}
    }
    collabSocket.onclose = () => { collabOnline.value = 1 }
}

/** 应用远程拓扑更新 */
function applyRemoteUpdate(data: any) {
    if (!graph) return
    try {
        graph.fromJSON(data)
        graph.centerContent()
    } catch { /* 忽略无效更新 */ }
}

// LLDP 发现状态
const showLldpDialog = ref(false)
const lldpHost = ref('')
const lldpPort = ref(22)
const lldpUser = ref('admin')
const lldpPass = ref('')
const lldpDepth = ref(2)
const lldpLoading = ref(false)

/** LLDP 自动发现并导入拓扑 */
async function handleLldpDiscover() {
    if (!lldpHost.value.trim() || !lldpUser.value.trim()) {
        ElMessage.warning('请输入设备 IP 和用户名'); return
    }
    lldpLoading.value = true
    try {
        const params = new URLSearchParams({
            host: lldpHost.value, port: String(lldpPort.value),
            username: lldpUser.value, password: lldpPass.value,
            max_depth: String(lldpDepth.value),
        })
        const res = await fetch('/api/lldp/discover?' + params)
        const data = await res.json()
        if (!data.success) {
            ElMessage.warning(data.message || '未发现邻居')
            return
        }
        // 导入到当前拓扑
        lldpImportToGraph(data.nodes, data.edges)
        ElMessage.success(`发现 ${data.total} 台设备，${data.edges.length} 条连线`)
        showLldpDialog.value = false
    } catch {
        ElMessage.error('LLDP 发现失败')
    } finally {
        lldpLoading.value = false
    }
}

/** 将 LLDP 发现的 JSON 数据导入 X6 图形 */
function lldpImportToGraph(jsonNodes: any[], jsonEdges: any[]) {
    if (!graph) return
    // 添加节点
    for (const n of jsonNodes) {
        if (graph.getCellById(n.id)) continue
        const data = topologyStore.getDeviceConfig(n.type || 'switch') || {}
        graph.addNode({
            id: n.id,
            shape: 'topo-node',
            x: n.x || 100, y: n.y || 100,
            width: 120, height: 70,
            data: { ...data, hostname: n.label, mgmtIp: n.mgmtIp, label: n.label },
            ports: { items: [{ group: 'top' }, { group: 'bottom' }] },
        })
    }
    // 添加连线
    for (const e of jsonEdges) {
        const existing = graph.getEdges().filter(edge =>
            (edge.getSourceCellId() === e.source && edge.getTargetCellId() === e.target) ||
            (edge.getSourceCellId() === e.target && edge.getTargetCellId() === e.source)
        )
        if (existing.length > 0) continue
        graph.addEdge({
            shape: 'edge',
            source: { cell: e.source, port: 'bottom' },
            target: { cell: e.target, port: 'top' },
            labels: e.sourcePort ? [{ attrs: { label: { text: `${e.sourcePort}↔${e.targetPort}` } } }] : [],
            attrs: { line: { stroke: '#94a3b8', strokeWidth: 2, targetMarker: null } },
        })
    }
    graph.centerContent()
}

// ─── 多拓扑管理（服务器文件存储）─────────────────────
import { getTopoList, createTopo, getTopoData, saveTopoData, renameTopo, deleteTopo, importTopo, type TopoItem } from '@/api'

const topoList = ref<TopoItem[]>([])
const currentTopoId = ref('')
const topoLoading = ref(false)
const autoSaving = ref(false)  // 自动保存中状态

// ─── TopoStats 统计数据 ─────────────────────────────────
const topoNodeCount = ref(0)
const topoEdgeCount = ref(0)
const topoOnline = ref(0)
const topoOffline = ref(0)
function updateTopoStats() {
  if (!graph) return
  const cells = graph.getCells()
  topoNodeCount.value = cells.filter((c:any) => c.isNode?.()).length
  topoEdgeCount.value = cells.filter((c:any) => c.isEdge?.()).length
  topoOnline.value = Math.floor(topoNodeCount.value * 0.8)
  topoOffline.value = topoNodeCount.value - topoOnline.value
}

// ─── 拓扑搜索 ──────────────────────────────────────────
function onTopoSearch(kw: string) {
  if (!graph) return
  const cells = graph.getCells()
  cells.forEach((c:any) => { if(c.isNode?.()) c.removeTool('button-remove') })
  if (!kw) return
  const found = cells.find((c:any) => {
    const d = c.getData?.() || {}
    const label = d.label || c.attr?.('text/text') || ''
    return label.includes(kw)
  })
  if (found) {
    graph.zoomToFit()
    graph.centerCell(found)
    setTimeout(() => graph.zoom(0.02), 100)
  }
}
function onTopoFilter(layer: string) {
  // 层级过滤 — 通过设备标签匹配
  if (!graph) return
  const cells = graph.getCells()
  cells.forEach((c:any) => {
    if (c.isNode?.()) {
      const d = c.getData?.() || {}
      if (layer === 'all') { c.setVisible(true); return }
      const label = (d.label || c.attr?.('text/text') || '').toLowerCase()
      const match = layer === 'core' ? label.includes('核心') || label.includes('core') :
        layer === 'dist' ? label.includes('汇聚') || label.includes('dist') :
        label.includes('接入') || label.includes('access')
      c.setVisible(match)
    }
  })
}

/** 启动时从服务器加载拓扑列表 */
async function initTopoList() {
  topoLoading.value = true
  try {
    const items = await getTopoList()
    if (items.length === 0) {
      // 首次使用，自动创建一个默认方案
      const { id } = await createTopo('默认拓扑')
      topoList.value = [{ id, name: '默认拓扑' }]
    } else {
      topoList.value = items
    }
    currentTopoId.value = topoList.value[0]?.id || ''
    await loadCurrentTopo()
  } catch { ElMessage.error('加载拓扑列表失败，请检查后端是否启动') }
  finally { topoLoading.value = false }
}

function handleNewTopo() {
  ElMessageBox.prompt('请输入拓扑名称', '新建拓扑', {
    confirmButtonText: '创建', cancelButtonText: '取消',
    inputValue: `拓扑方案${topoList.value.length + 1}`,
  }).then(async ({ value }) => {
    const name = value?.trim(); if (!name) return
    const { id } = await createTopo(name)
    topoList.value.push({ id, name }); currentTopoId.value = id
    graph?.clearCells()
    ElMessage.success(`已创建: ${name}`)
  }).catch(() => {})
}

async function switchTopo(id: string) {
  if (!graph) return
  // 先保存当前
  const oldData = graph.toJSON()
  if (oldData.cells && oldData.cells.length > 0) {
    await saveTopoData(currentTopoId.value, oldData).catch(() => {})
  }
  currentTopoId.value = id
  await loadCurrentTopo()
}

async function loadCurrentTopo() {
  if (!graph || !currentTopoId.value) return
  connectCollab(currentTopoId.value)  // 拓扑加载时连接协作房间
  try {
    const { data } = await getTopoData(currentTopoId.value)
    if (data && data.cells && data.cells.length > 0) {
      graph.fromJSON(data)
    } else {
      graph.clearCells()
    }
  } catch { graph.clearCells() }
}

function handleRenameTopo() {
  const item = topoList.value.find(t => t.id === currentTopoId.value)
  if (!item) return
  ElMessageBox.prompt('请输入新名称', '重命名拓扑', {
    confirmButtonText: '确定', cancelButtonText: '取消', inputValue: item.name,
  }).then(async ({ value }) => {
    const name = value?.trim(); if (!name) return
    await renameTopo(currentTopoId.value, name)
    item.name = name
    ElMessage.success('已重命名')
  }).catch(() => {})
}

function handleDeleteTopo() {
  if (topoList.value.length <= 1) { ElMessage.warning('至少保留一个拓扑'); return }
  const item = topoList.value.find(t => t.id === currentTopoId.value)
  if (!item) return
  ElMessageBox.confirm(`确定删除"${item.name}"？文件将被永久删除。`, '删除拓扑', {
    confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning',
  }).then(async () => {
    await deleteTopo(currentTopoId.value)
    topoList.value = topoList.value.filter(t => t.id !== currentTopoId.value)
    currentTopoId.value = topoList.value[0].id
    await loadCurrentTopo()
    ElMessage.success('已删除')
  }).catch(() => {})
}

let graph: Graph | null = null

// ─── 连线标签编辑 ───────────────────────────────────────────
const edgeLabelVisible = ref(false)
const editingEdgeId = ref<string | null>(null)
const edgeSourceName = ref('')
const edgeTargetName = ref('')

const edgeLabelForm = reactive({
    linkType: 'trunk',
    hasArrow: false,
    vlanId: undefined as number | undefined,
    allowedVlansStr: '',
    ipNetwork: '',
    bandwidth: '1G',
    sourcePort: '',
    targetPort: '',
    sourceMtu: 1500,
    targetMtu: 1500,
    sourceSpeed: 'auto',
    targetSpeed: 'auto',
    sourceDesc: '',
    targetDesc: '',
    sourceVlanifIp: '',
    targetVlanifIp: '',
    ospfArea: '',
})

// ─── 分组节点注册 ──────────────────────────────────────────
Graph.registerNode(
    'group-node',
    {
        inherit: 'rect',
        width: 300,
        height: 200,
        markup: [
            { tagName: 'rect', selector: 'body' },
            { tagName: 'text', selector: 'label' },
        ],
        attrs: {
            body: {
                refWidth: '100%',
                refHeight: '100%',
                fill: 'rgba(64,158,255,0.03)',
                stroke: '#409eff',
                strokeWidth: 1.5,
                strokeDasharray: '6,3',
                rx: 8,
                ry: 8,
            },
            label: {
                refX: 6,
                refY: 6,
                textAnchor: 'left',
                textVerticalAnchor: 'top',
                text: '分组',
                fontSize: 12,
                fontWeight: 600,
                fill: '#409eff',
                fontFamily: 'PingFang SC, Microsoft YaHei, sans-serif',
            },
        },
        ports: {
            groups: {},
            items: [],
        },
    },
    true,
)

// 注册自定义设备节点形状
Graph.registerNode(
  'custom-device',
  {
    inherit: 'rect',
    width: 80,
    height: 60,
    markup: [
      { tagName: 'rect', selector: 'body' },
      {
        tagName: 'image',
        selector: 'image',
        attrs: {
          'xlink:href': '',
        },
      },
      { tagName: 'text', selector: 'label' },
    ],
    attrs: {
      body: {
        refWidth: '100%',
        refHeight: '100%',
        rx: 6,
        ry: 6,
        fill: 'transparent',
        stroke: 'transparent',
        strokeWidth: 1,
      },
      image: {
        width: 72,
        height: 56,
        x: 4,
        y: 4,
        preserveAspectRatio: 'xMidYMid meet',
      },
      label: {
        refX: 0.5,
        refY: 64,
        textAnchor: 'middle',
        textVerticalAnchor: 'top',
        fontSize: 12,
        fontFamily: 'PingFang SC, Microsoft YaHei, sans-serif',
        fontWeight: 500,
        fill: '#303133',
      },
    },
    ports: {
      groups: {
        top: {
          position: 'top',
          attrs: {
            circle: {
              r: 4,
              magnet: true,
              stroke: '#5F95FF',
              strokeWidth: 1.5,
              fill: '#ffffff',
              opacity: 0.5,
              style: { cursor: 'crosshair' },
            },
          },
          maximum: 0,
        },
        right: {
          position: 'right',
          attrs: {
            circle: {
              r: 4,
              magnet: true,
              stroke: '#5F95FF',
              strokeWidth: 1.5,
              fill: '#ffffff',
              opacity: 0.5,
              style: { cursor: 'crosshair' },
            },
          },
          maximum: 0,
        },
        bottom: {
          position: 'bottom',
          attrs: {
            circle: {
              r: 4,
              magnet: true,
              stroke: '#5F95FF',
              strokeWidth: 1.5,
              fill: '#ffffff',
              opacity: 0.5,
              style: { cursor: 'crosshair' },
            },
          },
          maximum: 0,
        },
        left: {
          position: 'left',
          attrs: {
            circle: {
              r: 4,
              magnet: true,
              stroke: '#5F95FF',
              strokeWidth: 1.5,
              fill: '#ffffff',
              opacity: 0.5,
              style: { cursor: 'crosshair' },
            },
          },
          maximum: 0,
        },
      },
      items: [
        { id: 'port-top', group: 'top' },
        { id: 'port-right', group: 'right' },
        { id: 'port-bottom', group: 'bottom' },
        { id: 'port-left', group: 'left' },
      ],
    },
  },
  true,
)

onMounted(() => {
  initGraph()
  initTopoList()
})

onBeforeUnmount(() => {
  collabSocket?.close()
  document.removeEventListener('keydown', handleKeyDelete)
  graph?.dispose()
})

function initGraph() {
  if (!canvasRef.value) return

  graph = new Graph({
    container: canvasRef.value,
    grid: {
      size: 10,
      visible: true,
      type: 'dot',
      args: { color: '#e0e0e0', thickness: 1 },
    },
    panning: true,
    mousewheel: { enabled: true, modifiers: 'ctrl' },
    // 启用节点嵌入（拖入分组容器即成为子节点）
    embedding: {
      enabled: true,
      findParent({ node }) {
        const bbox = node.getBBox()
        // 查找覆盖节点的分组框
        return graph!.getNodes().filter(n => {
          if (n.id === node.id || n.shape !== 'group-node') return false
          const gbbox = n.getBBox()
          return (
            bbox.x >= gbbox.x &&
            bbox.y >= gbbox.y &&
            bbox.x + bbox.width <= gbbox.x + gbbox.width &&
            bbox.y + bbox.height <= gbbox.y + gbbox.height
          )
        })
      },
      validate({ child }) {
        // 只有设备节点可以被嵌入分组
        return child.shape === 'custom-device'
      },
    },
    connecting: {
      router: 'manhattan',
      connector: { name: 'rounded', args: { radius: 8 } },
      anchor: 'center',
      connectionPoint: 'anchor',
      allowBlank: false,
      allowLoop: false,
      allowNode: false,
      allowEdge: false,
      snap: { radius: 30 },
      validateMagnet({ magnet }) {
        return magnet.getAttribute('magnet') !== 'passive'
      },
      validateConnection({ sourceMagnet, targetMagnet }) {
        if (!sourceMagnet || !targetMagnet) return false
        return true
      },
      createEdge() {
        return graph!.createEdge({
          shape: 'edge',
          attrs: {
            line: {
              stroke: '#7a90b5',
              strokeWidth: 1.8,
              // 默认不显示箭头，用户可在对话框里开启
            },
          },
          labels: [],
          defaultLabel: {
            markup: [
              { tagName: 'rect', selector: 'labelBody' },
              { tagName: 'text', selector: 'labelText' },
            ],
            attrs: {
              labelText: {
                text: '--',
                fill: '#606266',
                fontSize: 11,
                textAnchor: 'middle',
                textVerticalAnchor: 'middle',
                fontFamily: 'PingFang SC, Microsoft YaHei, sans-serif',
              },
              labelBody: {
                ref: 'labelText',
                refWidth: '120%',
                refHeight: '120%',
                refX: '-10%',
                refY: '-10%',
                fill: '#ffffff',
                stroke: '#dcdfe6',
                strokeWidth: 1,
                rx: 4,
                ry: 4,
              },
            },
            position: { distance: 0.5, offset: -12 },
          },
          data: {
            linkType: 'trunk',
            hasArrow: false,
            sourcePort: '',
            targetPort: '',
            bandwidth: '1G',
            vlanId: undefined,
            ipNetwork: '',
          },
        })
      },
    },
    highlighting: {
      magnetAvailable: {
        name: 'stroke',
        args: {
          attrs: {
            fill: '#fff',
            stroke: '#67c23a',
            strokeWidth: 4,
          },
        },
      },
      magnetAdsorbed: {
        name: 'stroke',
        args: {
          attrs: {
            fill: '#fff',
            stroke: '#67c23a',
            strokeWidth: 4,
          },
        },
      },
    },
    history: {
      enabled: true,
      // 排除临时/导航节点变化
      beforeAddCommand(event, args) { return true },
    },
  })

  // ── 协作 + 自动保存 ──
  let autoSaveTimer: ReturnType<typeof setTimeout> | null = null
  graph.on('cell:change:*', () => {
    // 协作同步
    if (collabSocket?.readyState === WebSocket.OPEN && currentTopoId.value) {
      collabSocket.send(JSON.stringify({ type: 'update', room_id: currentTopoId.value, data: graph.toJSON() }))
    }
    // 自动保存：防抖 5 秒
    if (currentTopoId.value) {
      clearTimeout(autoSaveTimer!)
      autoSaveTimer = setTimeout(() => {
        autoSaving.value = true
        saveTopoData(currentTopoId.value, graph.toJSON()).finally(() => { autoSaving.value = false })
      }, 5000)
    }
  })

  // ─── 快捷键：Ctrl+Z 撤销 / Ctrl+Y 重做 ──────────────
  const handleKeyHistory = (e: KeyboardEvent) => {
    if (!graph || (e.target as HTMLElement)?.tagName === 'INPUT') return
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
      e.preventDefault(); graph.undo()
    } else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
      e.preventDefault(); graph.redo()
    }
  }
  document.addEventListener('keydown', handleKeyHistory)

  // 控制连接桩高亮的函数
  const showPorts = (show: boolean) => {
    if (!graph) return
    const ports = canvasRef.value!.querySelectorAll('.x6-port-body') as NodeListOf<SVGElement>
    ports.forEach((port) => {
      port.style.opacity = show ? '1' : '0.5'
    })
  }

  // 鼠标移入节点，显示连接桩 + 边框高亮
  graph.on('node:mouseenter', ({ node }) => {
    showPorts(true)
    if (node.shape === 'custom-device') {
      node.setAttrByPath('body/fill', 'rgba(64,158,255,0.06)')
      node.setAttrByPath('body/stroke', '#409eff')
    }
  })

  // 鼠标移出节点，隐藏连接桩 + 恢复边框
  graph.on('node:mouseleave', ({ node }) => {
    showPorts(false)
    if (node.shape === 'custom-device') {
      node.setAttrByPath('body/fill', 'transparent')
      node.setAttrByPath('body/stroke', 'transparent')
    }
  })

  // 点击节点
  graph.on('node:click', ({ node }) => {
    topologyStore.selectedNode = node
    topologyStore.selectedEdge = null
  })

  // 点击连线
  graph.on('edge:click', ({ edge }) => {
    topologyStore.selectedEdge = edge
    topologyStore.selectedNode = null
  })

  // 双击连线编辑标签
  graph.on('edge:dblclick', ({ edge }) => {
    openEdgeLabelEditor(edge)
  })

  // 连线创建完成后自动提示编辑标签
  graph.on('edge:connected', ({ edge }) => {
    // 新连线创建后自动打开标签编辑
    setTimeout(() => openEdgeLabelEditor(edge), 200)
  })

  // 点击画布空白处
  graph.on('blank:click', () => {
    topologyStore.selectedNode = null
    topologyStore.selectedEdge = null
    groupRenameVisible.value = false
  })

  // 双击分组节点改名
  graph.on('node:dblclick', ({ node }) => {
    if (node.shape === 'group-node') {
      editingGroupId.value = node.id
      groupRenameForm.name = node.getAttrByPath('label/text') || '分组'
      groupRenameVisible.value = true
      return
    }
    // 设备节点改名
    const currentLabel = node.getAttrByPath('label/text') as string || ''
    const newName = window.prompt('修改设备名称：', currentLabel)
    if (newName !== null && newName.trim() !== '') {
      node.setAttrByPath('label/text', newName.trim())
      const data = node.getData() || {}
      node.setData({ ...data, hostname: newName.trim() })
    }
  })
}

// ─── 连线标签编辑函数 ──────────────────────────────────────

/** 打开连线标签编辑弹窗 */
function openEdgeLabelEditor(edge: any) {
    editingEdgeId.value = edge.id
    const data = edge.getData() || {}

    // 读取源/目标设备名称
    const sourceCell = edge.getSourceCell()
    const targetCell = edge.getTargetCell()
    edgeSourceName.value = sourceCell?.getAttrByPath?.('label/text') as string
        || sourceCell?.getData?.()?.hostname
        || (sourceCell?.id || '未知设备')
    edgeTargetName.value = targetCell?.getAttrByPath?.('label/text') as string
        || targetCell?.getData?.()?.hostname
        || (targetCell?.id || '未知设备')

    // 读取当前连线数据填充表单
    edgeLabelForm.linkType = data.linkType || 'trunk'
    edgeLabelForm.hasArrow = data.hasArrow === true
    edgeLabelForm.vlanId = data.vlanId
    edgeLabelForm.ipNetwork = data.ipNetwork || ''
    edgeLabelForm.bandwidth = data.bandwidth || '1G'
    edgeLabelForm.sourcePort = data.sourcePort || ''
    edgeLabelForm.targetPort = data.targetPort || ''
    edgeLabelForm.sourceMtu = data.sourceMtu || 1500
    edgeLabelForm.targetMtu = data.targetMtu || 1500
    edgeLabelForm.sourceSpeed = data.sourceSpeed || 'auto'
    edgeLabelForm.targetSpeed = data.targetSpeed || 'auto'
    edgeLabelForm.sourceDesc = data.sourceDesc || ''
    edgeLabelForm.targetDesc = data.targetDesc || ''
    edgeLabelForm.sourceVlanifIp = data.sourceVlanifIp || ''
    edgeLabelForm.targetVlanifIp = data.targetVlanifIp || ''
    edgeLabelForm.ospfArea = data.ospfArea || ''

    // 将 VLAN 列表转回字符串
    if (data.allowedVlans && Array.isArray(data.allowedVlans)) {
        edgeLabelForm.allowedVlansStr = data.allowedVlans.join(',')
    } else {
        edgeLabelForm.allowedVlansStr = ''
    }

    edgeLabelVisible.value = true
}

/** 保存连线标签 */
function handleSaveEdgeLabel() {
    if (!graph || !editingEdgeId.value) return

    const edge = graph.getCellById(editingEdgeId.value)
    if (!edge || !edge.isEdge()) return

    // 解析 VLAN 列表字符串
    let allowedVlans: number[] | undefined
    if (edgeLabelForm.allowedVlansStr.trim()) {
        allowedVlans = parseVlanList(edgeLabelForm.allowedVlansStr)
    }

    // 更新 edge 的 data — 端口明确归属到源/目标设备
    const newData = {
        linkType: edgeLabelForm.linkType,
        hasArrow: edgeLabelForm.hasArrow,
        vlanId: edgeLabelForm.vlanId,
        allowedVlans,
        ipNetwork: edgeLabelForm.ipNetwork,
        bandwidth: edgeLabelForm.bandwidth,
        sourcePort: edgeLabelForm.sourcePort,
        targetPort: edgeLabelForm.targetPort,
        sourceMtu: edgeLabelForm.sourceMtu,
        targetMtu: edgeLabelForm.targetMtu,
        sourceSpeed: edgeLabelForm.sourceSpeed,
        targetSpeed: edgeLabelForm.targetSpeed,
        sourceDesc: edgeLabelForm.sourceDesc,
        targetDesc: edgeLabelForm.targetDesc,
        sourceVlanifIp: edgeLabelForm.sourceVlanifIp,
        targetVlanifIp: edgeLabelForm.targetVlanifIp,
        ospfArea: edgeLabelForm.ospfArea,
    }
    edge.setData(newData)

    // 构建显示标签文本（包含端口 + IP 信息）
    const labelParts: string[] = []

    // 链路类型
    if (edgeLabelForm.linkType === 'trunk') {
        labelParts.push('Trunk')
    } else if (edgeLabelForm.linkType === 'access' && edgeLabelForm.vlanId) {
        labelParts.push(`VLAN${edgeLabelForm.vlanId}`)
    } else if (edgeLabelForm.linkType === 'hybrid') {
        labelParts.push('Hybrid')
    } else if (edgeLabelForm.linkType === 'leased-line') {
        labelParts.push('专线')
    } else if (edgeLabelForm.linkType === 'internet') {
        labelParts.push('Internet')
    }

    // 端口
    if (edgeLabelForm.sourcePort && edgeLabelForm.targetPort) {
        labelParts.push(`${edgeLabelForm.sourcePort}→${edgeLabelForm.targetPort}`)
    } else if (edgeLabelForm.sourcePort) {
        labelParts.push(edgeLabelForm.sourcePort)
    }

    // VLANIF IP（更常用）
    if (edgeLabelForm.sourceVlanifIp && edgeLabelForm.targetVlanifIp) {
        labelParts.push(`${edgeLabelForm.sourceVlanifIp}↔${edgeLabelForm.targetVlanifIp}`)
    } else if (edgeLabelForm.ipNetwork) {
        labelParts.push(edgeLabelForm.ipNetwork)
    }

    // OSPF 标识
    if (edgeLabelForm.ospfArea) {
        labelParts.push(`OSPF Area ${edgeLabelForm.ospfArea}`)
    }

    const labelText = labelParts.join('\n') || edgeLabelForm.linkType

    // 更新连线标签
    edge.setLabels([
        {
            attrs: {
                labelText: { text: labelText },
            },
            position: { distance: 0.5, offset: -12 },
        },
    ])

    edgeLabelVisible.value = false
    editingEdgeId.value = null

    // ── 箭头与颜色 ─────────────────────────────────────────
    const lineStroke = edgeLabelForm.linkType === 'internet' ? '#e6a23c' : '#7a90b5'

    // 设置线条颜色
    edge.setAttrByPath('line/stroke', lineStroke)

    // 根据开关控制箭头
    if (edgeLabelForm.hasArrow) {
        edge.setAttrByPath('line/targetMarker/name', 'classic')
        edge.setAttrByPath('line/targetMarker/width', 8)
        edge.setAttrByPath('line/targetMarker/height', 8)
        edge.setAttrByPath('line/targetMarker/fill', lineStroke)
        edge.setAttrByPath('line/targetMarker/stroke', lineStroke)
    } else {
        // 移除箭头
        edge.removeAttrByPath('line/targetMarker')
    }

    // Internet 类型用虚线
    if (edgeLabelForm.linkType === 'internet') {
        edge.setAttrByPath('line/strokeDasharray', '6,3')
    } else {
        edge.setAttrByPath('line/strokeDasharray', '')
    }

    ElMessage.success('连线已更新')
}

/** 清除连线标签 */
function handleClearEdgeLabel() {
    if (!graph || !editingEdgeId.value) return

    const edge = graph.getCellById(editingEdgeId.value)
    if (!edge || !edge.isEdge()) return

    edge.setLabels([])
    edgeLabelVisible.value = false
    editingEdgeId.value = null
    ElMessage.info('连线标签已清除')
}

/** 解析 VLAN 列表字符串（支持逗号分隔和范围） */
function parseVlanList(str: string): number[] {
    const result: number[] = []
    const parts = str.split(',')

    for (const part of parts) {
        const trimmed = part.trim()
        if (trimmed.includes('-')) {
            const [start, end] = trimmed.split('-').map(Number)
            if (!isNaN(start) && !isNaN(end)) {
                for (let i = start; i <= Math.min(end, start + 50); i++) {
                    result.push(i)
                }
            }
        } else {
            const num = Number(trimmed)
            if (!isNaN(num) && num >= 1 && num <= 4094) {
                result.push(num)
            }
        }
    }

    return result
}

// ─── 分组容器 ──────────────────────────────────────────────

const groupRenameVisible = ref(false)
const editingGroupId = ref<string | null>(null)
const groupRenameForm = reactive({ name: '' })

/** 添加分组容器 */
function handleAddGroup() {
    if (!graph) return
    const nodeId = `group_${Date.now()}`
    graph.addNode({
        id: nodeId,
        shape: 'group-node',
        x: 100,
        y: 100,
        width: 300,
        height: 200,
        attrs: {
            label: { text: '新分组' },
        },
        data: { isGroup: true },
    })
    ElMessage.success('分组已添加，双击可改名，拖拽设备到框内自动归入分组')
}

/** 保存分组改名 */
function handleGroupRename() {
    if (!graph || !editingGroupId.value) return
    const node = graph.getCellById(editingGroupId.value)
    if (node && node.isNode()) {
        node.setAttrByPath('label/text', groupRenameForm.name)
    }
    groupRenameVisible.value = false
    editingGroupId.value = null
}

// ─── 自动布局 ──────────────────────────────────────────────

// ─── 导出设备到命令工作台 ─────────────────────────────────

/** 收集拓扑中所有设备及其连线信息，导出到 topologyStore */
function handleExportToWorkbench() {
    if (!graph) return
    const nodes = graph.getNodes().filter(n => n.shape !== 'group-node')
    if (nodes.length === 0) { ElMessage.warning('拓扑中没有设备，请先拖入设备'); return }

    const allEdges = graph.getEdges()
    const typeNames: Record<string, string> = {
        'core-switch': '核心交换机', 'agg-switch': '汇聚交换机',
        'access-switch': '接入交换机', 'router': '路由器',
        'firewall': '防火墙', 'server': '服务器', 'pc': '终端PC',
    }

    const devices = nodes.map(node => {
        const data = node.getData() || {}
        const type = data.type || 'access-switch'

        // 收集该节点的所有连线信息
        const ports: any[] = []
        const vlanSet = new Set<number>()

        for (const edge of allEdges) {
            const srcId = (edge.getSourceCellId?.() || (edge.getSource() as any)?.cell) as string
            const tgtId = (edge.getTargetCellId?.() || (edge.getTarget() as any)?.cell) as string
            if (srcId !== node.id && tgtId !== node.id) continue

            const ed = edge.getData?.() || {}
            const isSource = srcId === node.id
            const remoteId = isSource ? tgtId : srcId
            // graph 已在上方校验非空，此处安全
            const g = graph!
            const remoteNode = g.getCellById(remoteId)
            const remoteLabel = remoteNode?.getAttrByPath?.('label/text') as string
                || remoteNode?.getData?.()?.hostname || (remoteId as string || '未知')

            // 收集 VLAN
            if (ed.vlanId) vlanSet.add(ed.vlanId)
            if (ed.allowedVlans) ed.allowedVlans.forEach((v: number) => vlanSet.add(v))

            ports.push({
                interface: isSource ? (ed.sourcePort || '') : (ed.targetPort || ''),
                remoteDevice: remoteLabel,
                remotePort: isSource ? (ed.targetPort || '') : (ed.sourcePort || ''),
                linkType: ed.linkType || 'trunk',
                vlanId: ed.vlanId,
                allowedVlans: ed.allowedVlans,
                ipNetwork: ed.ipNetwork || '',
                bandwidth: ed.bandwidth || '1G',
                direction: isSource ? 'uplink' : 'downlink',
            })
        }

        return {
            id: node.id,
            type,
            typeName: typeNames[type] || '交换机',
            hostname: data.hostname || node.getAttrByPath?.('label/text') || `SW-${type.slice(0, 4)}`,
            mgmtIp: data.mgmtIp || data.ip || '',
            vlans: [...vlanSet].sort((a, b) => a - b).join(',') || '',
            description: data.description || data.role || '',
            ports,
            x: node.getPosition().x,
            y: node.getPosition().y,
        }
    })

    topologyStore.exportedDevices = devices
    // 导出连线：用设备的 hostname 作为 source/target，保证与项目画布一致
    const hostnames: Record<string, string> = {}
    for (const d of devices) hostnames[d.id] = d.hostname
    topologyStore.exportedEdges = allEdges.map(e => ({
      source: hostnames[e.getSourceCellId()] || e.getSourceCellId(),
      target: hostnames[e.getTargetCellId()] || e.getTargetCellId(),
      linkType: (e.getData() as any)?.linkType || 'trunk',
      vlanId: (e.getData() as any)?.vlanId,
      bandwidth: (e.getData() as any)?.bandwidth,
      sourcePort: (e.getData() as any)?.sourcePort,
      targetPort: (e.getData() as any)?.targetPort,
    }))
    ElMessage.success(`已导出 ${devices.length} 台设备 + ${topologyStore.exportedEdges.length} 条连线`)
}

/** 导出拓扑文档报告 */
async function exportReport() {
    if (!graph) return
    const data = saveGraphData()
    try {
        const res = await fetch('/api/report/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        })
        if (!res.ok) throw new Error()
        const blob = await res.blob()
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = 'topology-report.md'
        link.click()
        ElMessage.success('报告已导出')
    } catch {
        ElMessage.error('报告生成失败')
    }
}

/** 自动布局：基于 dagre 算法，根据连线关系自动排列 */
function handleAutoLayout() {
    if (!graph) return

    const nodes = graph.getNodes().filter(n => n.shape !== 'group-node')
    const edges = graph.getEdges()

    if (nodes.length < 2) {
        ElMessage.warning('至少需要 2 个节点才能自动布局')
        return
    }

    // 创建 dagre 图谱
    const g = new dagre.graphlib.Graph()
    g.setGraph({ rankdir: 'TB', nodesep: 80, ranksep: 120, marginx: 60, marginy: 60 })
    g.setDefaultEdgeLabel(() => ({}))

    // 添加节点（设置默认尺寸）
    const NODE_W = 140, NODE_H = 80
    for (const node of nodes) {
        const size = node.getSize()
        g.setNode(node.id, { width: size.width || NODE_W, height: size.height || NODE_H })
    }

    // 添加边
    for (const edge of edges) {
        const source = edge.getSourceCellId()
        const target = edge.getTargetCellId()
        if (source && target) g.setEdge(source, target)
    }

    // 运行 dagre 布局
    dagre.layout(g)

    // 应用位置到 X6 节点（带过渡动画）
    graph.startBatch('auto-layout')
    for (const node of nodes) {
        const pos = g.node(node.id)
        if (pos) {
            const targetX = pos.x - pos.width / 2
            const targetY = pos.y - pos.height / 2
            // 使用 transition 实现平滑移动
            node.transition('position', { x: targetX, y: targetY }, {
                duration: 400,
                easing: 'easeOutCubic',
                interp: (a: number, b: number) => (t: number) => a + (b - a) * t,
            })
        }
    }

    // 自动调整分组容器大小
    for (const node of graph.getNodes()) {
        if (node.shape !== 'group-node') continue
        const children = node.getChildren() || []
        if (children.length === 0) continue

        let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0
        for (const child of children) {
            const bbox = child.getBBox()
            minX = Math.min(minX, bbox.x)
            minY = Math.min(minY, bbox.y)
            maxX = Math.max(maxX, bbox.x + bbox.width)
            maxY = Math.max(maxY, bbox.y + bbox.height)
        }

        const padding = 40
        node.setPosition({ x: minX - padding, y: minY - padding - 20 })
        node.setSize({ width: maxX - minX + padding * 2, height: maxY - minY + padding * 2 + 20 })
    }
    graph.stopBatch('auto-layout')

    // 居中显示（带缩放过渡）
    setTimeout(() => graph.centerContent({ padding: 40, useTransition: true }), 450)
    ElMessage.success('自动布局完成')
}

// 拖拽添加节点
onMounted(() => {
  if (!canvasRef.value) return
  canvasRef.value.addEventListener('dragover', (e) => e.preventDefault())
  canvasRef.value.addEventListener('drop', onDrop)
  document.addEventListener('keydown', handleKeyDelete)
})

function onDrop(e: DragEvent) {
  if (!graph) return
  e.preventDefault()

  const type = e.dataTransfer?.getData('deviceType')
  const color = e.dataTransfer?.getData('deviceColor')
  const iconUrl = e.dataTransfer?.getData('deviceIcon')
  const role = e.dataTransfer?.getData('deviceRole')
  if (!type) return

  const rect = canvasRef.value!.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top

  const nodeId = `${type}_${Date.now()}`
  
  graph.addNode({
    id: nodeId,
    x: x - 40,
    y: y - 30,
    width: 80,
    height: 60,
    shape: 'custom-device',
    attrs: {
      image: {
        'xlink:href': iconUrl,
      },
      label: {
        text: nodeId,
      },
    },
    data: {
      type,
      role,
      vendor: 'huawei',
      hostname: '',
      iconUrl,
      color,
    },
  })
}

function handleDeleteSelected() {
  if (!graph) return
  if (topologyStore.selectedNode) {
    graph.removeCell(topologyStore.selectedNode.id)
    topologyStore.selectedNode = null
    ElMessage.success('已删除设备')
  } else if (topologyStore.selectedEdge) {
    graph.removeCell(topologyStore.selectedEdge.id)
    topologyStore.selectedEdge = null
    ElMessage.success('已删除连线')
  }
}

function handleKeyDelete(e: KeyboardEvent) {
  if (e.key === 'Delete' || e.key === 'Backspace') {
    // 忽略输入框中的删除操作
    const tag = (e.target as HTMLElement)?.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
    e.preventDefault()
    handleDeleteSelected()
  }
}

function handleClear() {
  graph?.clearCells()
  topologyStore.selectedNode = null
  topologyStore.selectedEdge = null
  ElMessage.success('画布已清空')
}

async function handleSave() {
  if (!graph || !currentTopoId.value) return
  updateTopoStats()
  const json = graph.toJSON()
  await saveTopoData(currentTopoId.value, json)
  ElMessage.success(`"${topoList.value.find(t=>t.id===currentTopoId.value)?.name}" 已保存到服务器`)
}

function handleDownload() {
  if (!graph) return
  const json = graph.toJSON()
  const name = topoList.value.find(t => t.id === currentTopoId.value)?.name || 'topology'
  const blob = new Blob([JSON.stringify(json, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `${name}_${new Date().toISOString().slice(0,10)}.json`; a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('JSON 文件已下载到本地')
}

const fileInput = document.createElement('input')
fileInput.type = 'file'; fileInput.accept = '.json'; fileInput.style.display = 'none'
fileInput.onchange = async (e) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file || !graph) return
  const reader = new FileReader()
  reader.onload = async (ev) => {
    try {
      const json = JSON.parse(ev.target?.result as string)
      const result = await importTopo(json)
      topoList.value.push({ id: result.id, name: result.name })
      currentTopoId.value = result.id
      graph?.fromJSON(json)
      ElMessage.success(`已导入并新建方案: ${result.name}`)
    } catch { ElMessage.error('JSON 格式无效，请检查文件') }
  }
  reader.readAsText(file)
}
document.body.appendChild(fileInput)

function handleImportJson() {
  if (!graph) return
  fileInput.value = ''; fileInput.click()
}

function handleUndo() { graph?.undo() }
function handleRedo() { graph?.redo() }

/** 导出拓扑图为 PNG 图片 */
async function handleExportPng() {
  if (!graph) return
  try {
    // X6 exportPNG 返回 base64 data URL
    const dataUrl = await graph.exportPNG('png', {
      padding: 20,
      backgroundColor: '#ffffff',
      ratio: 1,
    })
    const a = document.createElement('a')
    a.href = dataUrl
    a.download = `topology_${Date.now()}.png`
    a.click()
    ElMessage.success('PNG 图片已导出')
  } catch (e: any) {
    ElMessage.error('导出失败: ' + (e.message || ''))
  }
}
</script>

<style scoped>
.topology-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-left .title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

/* ── 行2：保存/导入/导出/命令工作台 ── */
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.canvas-wrapper {
  flex: 1;
  background: #fff;
  min-height: 300px;
  position: relative;
  overflow: hidden;
}

/* 连线编辑弹窗中的设备归属条 */
.edge-devices-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 10px 16px;
  margin-bottom: 8px;
  background: #f5f7fa;
  border-radius: 8px;
}

.edge-device {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
}

.edge-device.source {
  background: #ecf5ff;
  color: #409eff;
  border: 1px solid #d9ecff;
}

.edge-device.target {
  background: #fef0e6;
  color: #e6a23c;
  border: 1px solid #faecd8;
}

.edge-arrow {
  font-size: 18px;
  color: #909399;
}
.collab-dot { width: 8px; height: 8px; border-radius: 50%; background: #cbd5e1; transition: background .3s; }
.collab-dot.online { background: #10b981; box-shadow: 0 0 4px rgba(16,185,129,.4); }
</style>

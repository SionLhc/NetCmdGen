<template>
  <div class="topology-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="title">企业园区网拓扑编辑器</span>
        <el-button size="small" @click="handleAddGroup">+ 添加分组</el-button>
        <el-button size="small" @click="handleAutoLayout">自动布局</el-button>
        <el-divider direction="vertical" />
        <el-button size="small" @click="handleClear">清空</el-button>
        <el-button size="small" @click="handleSave">保存拓扑</el-button>
        <el-button size="small" @click="handleLoad">加载拓扑</el-button>
        <el-divider direction="vertical" />
        <el-button type="success" size="small" @click="handleExportToWorkbench">导出到命令工作台</el-button>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" size="small" @click="handleGenerateAll" :loading="topologyStore.generating">
          一键生成全部配置
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧设备库 -->
      <DevicePalette />

      <!-- 中间：画布 + 配置输出 -->
      <div class="center-area">
        <div class="canvas-wrapper" ref="canvasRef"></div>
        <ConfigOutput />
      </div>

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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, reactive } from 'vue'
import { Graph } from '@antv/x6'
import { ElMessage } from 'element-plus'
import { useTopologyStore } from '@/stores/topology'
import { generateCampusConfig } from '@/api'
import { analyzeTopology } from '@/utils/topologyAnalyzer'
import { buildConfigParams, formatConfigOutput } from '@/utils/configGenerator'
import DevicePalette from '@/components/topology/DevicePalette.vue'
import PropertyPanel from '@/components/topology/PropertyPanel.vue'
import ConfigOutput from '@/components/topology/ConfigOutput.vue'

const topologyStore = useTopologyStore()
const canvasRef = ref<HTMLDivElement>()

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
})

onBeforeUnmount(() => {
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
  })

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

  // 初始化缩略图导航
  initMiniMap()
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

// ─── 缩略图导航 ────────────────────────────────────────────

/** 初始化 MiniMap 缩略图（纯 Canvas 实现，兼容 X6 v3） */
function initMiniMap() {
    if (!graph || !canvasRef.value) return

    const container = document.createElement('div')
    container.className = 'x6-minimap-container'
    container.style.cssText = `
        position: absolute; bottom: 12px; right: 12px;
        width: 180px; height: 130px;
        border: 1px solid #dcdfe6; border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        background: #fff; overflow: hidden; z-index: 100;
        cursor: pointer;
    `
    const canvas = document.createElement('canvas')
    canvas.width = 180
    canvas.height = 130
    canvas.style.width = '180px'
    canvas.style.height = '130px'
    container.appendChild(canvas)

    canvasRef.value.style.position = 'relative'
    canvasRef.value.appendChild(container)

    // 点击缩略图定位到对应位置
    container.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect()
        const x = (e.clientX - rect.left) / 180
        const y = (e.clientY - rect.top) / 130
        if (graph) {
            const graphRect = graph.getGraphArea()
            graph.centerPoint(
                graphRect.x + graphRect.width * x,
                graphRect.y + graphRect.height * y
            )
        }
    })

    // 更新缩略图
    function updateMinimap() {
        if (!graph) return
        const ctx = canvas.getContext('2d')
        if (!ctx) return

        ctx.clearRect(0, 0, 180, 130)

        const graphArea = graph.getGraphArea()
        if (graphArea.width === 0 || graphArea.height === 0) return

        const scaleX = 170 / graphArea.width
        const scaleY = 120 / graphArea.height
        const scale = Math.min(scaleX, scaleY)

        // 绘制分组节点（半透明虚线框）
        for (const node of graph.getNodes()) {
            const bbox = node.getBBox()
            const x = (bbox.x - graphArea.x) * scale + 5
            const y = (bbox.y - graphArea.y) * scale + 5
            const w = bbox.width * scale
            const h = bbox.height * scale

            if (node.shape === 'group-node') {
                ctx.strokeStyle = '#a0cfff'
                ctx.lineWidth = 1
                ctx.setLineDash([3, 2])
                ctx.fillStyle = 'rgba(64,158,255,0.08)'
                ctx.fillRect(x, y, w, h)
                ctx.strokeRect(x, y, w, h)
                ctx.setLineDash([])
            } else {
                // 设备节点用颜色方块表示
                const data = node.getData() || {}
                const colorMap: Record<string, string> = {
                    'core-switch': '#409eff',
                    'agg-switch': '#e6a23c',
                    'access-switch': '#67c23a',
                    'router': '#f56c6c',
                    'firewall': '#f97316',
                    'cloud': '#4a90d9',
                }
                ctx.fillStyle = colorMap[data.type] || '#909399'
                ctx.fillRect(x, y, Math.max(w, 3), Math.max(h, 3))
            }
        }

        // 画视口框
        if (graphArea.width > 0) {
            const vp = {
                x: -graphArea.x * scale + 5,
                y: -graphArea.y * scale + 5,
                w: 170,
                h: 120,
            }
            ctx.strokeStyle = '#409eff'
            ctx.lineWidth = 1.5
            ctx.setLineDash([])
            ctx.strokeRect(
                Math.max(vp.x, 5), Math.max(vp.y, 5),
                Math.min(vp.w, 170), Math.min(vp.h, 120)
            )
        }
    }

    // 定时更新
    updateMinimap()
    setInterval(updateMinimap, 2000)
    graph.on('node:move', updateMinimap)
    graph.on('node:resize', updateMinimap)
    graph.on('cell:added', () => setTimeout(updateMinimap, 100))
    graph.on('cell:removed', () => setTimeout(updateMinimap, 100))
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
            const srcId = edge.getSourceCellId?.() || edge.getSource()?.cell
            const tgtId = edge.getTargetCellId?.() || edge.getTarget()?.cell
            if (srcId !== node.id && tgtId !== node.id) continue

            const ed = edge.getData?.() || {}
            const isSource = srcId === node.id
            const remoteId = isSource ? tgtId : srcId
            const remoteNode = graph.getCellById(remoteId as string)
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
        }
    })

    topologyStore.exportedDevices = devices
    ElMessage.success(`已导出 ${devices.length} 台设备 (含 ${allEdges.length} 条连线信息) 到命令工作台，请切换到「拓扑项目」Tab 查看`)
}

/** 自动布局：核心-汇聚-接入三层从上到下排列 */
function handleAutoLayout() {
    if (!graph) return

    const nodes = graph.getNodes()
    if (nodes.length < 2) {
        ElMessage.warning('至少需要 2 个节点才能自动布局')
        return
    }

    // 按角色分组
    const layers: Record<string, any[]> = {
        core: [],
        agg: [],
        access: [],
        other: [],
    }

    for (const node of nodes) {
        // 跳过分组节点
        if (node.shape === 'group-node') continue

        const data = node.getData() || {}
        const role = data.role || data.type || ''
        if (role.includes('core')) layers.core.push(node)
        else if (role.includes('agg')) layers.agg.push(node)
        else if (role.includes('access')) layers.access.push(node)
        else layers.other.push(node)
    }

    const startX = 100
    const layerGap = 180
    const nodeGap = 120

    function layoutLayer(layerNodes: any[], y: number) {
        const totalWidth = (layerNodes.length - 1) * nodeGap
        const startAtX = startX + (600 - totalWidth) / 2
        for (let i = 0; i < layerNodes.length; i++) {
            layerNodes[i].setPosition({ x: startAtX + i * nodeGap, y })
        }
    }

    let currentY = 80

    // 核心层在顶部
    if (layers.core.length > 0) {
        layoutLayer(layers.core, currentY)
        currentY += layerGap
    }

    // 汇聚层
    if (layers.agg.length > 0) {
        layoutLayer(layers.agg, currentY)
        currentY += layerGap
    }

    // 接入层
    if (layers.access.length > 0) {
        layoutLayer(layers.access, currentY)
        currentY += layerGap
    }

    // 其他设备
    if (layers.other.length > 0) {
        layoutLayer(layers.other, currentY)
    }

    // 自动调整分组容器大小以包含子节点
    for (const node of nodes) {
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

    ElMessage.success('自动布局完成')
}

// 拖拽添加节点
onMounted(() => {
  if (!canvasRef.value) return
  canvasRef.value.addEventListener('dragover', (e) => e.preventDefault())
  canvasRef.value.addEventListener('drop', onDrop)
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

function handleClear() {
  graph?.clearCells()
  topologyStore.selectedNode = null
  topologyStore.selectedEdge = null
  topologyStore.configOutput = ''
  ElMessage.success('画布已清空')
}

function handleSave() {
  if (!graph) return
  const json = graph.toJSON()
  const blob = new Blob([JSON.stringify(json, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `topology_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('拓扑已保存')
}

function handleLoad() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = (e: any) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      try {
        const json = JSON.parse(ev.target?.result as string)
        graph?.fromJSON(json)
        ElMessage.success('拓扑已加载')
      } catch {
        ElMessage.error('加载失败，文件格式错误')
      }
    }
    reader.readAsText(file)
  }
  input.click()
}

async function handleGenerateAll() {
  if (!graph) return
  const nodes = graph.getNodes()
  const edges = graph.getEdges()
  
  if (nodes.length === 0) {
    ElMessage.warning('画布中没有设备')
    return
  }

  topologyStore.generating = true
  
  try {
    // 步骤1：拓扑分析
    const topologyNodes = nodes.map(node => ({
      id: node.id,
      type: node.getData()?.type || 'switch',
      role: node.getData()?.role || 'access-switch',
      vendor: node.getData()?.vendor || 'huawei',
      hostname: node.getAttrByPath('text/text') || node.id,
      mgmtSubnet: node.getData()?.mgmtSubnet || '192.168.1.0/24',
    }))

    const topologyEdges = edges.map(edge => ({
      id: edge.id,
      source: edge.getSourceCellId(),
      target: edge.getTargetCellId(),
      sourcePort: edge.getData()?.sourcePort || '',
      targetPort: edge.getData()?.targetPort || '',
      linkType: edge.getData()?.linkType || 'trunk',
      vlanId: edge.getData()?.vlanId,
      allowedVlans: edge.getData()?.allowedVlans,
      bandwidth: edge.getData()?.bandwidth || '1G',
    }))

    // 找出核心交换机的管理网段
    const coreNode = topologyNodes.find(n => n.role === 'core-switch')
    const coreSubnet = coreNode?.mgmtSubnet || '192.168.1.0/24'
    
    const analysis = analyzeTopology(topologyNodes, topologyEdges, coreSubnet)
    
    // 步骤2：构建配置参数
    const configParams = buildConfigParams(topologyNodes, topologyEdges, analysis)
    
    // 步骤3：调用后端生成配置
    const outputs: Array<{ device: string; vendor: string; output: string }> = []
    
    for (const params of configParams) {
      // 确定场景类型
      let scene: 'campus_core' | 'campus_access' | 'campus_agg'
      if (params.role === 'core-switch') {
        scene = 'campus_core'
      } else if (params.role === 'agg-switch') {
        scene = 'campus_agg'
      } else {
        scene = 'campus_access'
      }
      
      try {
        const result = await generateCampusConfig({
          vendor: params.vendor,
          hostname: params.hostname,
          mgmt_ip: params.mgmtIp,
          vlans: params.vlans,
          interfaces: params.interfaces,
          routing: params.routing,
          stp: params.stp,
          scene,
        })
        
        outputs.push({
          device: params.hostname,
          vendor: params.vendor,
          output: result.output,
        })
      } catch (error: any) {
        outputs.push({
          device: params.hostname,
          vendor: params.vendor,
          output: `# 生成失败: ${error.response?.data?.detail || error.message}`,
        })
      }
    }
    
    // 步骤4：格式化输出
    topologyStore.configOutput = formatConfigOutput(outputs)
    
    ElMessage.success(`成功生成 ${outputs.length} 台设备的配置`)
  } catch (error: any) {
    ElMessage.error(`生成失败: ${error.message}`)
  } finally {
    topologyStore.generating = false
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

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.center-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.canvas-wrapper {
  flex: 1;
  background: #fff;
  min-height: 300px;
  position: relative;
}

.canvas-wrapper :deep(.x6-minimap-container) {
  position: absolute !important;
  bottom: 12px !important;
  right: 12px !important;
}

.canvas-wrapper :deep(.x6-minimap-container .x6-minimap-viewport) {
  border: 2px solid #409eff !important;
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
</style>

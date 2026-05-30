<template>
  <div class="topology-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="title">企业园区网拓扑编辑器</span>
        <el-button size="small" @click="handleClear">清空</el-button>
        <el-button size="small" @click="handleSave">保存拓扑</el-button>
        <el-button size="small" @click="handleLoad">加载拓扑</el-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
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
              targetMarker: {
                name: 'classic',
                width: 8,
                height: 8,
                fill: '#7a90b5',
                stroke: '#7a90b5',
              },
            },
          },
          labels: [],
          data: {
            linkType: 'trunk',
            sourcePort: '',
            targetPort: '',
            bandwidth: '1G',
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

  // 双击节点快速修改名称
  graph.on('node:dblclick', ({ node }) => {
    const currentLabel = node.getAttrByPath('label/text') as string || ''
    const newName = window.prompt('修改设备名称：', currentLabel)
    if (newName !== null && newName.trim() !== '') {
      node.setAttrByPath('label/text', newName.trim())
      const data = node.getData() || {}
      node.setData({ ...data, hostname: newName.trim() })
    }
  })

  // 点击连线
  graph.on('edge:click', ({ edge }) => {
    topologyStore.selectedEdge = edge
    topologyStore.selectedNode = null
  })

  // 点击画布空白处
  graph.on('blank:click', () => {
    topologyStore.selectedNode = null
    topologyStore.selectedEdge = null
  })
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
  height: calc(100vh - 128px);
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-left .title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
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
}
</style>

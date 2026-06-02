<template>
  <div ref="containerRef" class="pj-canvas-wrap"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { Graph } from '@antv/x6'
import { deviceIcons } from '@/components/topology/deviceIcons'
import type { TopologyEdgeExport } from '@/stores/topology'

interface CanvasDevice {
  id: string; hostname: string; type: string; typeName: string
  vendor: string; mgmtIp: string; vlans: string; generatedOutput?: string
}

const props = defineProps<{
  devices: CanvasDevice[]
  edges?: TopologyEdgeExport[]
  positions?: Record<string, { x: number; y: number }>
}>()

const emit = defineEmits<{ (e: 'select', ids: string[]): void }>()

const containerRef = ref<HTMLDivElement>()
let graph: Graph | null = null
let selectedIds = new Set<string>()

function getIcon(t: string) { return deviceIcons[t]?.iconUrl || '' }

function toggleSelect(id: string) {
  if (selectedIds.has(id)) selectedIds.delete(id)
  else selectedIds.add(id)
  updateNodeStyles()
  emit('select', [...selectedIds])
}

function updateNodeStyles() {
  if (!graph) return
  for (const node of graph.getNodes()) {
    const sel = selectedIds.has(node.id)
    const info = deviceIcons[(node.getData() as any)?.device?.type]
    const color = info?.color || '#94a3b8'
    node.setAttrs({
      body: {
        stroke: sel ? color : 'transparent',
        strokeWidth: sel ? 2.5 : 0,
      },
    })
    // 选中时加阴影高亮
    if (sel) {
      node.setProp('tools', [{
        name: 'boundary',
        args: { padding: 3, attrs: { fill: 'none', stroke: color, strokeWidth: 2, strokeOpacity: 0.4, rx: 8, ry: 8 } }
      }])
    } else {
      node.removeTools()
    }
  }
}

function initGraph() {
  if (!containerRef.value) return
  const w = containerRef.value.clientWidth || 700
  const h = containerRef.value.clientHeight || 500
  graph = new Graph({
    container: containerRef.value, width: w, height: h,
    background: { color: '#f8fafc' },
    grid: { size: 10, visible: true, type: 'dot', args: { color: '#e2e8f0', thickness: 1 } },
    panning: { enabled: true },
    mousewheel: { enabled: true, modifiers: 'ctrl' },
    autoResize: true,
  })
  graph.on('node:click', ({ node }) => toggleSelect(node.id))
  renderAll()
}

function makeNode(dev: CanvasDevice, x: number, y: number) {
  const info = deviceIcons[dev.type]; const hasGen = !!dev.generatedOutput
  return {
    id: dev.id, x, y, width: 128, height: 96, shape: 'rect',
    attrs: {
      body: {
        fill: hasGen ? '#f0fdf4' : '#ffffff',
        stroke: 'transparent', strokeWidth: 0,
        rx: 10, ry: 10,
      },
      // 阴影
      shadow: {
        ref: 'body', refWidth: '100%', refHeight: '100%',
        fill: '#000000', opacity: 0.04, rx: 10, ry: 10,
        refX: 0, refY: 2, width: 128, height: 96,
      },
      icon: {
        ref: 'body', refX: 0.5, refY: 0.35,
        x: -20, y: -20, width: 40, height: 40,
        'xlink:href': getIcon(dev.type),
      },
      nameLabel: {
        ref: 'body', refX: 0.5, refY: 0.78,
        text: dev.hostname,
        fill: '#334155', fontSize: 13, fontWeight: 600,
        textAnchor: 'middle', textVerticalAnchor: 'middle',
      },
    },
    markup: [
      { tagName: 'rect', selector: 'shadow' },
      { tagName: 'rect', selector: 'body' },
      { tagName: 'image', selector: 'icon' },
      { tagName: 'text', selector: 'nameLabel' },
    ],
    data: { device: dev },
  }
}

function makeEdge(src: string, tgt: string, ed: TopologyEdgeExport) {
  const labels: any[] = []
  if (ed.linkType) labels.push({ attrs: { text: { text: ed.linkType, fill: '#94a3b8', fontSize: 10 } }, position: { distance: 0.5 } })
  if (ed.vlanId) labels.push({ attrs: { text: { text: `VLAN${ed.vlanId}`, fill: '#10B981', fontSize: 9, fontWeight: 600 } }, position: { distance: 0.35 } })
  return {
    source: { cell: src }, target: { cell: tgt },
    attrs: {
      line: { stroke: '#6366f1', strokeWidth: 2.5,
        targetMarker: { name: 'classic', size: 8, fill: '#6366f1' } },
    },
    labels: labels.length > 0 ? labels : undefined,
  }
}

function renderAll() {
  if (!graph) return
  graph.clearCells()
  selectedIds.clear()
  emit('select', [])

  const devs = props.devices; const posMap = props.positions || {}
  const gW = (graph.options.width as number) || 700

  const layers = ['core-switch','router','firewall','agg-switch','access-switch','server','pc']
  const byRole = new Map<string, CanvasDevice[]>()
  for (const d of devs) { const a = byRole.get(d.type)||[]; a.push(d); byRole.set(d.type, a) }
  const H_GAP = 180, V_GAP = 140
  let y = 60

  for (const role of layers) {
    const list = byRole.get(role); if (!list || list.length === 0) continue
    const rowW = (list.length - 1) * H_GAP; const x0 = (gW - rowW) / 2
    for (let i = 0; i < list.length; i++) {
      const dev = list[i]
      const hasPos = posMap[dev.id]
      const x = hasPos ? hasPos.x : (x0 + i * H_GAP)
      const yy = hasPos ? hasPos.y : y
      graph!.addNode(makeNode(dev, x, yy))
    }
    y += V_GAP
  }

  if (props.edges && props.edges.length > 0) {
    const deviceIds = new Set(devs.map(d => d.id))
    for (const ed of props.edges) {
      if (!deviceIds.has(ed.source) || !deviceIds.has(ed.target)) continue
      graph!.addEdge(makeEdge(ed.source, ed.target, ed))
    }
  }
}

watch(() => [props.devices, props.edges], renderAll, { deep: true })

onMounted(() => nextTick(initGraph))
onBeforeUnmount(() => { graph?.dispose() })
</script>

<style scoped>
.pj-canvas-wrap { width: 100%; height: 100%; min-height: 300px; }
</style>

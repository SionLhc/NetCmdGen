<template>
  <div class="dash-app">
    <!-- 顶栏 -->
    <header class="dash-header">
      <div class="hd-left">
        <span class="hd-logo">📡</span>
        <span class="hd-title">NetFlow Monitor</span>
        <span class="hd-badge" v-if="streams.length">{{ streams.length }} streams</span>
      </div>
      <div class="hd-right">
        <button class="hd-btn" @click="showAdd=true">+ Add Device</button>
        <button class="hd-btn" @click="stopAll" v-if="streams.length">⏹ Stop All</button>
      </div>
    </header>

    <!-- 设备栏 + 接口多选 -->
    <div class="dev-bar">
      <div v-for="d in devices" :key="d.id" class="dev-chip" :class="{active: activeDev===d.id}" @click="onDevClick(d)">
        <span class="dev-dot"></span>
        <span>{{ d.name || d.host }}</span>
      </div>
      <div v-if="!devices.length" class="dev-empty">No devices — click + Add Device</div>
    </div>

    <!-- 接口选择条（当前设备） -->
    <div class="iface-strip" v-if="activeDev && devIfaces[activeDev]?.length">
      <span style="font-size:11px;color:#94a3b8;margin-right:8px">Interfaces:</span>
      <div v-for="f in devIfaces[activeDev]" :key="f.index" class="iface-tag"
        :class="{on: isStreamActive(activeDev, f.index)}"
        @click="toggleStream(devices.find(x=>x.id===activeDev)!, f)">
        {{ f.name }}
      </div>
      <span v-if="devIfaces[activeDev]?.length" style="font-size:10px;color:#94a3b8;margin-left:8px">
        点击切换监控
      </span>
    </div>
    <div class="iface-strip" v-else-if="activeDev" style="color:#94a3b8;font-size:11px;padding:6px 24px">
      Loading interfaces...
    </div>

    <!-- 速率概览卡片 -->
    <div class="stat-row">
      <div v-for="s in streams" :key="s.key" class="stat-tile" :class="s.rx >= s.tx ? 'rx-dominant' : 'tx-dominant'">
        <div class="tile-top">
          <span class="tile-dev">{{ s.dev?.name || s.dev?.host }}</span>
          <span class="tile-iface">{{ s.iface?.name }}</span>
          <span class="tile-close" @click="toggleStream(s.dev!, s.iface!)">✕</span>
        </div>
        <div class="tile-val">
          <div class="tile-rx">
            <span class="tile-dir">▼</span>
            <span class="tile-num">{{ s.rx }}</span>
            <span class="tile-unit">Mbps</span>
          </div>
          <div class="tile-tx">
            <span class="tile-dir">▲</span>
            <span class="tile-num">{{ s.tx }}</span>
            <span class="tile-unit">Mbps</span>
          </div>
        </div>
      </div>
      <div v-if="!streams.length && activeDev" class="stat-hint">
        Select interfaces from device dropdown to start monitoring
      </div>
      <div v-if="!activeDev" class="stat-hint">
        Click a device above, then select interfaces to monitor
      </div>
    </div>

    <!-- 主图表 -->
    <div class="chart-wrap">
      <div ref="chartRef" class="chart-canvas"></div>
      <div v-if="!streams.length" class="chart-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="width:52px;height:52px;opacity:.25;margin-bottom:12px">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
        <p style="font-size:13px;color:#94a3b8">Add a device and select interfaces</p>
        <p style="font-size:11px;color:#94a3b8">SNMP must be enabled: /snmp set enabled=yes</p>
      </div>
    </div>

    <!-- 添加设备 -->
    <el-dialog v-model="showAdd" title="Add RouterOS Device" width="360px">
      <el-form label-width="60px" size="default">
        <el-form-item label="Name"><el-input v-model="form.name" placeholder="Core-R1"/></el-form-item>
        <el-form-item label="IP"><el-input v-model="form.host" placeholder="192.168.88.1"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd=false">Cancel</el-button>
        <el-button type="primary" @click="saveDev">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

/* ── 设备 ── */
interface Dev { id: string; name: string; host: string; port: number }
interface Iface { index: number; name: string; speed: number; speed_label: string }

const devices = ref<Dev[]>([])
const activeDev = ref('')
const devIfaces = ref<Record<string, Iface[]>>({})
const form = reactive({ name: '', host: '' })
const showAdd = ref(false)

onMounted(loadDevices)

async function loadDevices() {
  try { const r = await fetch('/api/ros/devices'); devices.value = await r.json() } catch {}
}

async function saveDev() {
  if (!form.host) { ElMessage.warning('Enter IP'); return }
  await fetch('/api/ros/devices',{method:'PUT',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:form.name||form.host,host:form.host,port:443,username:'admin',password:''})})
  form.name = form.host = ''; showAdd.value = false
  await loadDevices(); ElMessage.success('Saved')
}

watch(activeDev, async (id) => {
  if (!id) return
  if (devIfaces.value[id]) return
  await fetchIfaces(id)
})

async function fetchIfaces(id: string) {
  const d = devices.value.find(x => x.id === id)
  if (!d) return
  try {
    const r = await fetch(`/api/ros/traffic/interfaces?host=${encodeURIComponent(d.host)}`)
    devIfaces.value[id] = await r.json()
  } catch { devIfaces.value[id] = [] }
}

async function onDevClick(d: Dev) {
  activeDev.value = d.id
  // 主动加载接口
  if (!devIfaces.value[d.id]) await fetchIfaces(d.id)
}

/* ── 多流管理 ── */
interface Stream {
  key: string
  dev: Dev | null
  iface: Iface | null
  rx: number; tx: number
  points: { ts: number; rx: number; tx: number }[]
  ctrl: AbortController | null
}

const streams = ref<Stream[]>([])
const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
const COLORS = ['#6366f1','#06b6d4','#f59e0b','#10b981','#ef4444','#8b5cf6','#ec4899','#14b8a6','#f97316','#3b82f6']

function isStreamActive(devId: string, ifIndex: number) {
  return streams.value.some(s => s.dev?.id === devId && s.iface?.index === ifIndex)
}

function makeKey(d: Dev, f: Iface) { return `${d.id}_${f.index}` }

function toggleStream(d: Dev, f: Iface) {
  const key = makeKey(d, f)
  const exist = streams.value.findIndex(s => s.key === key)
  if (exist >= 0) {
    // 移除
    streams.value[exist].ctrl?.abort()
    streams.value.splice(exist, 1)
    renderChart()
  } else {
    // 添加
    startStream(d, f)
  }
}

async function startStream(d: Dev, f: Iface) {
  const key = makeKey(d, f)
  const ctrl = new AbortController()
  const stream: Stream = { key, dev: d, iface: f, rx: 0, tx: 0, points: [], ctrl }
  streams.value.push(stream)
  renderChart()

  try {
    const url = `/api/ros/traffic/stream?host=${encodeURIComponent(d.host)}&if_index=${f.index}&duration_s=600`
    const resp = await fetch(url, { signal: ctrl.signal })
    const reader = resp.body!.getReader()
    const dec = new TextDecoder(); let buf = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += dec.decode(value, { stream: true })
      const lines = buf.split('\n'); buf = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const pt = JSON.parse(line.slice(6))
            if (pt.rx_mbps !== undefined) {
              stream.rx = pt.rx_mbps; stream.tx = pt.tx_mbps
              stream.points.push({ ts: pt.ts, rx: pt.rx_mbps, tx: pt.tx_mbps })
              renderChart()
            }
          } catch {}
        }
      }
    }
  } catch { /* aborted */ }
  finally {
    const idx = streams.value.findIndex(s => s.key === key)
    if (idx >= 0) streams.value.splice(idx, 1)
    renderChart()
  }
}

function stopAll() {
  streams.value.forEach(s => s.ctrl?.abort())
  streams.value = []
  renderChart()
}

/* ── ECharts ── */
function renderChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
    window.addEventListener('resize', () => chart?.resize())
  }

  const series: any[] = []
  const allTs = new Set<number>()

  streams.value.forEach((s, i) => {
    const color = COLORS[i % COLORS.length]
    const label = `${s.dev?.name||s.dev?.host}/${s.iface?.name}`
    s.points.forEach(p => allTs.add(p.ts))
    series.push({
      name: label + ' ▼',
      type: 'line', data: s.points.map(p => [p.ts, p.rx]),
      smooth: true, symbol: 'none',
      lineStyle: { color, width: 2 },
      itemStyle: { color },
    })
    series.push({
      name: label + ' ▲',
      type: 'line', data: s.points.map(p => [p.ts, p.tx]),
      smooth: true, symbol: 'none',
      lineStyle: { color, width: 1.5, type: 'dashed' },
      itemStyle: { color },
    })
  })

  const sortedTs = [...allTs].sort()
  const labels = sortedTs.map(t => new Date(t*1000).toLocaleTimeString())

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,255,255,.95)', borderColor: '#e2e8f0', textStyle: { fontSize: 11 } },
    legend: {
      bottom: 0, textStyle: { color: '#8899aa', fontSize: 10 },
      type: 'scroll',
    },
    grid: { top: 16, right: 20, bottom: 40, left: 55 },
    xAxis: {
      type: 'category', data: labels, boundaryGap: false,
      axisLabel: { fontSize: 10, color: '#94a3b8' },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value', name: 'Mbps',
      nameTextStyle: { fontSize: 10, color: '#556' },
      axisLabel: { fontSize: 10, color: '#556' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    series,
  }, true)
}
</script>

<style>
/* 全局暗色覆盖 */

</style>

<style scoped>
.dash-app {
  height: calc(100vh - 60px);
  display: flex; flex-direction: column;
  background: #f5f6fa;
  color: #1e293b; font-family: 'Inter', 'Microsoft YaHei', sans-serif;
  overflow: hidden;
}

/* ── 顶栏 ── */
.dash-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 24px;
  background: #fff;
  
  border-bottom: 1px solid #e5e7eb;
}
.hd-left { display: flex; align-items: center; gap: 10px; }
.hd-logo { font-size: 20px; }
.hd-title { font-size: 16px; font-weight: 700; letter-spacing: .5px; }
.hd-badge { font-size: 11px; background: rgba(99,102,241,.2); color: #a5b4fc; padding: 2px 10px; border-radius: 10px; }
.hd-right { display: flex; gap: 8px; }
.hd-btn {
  background: #f1f5f9; border: 1px solid #e2e8f0;
  color: #475569; padding: 6px 14px; border-radius: 6px;
  font-size: 12px; cursor: pointer; transition: .15s;
}
.hd-btn:hover { background: rgba(255,255,255,.12); border-color:#94a3b8; }

/* ── 设备栏 ── */
.dev-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 24px; overflow-x: auto;
  border-bottom: 1px solid #e5e7eb;
}
.dev-chip {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 20px;
  background: #fff; border: 1px solid #e2e8f0;
  font-size: 12px; cursor: pointer; white-space: nowrap; transition: .15s;
}
.dev-chip:hover { background: #f1f5f9; }
.dev-chip.active { background: #eff6ff; border-color: #93c5fd; }
.dev-dot { width: 7px; height: 7px; border-radius: 50%; background: #10b981; box-shadow: 0 0 6px #10b981; }
.dev-arrow { font-size: 10px; color: #94a3b8; margin-left: 2px; }
.dev-empty { font-size: 12px; color: #94a3b8; padding: 4px 0; }

/* 接口下拉 */
.iface-row {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 12px; cursor: pointer; font-size: 12px; border-bottom: 1px solid #f0f0f0;
}
.iface-row:hover { background: #f5f7fa; }
.iface-row.checked { background: #eef2ff; }
.iface-dot { width: 8px; height: 8px; border-radius: 50%; background: #ddd; }
.iface-dot.on { background: #6366f1; }

/* ── 速率卡片 ── */
.stat-row {
  display: flex; gap: 12px; padding: 14px 24px; overflow-x: auto;
  min-height: 80px; align-items: center;
}
.stat-tile {
  min-width: 180px; padding: 12px 16px; border-radius: 12px;
  background: #fff; border: 1px solid #e2e8f0;
  flex-shrink: 0;
}
.stat-tile.rx-dominant { border-left: 3px solid #6366f1; }
.stat-tile.tx-dominant { border-left: 3px solid #f59e0b; }
.tile-top { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.tile-dev { font-size: 11px; font-weight: 600; color: #64748b; }
.tile-iface { font-size: 11px; color: #94a3b8; }
.tile-close { margin-left: auto; cursor: pointer; font-size: 10px; color: #94a3b8; }
.tile-close:hover { color: #ef4444; }
.tile-val { display: flex; gap: 16px; }
.tile-rx, .tile-tx { display: flex; align-items: baseline; gap: 2px; }
.tile-dir { font-size: 10px; }
.tile-rx .tile-dir { color: #6366f1; }
.tile-tx .tile-dir { color: #f59e0b; }
.tile-num { font-size: 22px; font-weight: 700; font-family: monospace; color: #1e293b; }
.tile-unit { font-size: 10px; color: #94a3b8; margin-left: 2px; }
.stat-hint {
  font-size: 13px; color:#94a3b8; text-align: center; flex: 1;
}

/* ── 图表 ── */
.chart-wrap { flex: 1; position: relative; margin: 0 24px 16px; border-radius: 12px;
  background: #fff; border: 1px solid #e5e7eb; overflow: hidden; }
.chart-canvas { width: 100%; height: 100%; }
.chart-empty {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
</style>

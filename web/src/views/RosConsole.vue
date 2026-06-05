<template>
  <div class="dash-app">
    <!-- 顶栏 -->
    <header class="dash-header">
      <div class="hd-left">
        <span class="hd-logo">📡</span>
        <span class="hd-title">NetFlow Monitor</span>
        <span class="hd-badge" v-if="streams.length">{{ streams.length }} 条监控</span>
      </div>
      <div class="hd-right">
        <button class="hd-btn" @click="showAdd=true">+ 添加设备</button>
        <button class="hd-btn" @click="stopAll" v-if="streams.length">⏹ 全部停止</button>
      </div>
    </header>

    <!-- 控制栏：设备下拉 + 接口标签 -->
    <div class="control-bar">
      <el-select v-model="activeDev" placeholder="选择设备" size="default" style="width:220px"
        @change="onDevSelect" :loading="loadingDevices">
        <el-option v-for="d in devices" :key="d.id" :label="d.name || d.host" :value="d.id">
          <span style="display:flex;align-items:center;gap:8px">
            <span class="dev-dot-sm"></span>{{ d.name || d.host }}
            <span style="color:#94a3b8;font-size:11px;margin-left:auto">{{ d.host }}</span>
          </span>
        </el-option>
      </el-select>

      <span class="control-sep" v-if="activeDev && devIfaces[activeDev]?.length"></span>
      <div v-for="f in devIfaces[activeDev]" :key="f.index" class="iface-tag"
        :class="{on: isStreamActive(activeDev, f.index)}"
        v-show="activeDev && devIfaces[activeDev]?.length"
        @click="toggleStream(devices.find(x=>x.id===activeDev)!, f)">
        <span class="iface-name">{{ f.name }}</span>
        <span class="iface-speed">{{ f.speed_label }}</span>
      </div>
      <span v-if="activeDev && !devIfaces[activeDev]" style="font-size:11px;color:#94a3b8">加载接口中...</span>
      <span v-if="!activeDev" style="font-size:11px;color:#94a3b8">选择设备后，点击接口标签开始监控</span>
    </div>

    <!-- 监控卡片网格 -->
    <div class="monitor-grid" v-if="streams.length">
      <div v-for="s in streams" :key="s.key" class="mon-card">
        <!-- 卡片顶栏 -->
        <div class="card-head">
          <div class="card-dev-line">
            <span class="card-dev">{{ s.dev?.name || s.dev?.host }}</span>
            <span class="card-arrow">›</span>
            <span class="card-iface">{{ s.iface?.name }}</span>
            <span class="card-close" @click="toggleStream(s.dev!, s.iface!)">✕</span>
          </div>
          <div class="card-speeds">
            <div class="speed-box speed-down">
              <span class="speed-label">▼ 下载</span>
              <span class="speed-val">{{ s.rx >= 0 ? s.rx.toFixed(1) : '—' }}</span>
              <span class="speed-unit">Mbps</span>
            </div>
            <div class="speed-box speed-up">
              <span class="speed-label">▲ 上传</span>
              <span class="speed-val">{{ s.tx >= 0 ? s.tx.toFixed(1) : '—' }}</span>
              <span class="speed-unit">Mbps</span>
            </div>
          </div>
        </div>
        <!-- 独立图表 -->
        <div :ref="(el) => setChartRef(s.key, el as HTMLElement)" class="card-chart"></div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-zone" v-else>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:48px;height:48px;opacity:.2;margin-bottom:12px">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
      <p v-if="!activeDev" style="font-size:13px;color:#94a3b8">从下拉框选择设备，点击接口标签开始</p>
      <p v-else style="font-size:13px;color:#94a3b8">点击上方接口标签开始实时监控</p>
      <p style="font-size:11px;color:#94a3b8">需开启 SNMP：/snmp set enabled=yes</p>
    </div>

    <!-- 添加设备弹窗 -->
    <el-dialog v-model="showAdd" title="添加 RouterOS 设备" width="380px">
      <el-form label-width="50px" size="default">
        <el-form-item label="名称"><el-input v-model="form.name" placeholder="如: Core-R1"/></el-form-item>
        <el-form-item label="IP"><el-input v-model="form.host" placeholder="192.168.88.1"/></el-form-item>
        <el-form-item label="提示">
          <span style="font-size:11px;color:#94a3b8">
            RouterOS 需先开启 SNMP：
            <code style="background:#f1f5f9;padding:2px 6px;border-radius:4px">/snmp set enabled=yes</code>
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd=false">取消</el-button>
        <el-button type="primary" @click="saveDev">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

/* ── 类型 ── */
interface Dev { id: string; name: string; host: string; port: number }
interface Iface { index: number; name: string; speed: number; speed_label: string }
interface Stream {
  key: string
  dev: Dev | null
  iface: Iface | null
  rx: number; tx: number
  points: { ts: number; rx: number; tx: number }[]
  ctrl: AbortController | null
  chart: echarts.ECharts | null
}

/* ── 设备管理 ── */
const devices = ref<Dev[]>([])
const activeDev = ref('')
const devIfaces = ref<Record<string, Iface[]>>({})
const form = reactive({ name: '', host: '' })
const showAdd = ref(false)
const loadingDevices = ref(false)

onMounted(loadDevices)

async function loadDevices() {
  loadingDevices.value = true
  try { const r = await fetch('/api/ros/devices'); devices.value = await r.json() } catch {}
  finally { loadingDevices.value = false }
}

async function saveDev() {
  if (!form.host) { ElMessage.warning('请输入 IP'); return }
  await fetch('/api/ros/devices',{method:'PUT',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:form.name||form.host,host:form.host,port:443,username:'admin',password:''})})
  form.name = form.host = ''; showAdd.value = false
  await loadDevices(); ElMessage.success('已保存')
}

async function fetchIfaces(id: string) {
  const d = devices.value.find(x => x.id === id)
  if (!d) return
  try {
    const r = await fetch(`/api/ros/traffic/interfaces?host=${encodeURIComponent(d.host)}`)
    devIfaces.value[id] = await r.json()
  } catch { devIfaces.value[id] = [] }
}

async function onDevSelect(id: string) {
  if (!id) return
  if (!devIfaces.value[id]) await fetchIfaces(id)
}

/* ── 图表 ref 映射 ── */
const chartEls = new Map<string, HTMLElement>()
function setChartRef(key: string, el: HTMLElement | null) {
  if (el) { chartEls.set(key, el); renderStreamChart(key) }
  else chartEls.delete(key)
}

/* ── 多流管理 ── */
const streams = ref<Stream[]>([])
const COLORS = ['#6366f1','#06b6d4']

function isStreamActive(devId: string, ifIndex: number) {
  return streams.value.some(s => s.dev?.id === devId && s.iface?.index === ifIndex)
}

function makeKey(d: Dev, f: Iface) { return `${d.id}_${f.index}` }

function toggleStream(d: Dev, f: Iface) {
  const key = makeKey(d, f)
  const exist = streams.value.findIndex(s => s.key === key)
  if (exist >= 0) {
    streams.value[exist].ctrl?.abort()
  } else {
    startStream(d, f)
  }
}

async function startStream(d: Dev, f: Iface) {
  const key = makeKey(d, f)
  const ctrl = new AbortController()
  const stream: Stream = { key, dev: d, iface: f, rx: 0, tx: 0, points: [], ctrl, chart: null }
  streams.value.push(stream)

  // 等 DOM 渲染后初始化图表
  await nextTick()
  renderStreamChart(key)

  try {
    const url = `/api/ros/traffic/stream?host=${encodeURIComponent(d.host)}&if_index=${f.index}&duration_s=299`
    const resp = await fetch(url, { signal: ctrl.signal })
    if (!resp.ok) {
      stream.rx = stream.tx = -1
      ElMessage.error(`SNMP 连接失败 (${resp.status})`)
      renderStreamChart(key)
      return
    }
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
              renderStreamChart(key)
            }
          } catch {}
        }
      }
    }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      // 用户停止 → 清理
      stream.chart?.dispose()
      const idx = streams.value.findIndex(s => s.key === key)
      if (idx >= 0) streams.value.splice(idx, 1)
      chartEls.delete(key)
      return
    }
    ElMessage.error(`SNMP 中断: ${err.message}`)
    stream.rx = stream.tx = -1
    renderStreamChart(key)
  }
}

function stopAll() {
  // 先清理所有图表
  streams.value.forEach(s => { s.chart?.dispose(); s.ctrl?.abort() })
  streams.value = []
  chartEls.clear()
}

/* ── 单个图表渲染 ── */
function renderStreamChart(key: string) {
  const el = chartEls.get(key)
  if (!el) return
  const stream = streams.value.find(s => s.key === key)
  if (!stream) return

  // 初始化或复用实例
  if (!stream.chart) {
    stream.chart = echarts.init(el)
  }

  const colorRx = COLORS[0]
  const colorTx = COLORS[1]
  const dataRx = stream.points.map(p => [p.ts * 1000, p.rx])
  const dataTx = stream.points.map(p => [p.ts * 1000, p.tx])

  stream.chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,.95)',
      borderColor: '#e2e8f0',
      textStyle: { fontSize: 10, color: '#1e293b' },
      formatter: (params: any[]) => {
        if (!params.length) return ''
        const t = new Date(params[0].data[0]).toLocaleTimeString()
        let h = `<div style="font-weight:600">${t}</div>`
        params.forEach(p => {
          h += `<div style="font-size:11px"><span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:${p.color};margin-right:4px"></span>${p.seriesName} <b>${Number(p.data[1]).toFixed(2)}</b> Mbps</div>`
        })
        return h
      },
    },
    grid: { top: 14, right: 12, bottom: 14, left: 40 },
    xAxis: {
      type: 'time',
      axisLabel: { fontSize: 9, color: '#94a3b8' },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'Mbps',
      nameTextStyle: { fontSize: 9, color: '#94a3b8' },
      axisLabel: { fontSize: 9, color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    series: [
      {
        name: '▼ 下载', type: 'line', data: dataRx,
        smooth: true, symbol: 'none',
        lineStyle: { color: colorRx, width: 1.8 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99,102,241,.12)' },
            { offset: 1, color: 'rgba(99,102,241,0)' },
          ]),
        },
      },
      {
        name: '▲ 上传', type: 'line', data: dataTx,
        smooth: true, symbol: 'none',
        lineStyle: { color: colorTx, width: 1.2, type: 'dashed' },
      },
    ],
  }, true)
}
</script>

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
  padding: 8px 24px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}
.hd-left { display: flex; align-items: center; gap: 10px; }
.hd-logo { font-size: 20px; }
.hd-title { font-size: 15px; font-weight: 700; }
.hd-badge { font-size: 11px; background: rgba(99,102,241,.1); color: #6366f1; padding: 2px 10px; border-radius: 10px; font-weight: 600; }
.hd-right { display: flex; gap: 8px; }
.hd-btn {
  background: #f1f5f9; border: 1px solid #e2e8f0;
  color: #475569; padding: 5px 12px; border-radius: 6px;
  font-size: 12px; cursor: pointer; transition: .15s;
}
.hd-btn:hover { background: #e2e8f0; }

/* ── 控制栏 ── */
.control-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 24px; flex-wrap: wrap;
  border-bottom: 1px solid #e5e7eb; background: #fff;
  flex-shrink: 0; min-height: 44px;
}
.control-sep { width: 1px; height: 18px; background: #e2e8f0; margin: 0 2px; }
.dev-dot-sm { width: 6px; height: 6px; border-radius: 50%; background: #10b981; flex-shrink: 0; }

.iface-tag {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px; border-radius: 12px; font-size: 11px; cursor: pointer;
  background: #f8fafc; color: #475569; border: 1px solid #e2e8f0;
  transition: all .15s; white-space: nowrap;
}
.iface-tag:hover { background: #f1f5f9; border-color: #cbd5e1; }
.iface-tag.on { background: #6366f1; color: #fff; border-color: #6366f1; }
.iface-name { font-weight: 500; }
.iface-speed { font-size: 10px; opacity: .65; }
.iface-tag.on .iface-speed { opacity: .8; }

/* ── 监控卡片网格 ── */
.monitor-grid {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 12px; padding: 12px 24px; align-content: start;
}

.mon-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  display: flex; flex-direction: column;
  min-height: 240px; max-height: 360px;
  overflow: hidden;
}

/* ── 卡片头部 ── */
.card-head {
  padding: 10px 14px 6px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}
.card-dev-line {
  display: flex; align-items: center; gap: 4px;
  font-size: 11px; margin-bottom: 6px;
}
.card-dev { color: #64748b; font-weight: 600; }
.card-arrow { color: #94a3b8; font-size: 10px; }
.card-iface { color: #1e293b; }
.card-close {
  margin-left: auto; cursor: pointer;
  font-size: 10px; color: #94a3b8; padding: 2px 4px;
}
.card-close:hover { color: #ef4444; }

.card-speeds {
  display: flex; gap: 16px;
}
.speed-box {
  display: flex; align-items: baseline; gap: 4px;
}
.speed-label { font-size: 10px; color: #94a3b8; }
.speed-val { font-size: 18px; font-weight: 700; }
.speed-unit { font-size: 10px; color: #94a3b8; margin-left: 2px; }
.speed-down .speed-val { color: #6366f1; }
.speed-up .speed-val { color: #06b6d4; }

/* ── 卡片图表 ── */
.card-chart {
  flex: 1; min-height: 0;
  width: 100%;
}

/* ── 空状态 ── */
.empty-zone {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
</style>

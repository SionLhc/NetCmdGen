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

    <!-- 设备选择 + 接口筛选行 -->
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

      <!-- 当前设备的接口标签常驻 -->
      <template v-if="activeDev && devIfaces[activeDev]?.length">
        <span class="control-sep"></span>
        <div v-for="f in devIfaces[activeDev]" :key="f.index" class="iface-tag"
          :class="{on: isStreamActive(activeDev, f.index)}"
          @click="toggleStream(devices.find(x=>x.id===activeDev)!, f)">
          <span class="iface-name">{{ f.name }}</span>
          <span class="iface-speed">{{ f.speed_label }}</span>
        </div>
      </template>
      <span v-else-if="activeDev" style="font-size:11px;color:#94a3b8">加载接口中...</span>
      <span v-else style="font-size:11px;color:#94a3b8">添加设备后在这里选择</span>
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
            <span class="tile-num">{{ s.rx >= 0 ? s.rx.toFixed(1) : '—' }}</span>
            <span class="tile-unit"> Mbps</span>
          </div>
          <div class="tile-tx">
            <span class="tile-dir">▲</span>
            <span class="tile-num">{{ s.tx >= 0 ? s.tx.toFixed(1) : '—' }}</span>
            <span class="tile-unit"> Mbps</span>
          </div>
        </div>
      </div>
      <div v-if="!streams.length && activeDev" class="stat-hint">
        点击上方接口标签开始监控流量
      </div>
      <div v-if="!activeDev" class="stat-hint">
        从上方下拉框选择设备
      </div>
    </div>

    <!-- 主图表 -->
    <div class="chart-wrap" v-show="streams.length">
      <div ref="chartRef" class="chart-canvas"></div>
    </div>

    <!-- 添加设备弹窗 -->
    <el-dialog v-model="showAdd" title="添加 RouterOS 设备" width="380px">
      <el-form label-width="50px" size="default">
        <el-form-item label="名称"><el-input v-model="form.name" placeholder="如: Core-R1"/></el-form-item>
        <el-form-item label="IP"><el-input v-model="form.host" placeholder="192.168.88.1"/></el-form-item>
        <el-form-item label="提示">
          <span style="font-size:11px;color:#94a3b8">
            RouterOS 需先开启 SNMP：<code style="background:#f1f5f9;padding:2px 6px;border-radius:4px">/snmp set enabled=yes</code>
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
  // 设备切换时加载接口列表
  if (!devIfaces.value[id]) await fetchIfaces(id)
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
    // 仅发送 abort 信号，由 catch 块负责删除（避免竞态）
    streams.value[exist].ctrl?.abort()
  } else {
    // 添加新流
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
    // 注意：后端 duration_s 上限 300，这里传 299 留 1s 余量
    const url = `/api/ros/traffic/stream?host=${encodeURIComponent(d.host)}&if_index=${f.index}&duration_s=299`
    const resp = await fetch(url, { signal: ctrl.signal })
    if (!resp.ok) {
      // 请求失败（如 422 参数校验），保留流但标记错误
      const errBody = await resp.text()
      stream.rx = stream.tx = -1  // -1 表示错误状态
      ElMessage.error(`SNMP 连接失败 (${resp.status}): ${errBody.slice(0, 80)}`)
      renderChart()
      return  // 不进入 reader 循环，保留流在数组中显示错误
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
              renderChart()
            }
          } catch {}
        }
      }
    }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      // 用户手动停止 → 正常删除流
      const idx = streams.value.findIndex(s => s.key === key)
      if (idx >= 0) streams.value.splice(idx, 1)
      renderChart()
      return
    }
    // 其他网络错误 → 保留流，显示错误
    ElMessage.error(`SNMP 连接中断: ${err.message}`)
    stream.rx = stream.tx = -1
    renderChart()
  }
  // 正常结束（连接关闭/duration 耗尽）→ 保留数据和图表
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
    window.addEventListener('resize', () => {
      if (chartRef.value && chartRef.value.offsetParent) chart?.resize()
    })
  }

  const series: any[] = []

  streams.value.forEach((s, i) => {
    const color = COLORS[i % COLORS.length]
    const label = `${s.dev?.name||s.dev?.host}/${s.iface?.name}`
    // 时间轴用毫秒级时间戳，ECharts time 轴自动定位
    series.push({
      name: label + ' ▼ 下载',
      type: 'line',
      data: s.points.map(p => [p.ts * 1000, p.rx]),
      smooth: true, symbol: 'none',
      lineStyle: { color, width: 2 },
      itemStyle: { color },
    })
    series.push({
      name: label + ' ▲ 上传',
      type: 'line',
      data: s.points.map(p => [p.ts * 1000, p.tx]),
      smooth: true, symbol: 'none',
      lineStyle: { color, width: 1.5, type: 'dashed' },
      itemStyle: { color },
    })
  })

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,.95)',
      borderColor: '#e2e8f0',
      textStyle: { fontSize: 11, color: '#1e293b' },
      formatter: (params: any[]) => {
        if (!params.length) return ''
        const time = new Date(params[0].data[0]).toLocaleTimeString()
        let html = `<div style="font-weight:600;margin-bottom:4px">${time}</div>`
        params.forEach(p => {
          html += `<div style="display:flex;align-items:center;gap:6px">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
            ${p.seriesName}: <b>${Number(p.data[1]).toFixed(2)} Mbps</b>
          </div>`
        })
        return html
      },
    },
    legend: {
      bottom: 0,
      textStyle: { color: '#64748b', fontSize: 10 },
      type: 'scroll',
    },
    grid: { top: 16, right: 20, bottom: 36, left: 55 },
    xAxis: {
      type: 'time',
      axisLabel: {
        fontSize: 10, color: '#94a3b8',
        formatter: (val: any) => {
          const d = new Date(val)
          return d.toLocaleTimeString()
        },
      },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value', name: 'Mbps',
      nameTextStyle: { fontSize: 10, color: '#94a3b8' },
      axisLabel: { fontSize: 10, color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    series,
  }, true)

  // v-show 切显时容器尺寸可能为0，强制 resize
  nextTick(() => chart?.resize())
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
.hd-badge { font-size: 11px; background: rgba(99,102,241,.1); color: #6366f1; padding: 2px 10px; border-radius: 10px; font-weight: 600; }
.hd-right { display: flex; gap: 8px; }
.hd-btn {
  background: #f1f5f9; border: 1px solid #e2e8f0;
  color: #475569; padding: 6px 14px; border-radius: 6px;
  font-size: 12px; cursor: pointer; transition: .15s;
}
.hd-btn:hover { background: #e2e8f0; }

/* ── 控制栏（设备下拉 + 接口标签） ── */
.control-bar {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 24px; flex-wrap: wrap;
  border-bottom: 1px solid #e5e7eb; background: #fff;
}
.control-sep { width: 1px; height: 20px; background: #e2e8f0; margin: 0 4px; }
.dev-dot-sm { width: 6px; height: 6px; border-radius: 50%; background: #10b981; flex-shrink: 0; }

/* ── 接口标签 ── */
.iface-tag {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 14px; border-radius: 16px; font-size: 11px; cursor: pointer;
  background: #f8fafc; color: #475569; border: 1px solid #e2e8f0;
  transition: all .15s; white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0,0,0,.02);
}
.iface-tag:hover { background: #f1f5f9; border-color: #cbd5e1; }
.iface-tag.on { background: #6366f1; color: #fff; border-color: #6366f1; box-shadow: 0 2px 6px rgba(99,102,241,.25); }
.iface-name { font-weight: 500; }
.iface-speed { font-size: 10px; opacity: .7; }
.iface-tag.on .iface-speed { opacity: .85; }

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
  background: #fff; border: 1px solid #e5e7eb; overflow: hidden; min-height: 0; }
.chart-canvas { width: 100%; height: 100%; }
</style>

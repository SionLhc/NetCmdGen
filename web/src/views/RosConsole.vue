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

    <!-- 控制栏：多选设备 -->
    <div class="control-bar" style="flex-wrap:wrap">
      <el-select v-model="selectedDevs" placeholder="选择设备（可多选）" size="default" style="min-width:220px"
        multiple collapse-tags collapse-tags-tooltip :loading="loadingDevices">
        <el-option v-for="d in devices" :key="d.id" :label="d.name || d.host" :value="d.id">
          <span style="display:flex;align-items:center;gap:8px">
            <span class="dev-dot-sm"></span>{{ d.name || d.host }}
            <span style="color:#94a3b8;font-size:11px;margin-left:auto">{{ d.host }}</span>
          </span>
        </el-option>
      </el-select>
    </div>

    <!-- 每个选中设备的接口标签行 -->
    <div v-for="devId in selectedDevs" :key="devId" class="iface-row-bar">
      <span class="iface-row-label">{{ getDev(devId)?.name || getDev(devId)?.host }}</span>
      <span class="iface-row-loading" v-if="!devIfaces[devId]">加载中...</span>
      <span class="iface-row-error" v-if="Array.isArray(devIfaces[devId]) && devIfaces[devId].length === 0">
        ⚠ SNMP 不可达
      </span>
      <div v-for="f in (devIfaces[devId] || [])" :key="f.index" class="iface-tag"
        :class="{on: isStreamActive(devId, f.index)}"
        @click="toggleStream(getDev(devId)!, f)">
        <span class="iface-name">{{ f.name }}</span>
        <span class="iface-speed">{{ f.speed_label }}</span>
      </div>
    </div>
    <div class="iface-row-bar" v-if="!selectedDevs.length" style="color:#94a3b8;font-size:11px">
      多选设备 → 点击接口标签开始监控 → 下方卡片对比查看
    </div>

    <!-- 监控卡片网格（等切片下次刷新即有数据） -->
    <div class="monitor-grid" v-if="streams.length">
      <div v-for="s in streams" :key="s.key" class="mon-card">
        <div class="card-head">
          <div class="card-dev-line">
            <span class="card-dev">{{ s.dev?.name || s.dev?.host }}</span>
            <span class="card-arrow">›</span>
            <span class="card-iface">{{ s.iface?.name }}</span>
            <span class="card-close" @click="removeStream(streams.findIndex(x=>x.key===s.key))">✕</span>
          </div>
          <div class="card-speeds">
            <div class="speed-box speed-down">
              <span class="speed-label">▼ 下载</span>
              <span class="speed-val" :style="s.errors>2?{color:'#d1d5db'}:{}">{{ s.errors > 2 ? '—' : (s.rx >= 0 ? s.rx.toFixed(1) : '—') }}</span>
              <span class="speed-unit">Mbps</span>
            </div>
            <div class="speed-box speed-up">
              <span class="speed-label">▲ 上传</span>
              <span class="speed-val" :style="s.errors>2?{color:'#d1d5db'}:{}">{{ s.errors > 2 ? '—' : (s.tx >= 0 ? s.tx.toFixed(1) : '—') }}</span>
              <span class="speed-unit">Mbps</span>
            </div>
            <span v-if="s.errors > 2" style="font-size:10px;color:#ef4444;margin-left:auto">
              ⚠ {{ s.errors }} 次失败
            </span>
            <span v-else-if="s.points.length" style="font-size:10px;color:#94a3b8;margin-left:auto">
              {{ s.points.length }} 点
            </span>
          </div>
        </div>
        <div :id="'chart-' + s.key" class="card-chart"></div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-zone" v-else>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:48px;height:48px;opacity:.2;margin-bottom:12px">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
      <p style="font-size:13px;color:#94a3b8">选择设备 → 点击接口标签开始</p>
      <p style="font-size:11px;color:#94a3b8">每秒采集，显示最近 5 分钟流量趋势</p>
    </div>

    <!-- 添加设备弹窗 -->
    <el-dialog v-model="showAdd" title="添加 RouterOS 设备" width="380px">
      <el-form label-width="50px" size="default">
        <el-form-item label="名称"><el-input v-model="form.name" placeholder="如: Core-R1"/></el-form-item>
        <el-form-item label="IP"><el-input v-model="form.host" placeholder="192.168.88.1"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd=false">取消</el-button>
        <el-button type="primary" @click="saveDev">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
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
  timer: ReturnType<typeof setTimeout> | null
  chart: echarts.ECharts | null
  errors: number  // 连续失败次数
}

/* ── 设备管理 ── */
const devices = ref<Dev[]>([])
const selectedDevs = ref<string[]>([])        // 多选设备 ID
const devIfaces = ref<Record<string, Iface[]>>({})
const form = reactive({ name: '', host: '' })
const showAdd = ref(false)
const loadingDevices = ref(false)

onMounted(() => { loadDevices() })

function getDev(id: string): Dev | undefined {
  return devices.value.find(x => x.id === id)
}

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
  const d = getDev(id)
  if (!d) return
  try {
    const ctrl = new AbortController()
    const timer = setTimeout(() => ctrl.abort(), 12000)
    const r = await fetch(`/api/ros/traffic/interfaces?host=${encodeURIComponent(d.host)}`, { signal: ctrl.signal })
    clearTimeout(timer)
    devIfaces.value[id] = await r.json()
  } catch {
    devIfaces.value[id] = []
    ElMessage.error(`SNMP 超时 (${getDev(id)?.host})`)
  }
}

// 监听多选变化，自动加载接口
watch(selectedDevs, (ids) => {
  ids.forEach(id => {
    if (!devIfaces.value[id]) fetchIfaces(id)
  })
}, { deep: true })

/* ── 多流管理 ── */
const streams = ref<Stream[]>([])
const POLL_INTERVAL = 3000              // 3 秒采集一次（避免 SNMP 超时）
const MAX_POINTS = 100                  // 100 点 × 3s = 5 分钟
const COLORS = ['#6366f1', '#06b6d4']

function isStreamActive(devId: string, ifIndex: number) {
  return streams.value.some(s => s.dev?.id === devId && s.iface?.index === ifIndex)
}

function makeKey(d: Dev, f: Iface) { return `${d.id}_${f.index}` }

function toggleStream(d: Dev, f: Iface) {
  const key = makeKey(d, f)
  const exist = streams.value.findIndex(s => s.key === key)
  if (exist >= 0) {
    // 已存在 → 不删除（用户应该用卡片上的 ✕ 来关闭）
    return
  }
  addStream(d, f)
}

function addStream(d: Dev, f: Iface) {
  const key = makeKey(d, f)
  const stream: Stream = { key, dev: d, iface: f, rx: 0, tx: 0, points: [], timer: null, chart: null, errors: 0 }
  streams.value.push(stream)

  // DOM 渲染 → 等 200ms 确保 CSS Grid 布局完成 → init
  nextTick(() => setTimeout(() => initChart(stream), 200))

  // 注册设备到后台采集器（后端自治轮询，前端只被动读）
  registerWithCollector(d, f)

  // 立即采集，采集完自己调度下一次（递归 setTimeout，不怕后台冻结）
  scheduleNext(stream)
}

async function registerWithCollector(d: Dev, f: Iface) {
  try {
    await fetch(`/api/ros/traffic/collector/register?device_id=${encodeURIComponent(d.id)}&host=${encodeURIComponent(d.host)}&interfaces=${f.index}`)
  } catch { /* 静默失败，采集器可能未启动 */ }
}

function scheduleNext(stream: Stream) {
  const d = stream.dev; const f = stream.iface
  if (!d || !f) return
  // 先采集，完成后再递归调度下一次
  pollSnapshot(stream).finally(() => {
    // 检查流是否还活跃（未被用户关闭）
    if (streams.value.find(s => s.key === stream.key)) {
      stream.timer = setTimeout(() => scheduleNext(stream), POLL_INTERVAL)
    }
  })
}

function removeStream(idx: number) {
  const s = streams.value[idx]
  if (s.timer) clearTimeout(s.timer)
  s.chart?.dispose()
  streams.value.splice(idx, 1)
}

function stopAll() {
  streams.value.forEach(s => {
    if (s.timer) clearTimeout(s.timer)
    s.chart?.dispose()
  })
  streams.value = []
}

// 标签页切回来时立即补采一次
function onVisibilityChange() {
  if (document.visibilityState === 'visible' && streams.value.length) {
    streams.value.forEach(s => {
      if (s.timer) clearTimeout(s.timer)
      scheduleNext(s)
    })
  }
}

/* ── 轮询快照（优先读采集器缓存，后端自治轮询不受前端 Tab 状态影响）── */
async function pollSnapshot(stream: Stream) {
  const d = stream.dev; const f = stream.iface
  if (!d || !f) return
  try {
    // 优先从后台采集器读取缓存（后端自驱，图表永不停）
    let url = `/api/ros/traffic/collector/snapshot?device_id=${encodeURIComponent(d.id)}`
    const ctrl = new AbortController()
    const timer = setTimeout(() => ctrl.abort(), 5000)
    const r = await fetch(url, { signal: ctrl.signal })
    clearTimeout(timer)
    if (!r.ok) { stream.errors++; return }

    const snap = await r.json()
    if (!snap.ok) {
      // 采集器无数据 → 回退到直接 SNMP
      url = `/api/ros/traffic/snapshot?host=${encodeURIComponent(d.host)}&if_index=${f.index}`
      const r2 = await fetch(url)
      const pt = await r2.json()
      pushPoint(stream, pt)
      return
    }

    // 从采集器缓存读取
    const data = snap.data || {}
    const pt = data[f.index + ''] || data[String(f.index)]
    if (pt) pushPoint(stream, pt)
  } catch {
    stream.errors++
  }
}

function pushPoint(stream: Stream, pt: any) {
  if (pt.rx_mbps !== undefined) {
    stream.errors = 0
    stream.rx = pt.rx_mbps; stream.tx = pt.tx_mbps
    stream.points.push({ ts: pt.ts, rx: pt.rx_mbps, tx: pt.tx_mbps })
    if (stream.points.length > MAX_POINTS) {
      stream.points = stream.points.slice(-MAX_POINTS)
    }
    updateChart(stream)
  }
}

/* ── 图表 ── */
function initChart(stream: Stream) {
  const el = document.getElementById('chart-' + stream.key)
  if (!el) return  // DOM 还没到，等下次 updateChart 触发
  if (stream.chart) { stream.chart.resize(); return }
  stream.chart = echarts.init(el)
  updateChart(stream)
}

function updateChart(stream: Stream) {
  if (!stream.chart) { initChart(stream); return }
  const dataRx = stream.points.map(p => [p.ts * 1000, p.rx])
  const dataTx = stream.points.map(p => [p.ts * 1000, p.tx])

  stream.chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,.95)',
      borderColor: '#e2e8f0',
      textStyle: { fontSize: 10, color: '#1e293b' },
    },
    grid: { top: 12, right: 8, bottom: 12, left: 38 },
    xAxis: {
      type: 'time',
      axisLabel: { fontSize: 9, color: '#94a3b8' },
      axisLine: { show: false }, axisTick: { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value', name: 'Mbps',
      nameTextStyle: { fontSize: 9, color: '#94a3b8' },
      axisLabel: { fontSize: 9, color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    series: [
      {
        name: '▼ 下载', type: 'line', data: dataRx,
        smooth: true, symbol: 'circle', symbolSize: 3,
        lineStyle: { color: COLORS[0], width: 1.8 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99,102,241,.12)' },
            { offset: 1, color: 'rgba(99,102,241,0)' },
          ]),
        },
      },
      {
        name: '▲ 上传', type: 'line', data: dataTx,
        smooth: true, symbol: 'circle', symbolSize: 3,
        lineStyle: { color: COLORS[1], width: 1.2, type: 'dashed' },
      },
    ],
  }, true)
}

// 窗口 resize
function handleResize() {
  streams.value.forEach(s => s.chart?.resize())
}
onMounted(() => {
  window.addEventListener('resize', handleResize)
  document.addEventListener('visibilitychange', onVisibilityChange)
})
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
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
  padding: 8px 24px; background: #fff;
  border-bottom: 1px solid #e5e7eb; flex-shrink: 0;
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
  display: flex; align-items: center; gap: 8px; padding: 8px 24px;
  flex-wrap: wrap; border-bottom: 1px solid #e5e7eb;
  background: #fff; flex-shrink: 0; min-height: 44px;
}
.control-sep { width: 1px; height: 18px; background: #e2e8f0; margin: 0 2px; }
.dev-dot-sm { width: 6px; height: 6px; border-radius: 50%; background: #10b981; flex-shrink: 0; }

/* ── 每设备一行接口标签 ── */
.iface-row-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 24px; flex-wrap: wrap;
  border-bottom: 1px solid #f1f5f9; background: #fafbfc;
}
.iface-row-label {
  font-size: 11px; font-weight: 600; color: #64748b;
  min-width: 100px; white-space: nowrap;
}
.iface-row-loading { font-size: 11px; color: #94a3b8; }
.iface-row-error { font-size: 11px; color: #ef4444; }

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

/* ── 卡片网格 ── */
.monitor-grid {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 12px; padding: 12px 24px; align-content: start;
}
.mon-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  display: flex; flex-direction: column;
  min-height: 220px; max-height: 380px; overflow: hidden;
}
.card-head {
  padding: 10px 14px 6px;
  border-bottom: 1px solid #f1f5f9; flex-shrink: 0;
}
.card-dev-line {
  display: flex; align-items: center; gap: 4px;
  font-size: 11px; margin-bottom: 4px;
}
.card-dev { color: #64748b; font-weight: 600; }
.card-arrow { color: #94a3b8; font-size: 10px; }
.card-iface { color: #1e293b; }
.card-close { margin-left: auto; cursor: pointer; font-size: 10px; color: #94a3b8; padding: 2px 4px; }
.card-close:hover { color: #ef4444; }
.card-speeds { display: flex; gap: 16px; align-items: baseline; }
.speed-box { display: flex; align-items: baseline; gap: 4px; }
.speed-label { font-size: 10px; color: #94a3b8; }
.speed-val { font-size: 18px; font-weight: 700; }
.speed-unit { font-size: 10px; color: #94a3b8; margin-left: 2px; }
.speed-down .speed-val { color: #6366f1; }
.speed-up .speed-val { color: #06b6d4; }
.card-chart { flex: 1; min-height: 130px; width: 100%; }

/* ── 空状态 ── */
.empty-zone {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
</style>

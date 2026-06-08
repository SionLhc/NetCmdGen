<template>
  <div class="big-app">
    <!-- 顶栏 -->
    <header class="big-header">
      <div class="big-hd-left">
        <span class="big-logo">📡</span>
        <span class="big-title">NetCmdGen 运维态势大屏</span>
        <span class="big-badge" v-if="snmpStreams.length">{{ snmpStreams.length }} 路流量</span>
      </div>
      <div class="big-hd-right">
        <span class="big-clock">{{ clock }}</span>
        <button class="big-btn" @click="showAddDev=true">+ 添加设备</button>
        <button class="big-btn" @click="showSettings=true" title="配置常驻监控">⚙ 设置</button>
        <button class="big-btn" @click="stopAllSnmp" v-if="snmpStreams.length">⏹ 停止</button>
      </div>
    </header>

    <!-- 统计卡片行 -->
    <div class="big-cards">
      <div class="big-card" v-for="c in statCards" :key="c.label">
        <div class="bc-val" :style="{ color: c.color }">{{ c.value }}</div>
        <div class="bc-label">{{ c.label }}</div>
      </div>
    </div>

    <!-- 主体：双栏布局 -->
    <div class="big-body">
      <!-- 左栏：SNMP 流量监控 — 所有设备一行 -->
      <div class="big-left">
        <div class="big-panel snmp-panel">
          <div class="bp-title">📊 SNMP 实时流量</div>

          <!-- 无设备提示 -->
          <div v-if="!snmpDevices.length" class="snmp-empty">点击"+ 添加设备"添加交换机/路由器</div>

          <!-- 每设备一行接口 -->
          <div v-for="dev in snmpDevices" :key="dev.id" class="dev-row">
            <div class="dev-row-hd">
              <span class="dev-row-dot" :class="{ pinned: isPinnedAny(dev.id) }"></span>
              <span class="dev-row-name">{{ dev.name || dev.host }}</span>
              <span class="dev-row-ip">{{ dev.host }}</span>
              <span v-if="snmpIfaces[dev.id] === undefined" style="font-size:10px;color:#64748b">加载中...</span>
              <span v-if="Array.isArray(snmpIfaces[dev.id]) && !snmpIfaces[dev.id]!.length" style="font-size:10px;color:#ef4444">⚠ SNMP 不可达</span>
            </div>
            <div class="dev-row-tags" v-if="snmpIfaces[dev.id]?.length">
              <span v-for="f in (snmpIfaces[dev.id]||[])" :key="f.index" class="snmp-tag"
                :class="{on: isSnmpActive(dev.id, f.index)}"
                @click="toggleSnmpStream(dev, f)">
                <span class="tag-name">{{ f.name }}</span>
                <span class="tag-speed">{{ f.speed_label }}</span>
                <span v-if="isSnmpActive(dev.id,f.index)&&getStream(dev.id,f.index)" class="tag-live">
                  {{ getStream(dev.id,f.index)!.rx >= 0 ? getStream(dev.id,f.index)!.rx.toFixed(1) : '—' }}
                </span>
              </span>
            </div>
          </div>
        </div>

        <!-- 流量图表网格 -->
        <div class="snmp-charts" v-if="activeStreams.length">
          <div v-for="s in activeStreams" :key="s.key" class="snmp-card">
            <div class="snmp-card-hd">
              <span class="snmp-card-title">{{ s.dev?.name||s.dev?.host }} › {{ s.iface?.name }}</span>
              <span style="font-size:10px;opacity:.6">{{ s.errors>2?'⚠'+s.errors+'次失败':s.points.length+'点' }}</span>
              <span style="cursor:pointer;margin-left:auto;font-size:12px;opacity:.5" @click="removeSnmpStream(s.key)">✕</span>
            </div>
            <div class="snmp-card-body">
              <div class="snmp-card-vals">
                <span class="snmp-val rx">▼ {{ s.rx>=0?s.rx.toFixed(1):'—' }}<em> Mbps</em></span>
                <span class="snmp-val tx">▲ {{ s.tx>=0?s.tx.toFixed(1):'—' }}<em> Mbps</em></span>
              </div>
              <div :id="'snmp-chart-'+s.key" class="snmp-card-chart"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右栏：告警 + 事件 -->
      <div class="big-right">
        <div class="big-panel">
          <div class="bp-title">⚠ 告警分布</div>
          <div ref="alertChartRef" class="bp-chart"></div>
        </div>
        <div class="big-panel">
          <div class="bp-title">📋 实时事件</div>
          <div class="ev-list" v-if="events.length">
            <div v-for="e in events" :key="e.time" class="ev-row">
              <span class="ev-t">{{ e.time }}</span>
              <span class="ev-dot" :class="e.level"></span>
              <span>{{ e.msg }}</span>
            </div>
          </div>
          <div v-else style="font-size:12px;color:#64748b;text-align:center;padding:20px">暂无事件</div>
        </div>
      </div>
    </div>

    <!-- 底部：24h 趋势 -->
    <div class="big-footer-panel">
      <div class="bp-title">📈 24 小时设备在线趋势</div>
      <div ref="trendChartRef" class="bp-chart-trend"></div>
    </div>

    <!-- 添加设备弹窗 -->
    <el-dialog v-model="showAddDev" title="添加 SNMP 设备" width="360px">
      <el-form label-width="50px" size="default">
        <el-form-item label="名称"><el-input v-model="devForm.name" placeholder="Core-R1"/></el-form-item>
        <el-form-item label="IP"><el-input v-model="devForm.host" placeholder="192.168.88.1"/></el-form-item>
        <el-form-item label="提示">
          <span style="font-size:11px;color:#94a3b8">
            RouterOS 需先开启：<code style="background:rgba(255,255,255,.05);padding:2px 6px;border-radius:4px">/snmp set enabled=yes</code>
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDev=false">取消</el-button>
        <el-button type="primary" @click="saveSnmpDev">保存</el-button>
      </template>
    </el-dialog>

    <!-- 设置弹窗：配置常驻监控的接口 -->
    <el-dialog v-model="showSettings" title="⚙ 常驻监控配置" width="640px">
      <div style="font-size:12px;color:#94a3b8;margin-bottom:14px">
        勾选的接口会在每次打开大屏时自动开始监控，无需手动点击。
      </div>
      <div v-if="!snmpDevices.length" style="color:#64748b;text-align:center;padding:20px">暂无设备，请先添加</div>
      <div v-for="dev in snmpDevices" :key="dev.id" style="margin-bottom:12px">
        <div style="font-weight:600;font-size:13px;margin-bottom:6px;color:#e2e8f0">{{ dev.name || dev.host }}</div>
        <div v-if="!snmpIfaces[dev.id]" style="font-size:11px;color:#64748b">加载接口中...</div>
        <div v-else-if="!snmpIfaces[dev.id]!.length" style="font-size:11px;color:#ef4444">⚠ SNMP 不可达</div>
        <el-checkbox-group v-else v-model="pinnedKeys" style="display:flex;flex-wrap:wrap;gap:6px">
          <el-checkbox v-for="f in (snmpIfaces[dev.id]||[])" :key="dev.id+'_'+f.index"
            :label="dev.id+'_'+f.index" border size="small">
            {{ f.name }} ({{ f.speed_label }})
          </el-checkbox>
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="showSettings=false">关闭</el-button>
        <el-button type="primary" @click="savePinned">保存配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

/* ── 时钟 ── */
const clock = ref('')
setInterval(() => { clock.value = new Date().toLocaleString() }, 1000)

/* ── 统计卡片 ── */
const statCards = ref([
  { label: '设备总数', value: 0, color: '#409eff' },
  { label: '在线', value: 0, color: '#67c23a' },
  { label: '离线', value: 0, color: '#f56c6c' },
  { label: '今日告警', value: 0, color: '#e6a23c' },
  { label: '带宽使用', value: '0%', color: '#409eff' },
  { label: '备份完成', value: 0, color: '#67c23a' },
])
const events = ref<any[]>([])
const alertChartRef = ref<HTMLElement | null>(null)
const trendChartRef = ref<HTMLElement | null>(null)

/* ── SNMP 类型 ── */
interface Dev { id:string; name:string; host:string; port:number }
interface Iface { index:number; name:string; speed:number; speed_label:string }
interface SnmpStream {
  key:string; dev:Dev|null; iface:Iface|null; rx:number; tx:number
  points:{ts:number;rx:number;tx:number}[]
  timer:ReturnType<typeof setTimeout>|null; errors:number
  chart:echarts.ECharts|null
}

const snmpDevices = ref<Dev[]>([])
const snmpIfaces = ref<Record<string,Iface[]>>({})
const snmpStreams = ref<SnmpStream[]>([])
const showAddDev = ref(false)
const showSettings = ref(false)
const devForm = reactive({name:'',host:''})

const SNMP_POLL = 3000; const SNMP_MAX = 100
const SNMP_COLORS = ['#6366f1','#06b6d4','#f59e0b','#ef4444','#10b981','#ec4899','#8b5cf6','#14b8a6']

/* ── 常驻配置 (localStorage) ── */
const PINNED_KEY = 'bigscreen_pinned_interfaces'
const pinnedKeys = ref<string[]>([])  // 格式: "devId_ifIndex"

function loadPinned() {
  try { pinnedKeys.value = JSON.parse(localStorage.getItem(PINNED_KEY) || '[]') } catch { pinnedKeys.value = [] }
}
function savePinned() {
  localStorage.setItem(PINNED_KEY, JSON.stringify(pinnedKeys.value))
  ElMessage.success('配置已保存')
  showSettings.value = false
  // 立即应用：启动 pin 的接口，停止未 pin 的
  applyPinned()
}

function isPinnedAny(devId:string): boolean {
  return pinnedKeys.value.some(k => k.startsWith(devId + '_'))
}

/* ── 应用常驻配置 ── */
async function applyPinned() {
  // 停止不在 pin 列表中的流
  const toRemove: string[] = []
  snmpStreams.value.forEach(s => {
    const k = `${s.dev?.id}_${s.iface?.index}`
    if (!pinnedKeys.value.includes(k)) toRemove.push(s.key)
  })
  toRemove.forEach(k => removeSnmpStream(k))

  // 启动 pin 列表中的流
  for (const pk of pinnedKeys.value) {
    const [devId, ifIdxStr] = pk.split('_')
    const ifIdx = parseInt(ifIdxStr)
    if (snmpStreams.value.some(s => s.dev?.id === devId && s.iface?.index === ifIdx)) continue
    const dev = snmpDevices.value.find(d => d.id === devId)
    if (!dev) continue
    // 确保接口列表已加载
    if (!snmpIfaces.value[devId]) await loadIfaces(dev)
    const iface = (snmpIfaces.value[devId] || []).find(f => f.index === ifIdx)
    if (iface) addSnmpStream(dev, iface)
  }
}

/* ── SNMP 操作 ── */
const activeStreams = computed(() => snmpStreams.value)

function isSnmpActive(devId:string, ifIdx:number) { return snmpStreams.value.some(s => s.dev?.id === devId && s.iface?.index === ifIdx) }
function getStream(devId:string, ifIdx:number): SnmpStream|undefined { return snmpStreams.value.find(s => s.dev?.id === devId && s.iface?.index === ifIdx) }
function makeKey(d:Dev,f:Iface){ return `${d.id}_${f.index}` }

async function loadSnmpDevices(){
  try { const r = await fetch('/api/ros/devices'); snmpDevices.value = await r.json() } catch {}
  // 并行加载所有设备的接口
  snmpDevices.value.forEach(d => { if (!snmpIfaces.value[d.id]) loadIfaces(d) })
}

async function loadIfaces(dev:Dev) {
  try {
    const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 12000)
    const r = await fetch(`/api/ros/traffic/interfaces?host=${encodeURIComponent(dev.host)}`, { signal: ctrl.signal })
    snmpIfaces.value[dev.id] = await r.json()
  } catch { snmpIfaces.value[dev.id] = [] }
}

async function saveSnmpDev(){
  if (!devForm.host) { ElMessage.warning('请输入IP'); return }
  await fetch('/api/ros/devices',{method:'PUT',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:devForm.name||devForm.host,host:devForm.host,port:443,username:'admin',password:''})})
  devForm.name = devForm.host = ''; showAddDev.value = false
  await loadSnmpDevices(); ElMessage.success('已保存')
}

function toggleSnmpStream(d:Dev,f:Iface){
  const key = makeKey(d,f)
  const exist = snmpStreams.value.find(s => s.key === key)
  if (exist) {
    // 已经在监控，移除
    if (pinnedKeys.value.includes(`${d.id}_${f.index}`)) {
      // 从 pin 中移除
      pinnedKeys.value = pinnedKeys.value.filter(k => k !== `${d.id}_${f.index}`)
      localStorage.setItem(PINNED_KEY, JSON.stringify(pinnedKeys.value))
    }
    removeSnmpStream(key)
  } else {
    addSnmpStream(d,f)
  }
}

function addSnmpStream(d:Dev,f:Iface){
  const key = makeKey(d,f)
  const s:SnmpStream = { key, dev: d, iface: f, rx: 0, tx: 0, points: [], timer: null, errors: 0, chart: null }
  snmpStreams.value.push(s)
  nextTick(() => setTimeout(() => initChart(s), 300))
  scheduleSnmp(s)
}

function scheduleSnmp(s:SnmpStream){
  pollSnmp(s).finally(() => {
    if (snmpStreams.value.find(x => x.key === s.key))
      s.timer = setTimeout(() => scheduleSnmp(s), SNMP_POLL)
  })
}

async function pollSnmp(s:SnmpStream){
  const d = s.dev; const f = s.iface; if (!d || !f) return
  try {
    const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 5000)
    const r = await fetch(`/api/ros/traffic/snapshot?host=${encodeURIComponent(d.host)}&if_index=${f.index}`, { signal: ctrl.signal })
    if (!r.ok) { s.errors++; return }
    const pt = await r.json()
    if (pt.rx_mbps !== undefined) {
      s.errors = 0; s.rx = pt.rx_mbps; s.tx = pt.tx_mbps
      s.points.push({ ts: pt.ts, rx: pt.rx_mbps, tx: pt.tx_mbps })
      if (s.points.length > SNMP_MAX) s.points = s.points.slice(-SNMP_MAX)
      updateChart(s)
    }
  } catch { s.errors++ }
}

function removeSnmpStream(key:string) {
  const idx = snmpStreams.value.findIndex(s => s.key === key)
  if (idx < 0) return
  const s = snmpStreams.value[idx]
  if (s.timer) clearTimeout(s.timer)
  s.chart?.dispose()
  snmpStreams.value.splice(idx, 1)
}

function stopAllSnmp(){
  snmpStreams.value.forEach(s => { if(s.timer) clearTimeout(s.timer); s.chart?.dispose() })
  snmpStreams.value = []
}

// ── 图表 ──
function initChart(s:SnmpStream) {
  const el = document.getElementById('snmp-chart-' + s.key)
  if (!el) return
  if (s.chart) { s.chart.resize(); return }
  s.chart = echarts.init(el)
}

function updateChart(s:SnmpStream) {
  if (!s.chart) { initChart(s); return }
  const color = SNMP_COLORS[snmpStreams.value.indexOf(s) % SNMP_COLORS.length]
  s.chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15,23,42,.95)',
      borderColor: '#334155',
      textStyle: { fontSize: 10, color: '#e2e8f0' },
    },
    grid: { top: 6, right: 8, bottom: 6, left: 40 },
    xAxis: { type: 'time', show: false },
    yAxis: {
      type: 'value', name: '', axisLabel: { fontSize: 8, color: '#475569' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,.04)' } },
    },
    series: [
      {
        name: '下载', type: 'line',
        data: s.points.map(p => [p.ts * 1000, p.rx]),
        smooth: true, symbol: 'none',
        lineStyle: { color, width: 1.5 },
      },
      {
        name: '上传', type: 'line',
        data: s.points.map(p => [p.ts * 1000, p.tx]),
        smooth: true, symbol: 'none',
        lineStyle: { color, width: 1, type: 'dashed' },
      },
    ],
  }, true)
}

function onVis() {
  if (document.visibilityState === 'visible' && snmpStreams.value.length)
    snmpStreams.value.forEach(s => { if (s.timer) clearTimeout(s.timer); scheduleSnmp(s) })
}

/* ── 大屏概览数据 ── */
async function loadOverview(){
  try {
    const r = await fetch('/api/bigscreen/overview'); const d = await r.json()
    statCards.value = [
      { label: '设备总数', value: d.summary.total_devices, color: '#409eff' },
      { label: '在线', value: d.summary.online_devices, color: '#67c23a' },
      { label: '离线', value: d.summary.offline_devices, color: '#f56c6c' },
      { label: '今日告警', value: d.summary.alerts_today, color: '#e6a23c' },
      { label: '带宽使用', value: d.summary.bandwidth_used + '%', color: '#409eff' },
      { label: '备份完成', value: d.summary.backup_ok, color: '#67c23a' },
    ]
    events.value = d.recent_events || []
    await nextTick()
    if (alertChartRef.value && d.alert_distribution?.length) {
      const c = echarts.init(alertChartRef.value)
      c.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'item', textStyle: { color: '#e2e8f0' } },
        series: [{
          type: 'pie', radius: ['40%', '70%'], center: ['50%', '50%'],
          label: { color: '#94a3b8', fontSize: 10, formatter: '{b}\n{d}%' },
          data: d.alert_distribution,
        }],
      })
    }
    if (trendChartRef.value && d.trend_24h?.length) {
      const c = echarts.init(trendChartRef.value)
      c.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,.95)', borderColor: '#334155', textStyle: { color: '#e2e8f0', fontSize: 10 } },
        grid: { left: 44, right: 16, top: 8, bottom: 24 },
        xAxis: { type: 'category', data: d.trend_24h.map((t: any) => t.time), axisLabel: { fontSize: 9, color: '#64748b' }, axisLine: { show: false }, splitLine: { show: false } },
        yAxis: { type: 'value', axisLabel: { fontSize: 9, color: '#64748b' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,.05)' } } },
        series: [
          { name: '在线', type: 'line', data: d.trend_24h.map((t: any) => t.online), smooth: true, areaStyle: { color: 'rgba(103,194,58,.12)' }, lineStyle: { color: '#67c23a' }, itemStyle: { color: '#67c23a' } },
          { name: '离线', type: 'line', data: d.trend_24h.map((t: any) => t.offline), smooth: true, areaStyle: { color: 'rgba(245,108,108,.1)' }, lineStyle: { color: '#f56c6c' }, itemStyle: { color: '#f56c6c' } },
        ],
      })
    }
  } catch {}
}

onMounted(async () => {
  loadPinned()
  await Promise.all([loadOverview(), loadSnmpDevices()])
  // 等设备+接口加载后应用常驻配置
  await nextTick()
  await applyPinned()
  document.addEventListener('visibilitychange', onVis)
  window.addEventListener('resize', () => {
    snmpStreams.value.forEach(s => {
      try { s.chart?.resize() } catch {}
    })
  })
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', onVis)
  snmpStreams.value.forEach(s => { if (s.timer) clearTimeout(s.timer); s.chart?.dispose() })
})
</script>

<style scoped>
.big-app { background: linear-gradient(160deg, #0a0f1e 0%, #0f172a 40%, #1a1030 100%); min-height: 100vh; padding: 16px 20px 20px; color: #e2e8f0; display: flex; flex-direction: column; gap: 14px; }
.big-header { display: flex; justify-content: space-between; align-items: center; }
.big-hd-left { display: flex; align-items: center; gap: 12px; }
.big-logo { font-size: 22px; } .big-title { font-size: 20px; font-weight: 700; }
.big-badge { font-size: 11px; background: rgba(99,102,241,.2); color: #a5b4fc; padding: 2px 10px; border-radius: 10px; }
.big-hd-right { display: flex; align-items: center; gap: 12px; }
.big-clock { font-size: 13px; color: #94a3b8; font-family: monospace; }
.big-btn { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); color: #c8d2e0; padding: 5px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; transition: .15s; }
.big-btn:hover { background: rgba(255,255,255,.12); }

.big-cards { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; }
.big-card { background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.06); border-radius: 10px; padding: 14px 16px; text-align: center; }
.bc-val { font-size: 28px; font-weight: 700; } .bc-label { font-size: 11px; color: #64748b; margin-top: 4px; }

.big-body { display: grid; grid-template-columns: 1fr 360px; gap: 14px; flex: 1; min-height: 0; }
.big-left { min-width: 0; display: flex; flex-direction: column; gap: 14px; }
.big-right { display: flex; flex-direction: column; gap: 14px; }

.big-panel { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06); border-radius: 12px; padding: 14px; }
.bp-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; color: #c8d2e0; }
.bp-chart { width: 100%; height: 220px; }
.bp-chart-trend { width: 100%; height: 180px; }
.big-footer-panel { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06); border-radius: 12px; padding: 14px; }

/* ── SNMP 设备行 ── */
.snmp-panel { flex-shrink: 0; }
.dev-row {
  padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,.04);
  display: flex; flex-direction: column; gap: 4px;
}
.dev-row-hd { display: flex; align-items: center; gap: 8px; }
.dev-row-dot { width: 6px; height: 6px; border-radius: 50%; background: #475569; flex-shrink: 0; }
.dev-row-dot.pinned { background: #6366f1; box-shadow: 0 0 6px #6366f1; }
.dev-row-name { font-weight: 600; font-size: 13px; color: #c8d2e0; }
.dev-row-ip { font-size: 11px; color: #64748b; font-family: monospace; }
.dev-row-tags { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; padding-left: 14px; }

.snmp-tag {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px; border-radius: 12px; font-size: 11px; cursor: pointer;
  background: rgba(255,255,255,.05); color: #94a3b8;
  border: 1px solid rgba(255,255,255,.08); transition: .15s; white-space: nowrap;
}
.snmp-tag:hover { background: rgba(255,255,255,.12); }
.snmp-tag.on { background: #6366f1; color: #fff; border-color: #6366f1; }
.tag-name { font-weight: 500; }
.tag-speed { font-size: 10px; opacity: .6; }
.tag-live { font-size: 10px; background: rgba(0,0,0,.2); padding: 1px 4px; border-radius: 4px; font-family: monospace; }
.snmp-empty { text-align: center; padding: 24px; color: #64748b; font-size: 13px; }

/* ── 图表卡片网格 ── */
.snmp-charts { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 10px; }
.snmp-card {
  background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06);
  border-radius: 10px; padding: 10px 12px; display: flex; flex-direction: column;
}
.snmp-card-hd { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #94a3b8; margin-bottom: 6px; }
.snmp-card-title { font-weight: 600; color: #c8d2e0; }
.snmp-card-body { flex: 1; display: flex; flex-direction: column; min-height: 140px; }
.snmp-card-vals { display: flex; gap: 16px; margin-bottom: 4px; }
.snmp-val { font-size: 14px; font-weight: 700; }
.snmp-val.rx { color: #22d3ee; }
.snmp-val.tx { color: #a78bfa; }
.snmp-val em { font-size: 10px; font-weight: 400; opacity: .6; }
.snmp-card-chart { flex: 1; min-height: 100px; width: 100%; }

.ev-list { max-height: 220px; overflow-y: auto; font-size: 12px; }
.ev-row { display: flex; align-items: center; gap: 8px; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,.04); }
.ev-t { color: #475569; font-family: monospace; font-size: 10px; min-width: 36px; }
.ev-dot { width: 5px; height: 5px; border-radius: 50%; }
.ev-dot.err { background: #f56c6c; } .ev-dot.warn { background: #e6a23c; } .ev-dot.info { background: #409eff; }
</style>

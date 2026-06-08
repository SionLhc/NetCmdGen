<template>
  <div class="big-app">
    <!-- 顶栏 -->
    <header class="big-header">
      <div class="big-hd-left">
        <span class="big-logo">📡</span>
        <span class="big-title">NetCmdGen 运维态势大屏</span>
        <span class="big-badge" v-if="snmpStreams.length">{{ snmpStreams.length }} 路</span>
      </div>
      <div class="big-hd-right">
        <span class="big-clock">{{ clock }}</span>
        <button class="big-btn" @click="showAddDev=true">+ 添加设备</button>
        <button class="big-btn" @click="showSettings=true">⚙ 设置</button>
        <button class="big-btn" @click="stopAllSnmp" v-if="snmpStreams.length">⏹ 全部停止</button>
      </div>
    </header>

    <!-- 统计卡片 -->
    <div class="big-cards">
      <div class="big-card" v-for="c in statCards" :key="c.label">
        <div class="bc-val" :style="{ color: c.color }">{{ c.value }}</div>
        <div class="bc-label">{{ c.label }}</div>
      </div>
    </div>

    <!-- 主体三栏 -->
    <div class="big-body">
      <!-- 左栏：设备树 (可折叠) -->
      <div class="big-left">
        <div class="big-panel dev-panel">
          <div class="bp-title" style="display:flex;justify-content:space-between;align-items:center">
            🔌 设备接口
            <el-button link size="small" @click="expandAll">{{ allExpanded ? '全部折叠' : '全部展开' }}</el-button>
          </div>
          <div class="dev-scroll">
            <div v-if="!snmpDevices.length" class="snmp-empty">点击 <b>+ 添加设备</b></div>
            <!-- 设备折叠面板 -->
            <div v-for="dev in snmpDevices" :key="dev.id" class="dev-fold">
              <!-- 设备头部 -->
              <div class="dev-fold-hd" @click="toggleDev(dev.id)">
                <span class="dev-fold-arrow">{{ expandedDevs.has(dev.id) ? '▼' : '▶' }}</span>
                <span class="dev-fold-dot" :class="{pinned:devHasPinned(dev.id)}"></span>
                <span class="dev-fold-name">{{ dev.name || dev.host }}</span>
                <span style="font-size:10px;color:#64748b;margin-left:auto;font-family:monospace">{{ dev.host }}</span>
                <span v-if="devActiveCount(dev.id)" style="font-size:10px;background:rgba(99,102,241,.15);color:#a5b4fc;padding:1px 6px;border-radius:8px;margin-left:4px">
                  {{ devActiveCount(dev.id) }} 路
                </span>
              </div>
              <!-- 接口标签 -->
              <div class="dev-fold-body" v-show="expandedDevs.has(dev.id)">
                <div v-if="snmpIfaces[dev.id] === undefined" style="font-size:10px;color:#64748b;padding:4px 0">加载中...</div>
                <div v-else-if="!snmpIfaces[dev.id]!.length" style="font-size:10px;color:#ef4444;padding:4px 0">⚠ 不可达</div>
                <div v-else class="dev-tags">
                  <span v-for="f in (snmpIfaces[dev.id]||[])" :key="f.index" class="snmp-tag"
                    :class="{on: isSnmpActive(dev.id,f.index)}"
                    @click="toggleSnmpStream(dev,f)">
                    {{ f.name }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中栏：统一 SNMP 流量图 -->
      <div class="big-mid">
        <div class="big-panel chart-panel" v-show="snmpStreams.length">
          <div class="bp-title">
            📊 实时流量
            <span style="font-weight:400;font-size:10px;color:#64748b;margin-left:8px">{{ activeStreamLabels.length }} 条曲线</span>
          </div>
          <div ref="unifiedChartRef" class="unified-chart"></div>
        </div>
        <div v-if="!snmpStreams.length" class="big-panel chart-panel" style="display:flex;align-items:center;justify-content:center;color:#64748b;font-size:13px">
          <div style="text-align:center">
            <div style="font-size:48px;opacity:.15;margin-bottom:8px">📊</div>
            左侧展开设备 → 点击接口标签开始监控
          </div>
        </div>

        <!-- 24h 趋势 -->
        <div class="big-panel">
          <div class="bp-title">📈 24 小时设备在线趋势</div>
          <div ref="trendChartRef" class="bp-chart-trend"></div>
        </div>
      </div>

      <!-- 右栏：告警 + 事件 + 活跃接口速览 -->
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
        <!-- 活跃接口实时速率 -->
        <div class="big-panel" v-if="snmpStreams.length">
          <div class="bp-title">💹 实时速率</div>
          <div class="rate-list">
            <div v-for="s in snmpStreams" :key="s.key" class="rate-row">
              <div class="rate-dev">{{ s.dev?.name || s.dev?.host }} / {{ s.iface?.name }}</div>
              <div class="rate-vals">
                <span class="rv rx">▼ {{ s.rx>=0?s.rx.toFixed(1):'—' }}</span>
                <span class="rv tx">▲ {{ s.tx>=0?s.tx.toFixed(1):'—' }}</span>
                <span v-if="s.errors>2" style="color:#ef4444;font-size:9px">⚠</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加设备弹窗 -->
    <el-dialog v-model="showAddDev" title="添加 SNMP 设备" width="360px">
      <el-form label-width="50px" size="default">
        <el-form-item label="名称"><el-input v-model="devForm.name" placeholder="Core-R1"/></el-form-item>
        <el-form-item label="IP"><el-input v-model="devForm.host" placeholder="192.168.88.1"/></el-form-item>
        <el-form-item label="提示">
          <span style="font-size:11px;color:#94a3b8">
            RouterOS: <code style="background:rgba(255,255,255,.05);padding:2px 6px;border-radius:4px">/snmp set enabled=yes</code>
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDev=false">取消</el-button>
        <el-button type="primary" @click="saveSnmpDev">保存</el-button>
      </template>
    </el-dialog>

    <!-- 设置弹窗 -->
    <el-dialog v-model="showSettings" title="⚙ 常驻监控配置" width="620px">
      <div style="font-size:12px;color:#94a3b8;margin-bottom:12px">
        勾选的接口在每次打开大屏时自动启动监控。建议只勾选关键接口，避免界面混乱。
      </div>
      <div v-if="!snmpDevices.length" style="text-align:center;color:#64748b;padding:20px">暂无设备</div>
      <div v-for="dev in snmpDevices" :key="dev.id" style="margin-bottom:10px;background:rgba(255,255,255,.02);border-radius:8px;padding:10px 12px">
        <div style="font-weight:600;font-size:13px;margin-bottom:6px;color:#c8d2e0">
          {{ dev.name || dev.host }}
          <span style="font-size:10px;color:#64748b;margin-left:6px">{{ dev.host }}</span>
        </div>
        <div v-if="!snmpIfaces[dev.id]" style="font-size:10px;color:#64748b">加载中...</div>
        <div v-else-if="!snmpIfaces[dev.id]!.length" style="font-size:10px;color:#ef4444">⚠ 不可达</div>
        <el-checkbox-group v-else v-model="pinnedKeys" style="display:flex;flex-wrap:wrap;gap:6px">
          <el-checkbox v-for="f in (snmpIfaces[dev.id]||[])" :key="dev.id+'_'+f.index"
            :label="dev.id+'_'+f.index" border size="small">
            {{ f.name }} <span style="font-size:10px;color:#64748b">({{ f.speed_label }})</span>
          </el-checkbox>
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="showSettings=false">取消</el-button>
        <el-button type="primary" @click="savePinned">保存配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
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
const unifiedChartRef = ref<HTMLElement | null>(null)

/* ── 设备树折叠 ── */
const expandedDevs = ref(new Set<string>())
const allExpanded = computed(() => expandedDevs.value.size === snmpDevices.value.length && snmpDevices.value.length > 0)

function toggleDev(id: string) {
  if (expandedDevs.value.has(id)) expandedDevs.value.delete(id)
  else expandedDevs.value.add(id)
  // 展开时加载接口
  if (expandedDevs.value.has(id) && !snmpIfaces.value[id]) {
    const dev = snmpDevices.value.find(d => d.id === id)
    if (dev) loadIfaces(dev)
  }
}
function expandAll() {
  if (allExpanded.value) {
    expandedDevs.value = new Set()
  } else {
    expandedDevs.value = new Set(snmpDevices.value.map(d => d.id))
    snmpDevices.value.forEach(d => {
      if (!snmpIfaces.value[d.id]) loadIfaces(d)
    })
  }
}
function devActiveCount(devId: string) {
  return snmpStreams.value.filter(s => s.dev?.id === devId).length
}
function devHasPinned(devId: string) {
  return pinnedKeys.value.some(k => k.startsWith(devId + '_'))
}

/* ── SNMP 类型 ── */
interface Dev { id:string; name:string; host:string; port:number }
interface Iface { index:number; name:string; speed:number; speed_label:string }
interface SnmpStream {
  key:string; dev:Dev|null; iface:Iface|null; rx:number; tx:number
  points:{ts:number;rx:number;tx:number}[]
  timer:ReturnType<typeof setTimeout>|null; errors:number
}

const snmpDevices = ref<Dev[]>([])
const snmpIfaces = ref<Record<string,Iface[]>>({})
const snmpStreams = ref<SnmpStream[]>([])
const showAddDev = ref(false)
const showSettings = ref(false)
const devForm = reactive({name:'',host:''})

const SNMP_POLL = 3000; const SNMP_MAX = 100
const SNMP_COLORS = ['#6366f1','#06b6d4','#f59e0b','#10b981','#ef4444','#ec4899','#8b5cf6','#14b8a6','#e11d48','#3b82f6']

/* ── 统一图表 ── */
let unifiedChart: echarts.ECharts|null = null
const activeStreamLabels = computed(() => snmpStreams.value.map(s => `${s.dev?.name||s.dev?.host}/${s.iface?.name}`))

function renderUnifiedChart() {
  if (!unifiedChartRef.value) return
  if (!unifiedChart) unifiedChart = echarts.init(unifiedChartRef.value)

  const series: any[] = []
  const legendData: string[] = []
  snmpStreams.value.forEach((s, i) => {
    const c = SNMP_COLORS[i % SNMP_COLORS.length]
    const label = `${s.dev?.name||s.dev?.host}/${s.iface?.name}`
    legendData.push(label + ' ▼')
    legendData.push(label + ' ▲')
    series.push({
      name: label + ' ▼', type: 'line',
      data: s.points.map(p => [p.ts * 1000, p.rx]),
      smooth: true, symbol: 'none',
      lineStyle: { color: c, width: 1.5 },
    })
    series.push({
      name: label + ' ▲', type: 'line',
      data: s.points.map(p => [p.ts * 1000, p.tx]),
      smooth: true, symbol: 'none',
      lineStyle: { color: c, width: 1, type: 'dashed' },
    })
  })

  unifiedChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15,23,42,.95)',
      borderColor: '#334155',
      textStyle: { fontSize: 10, color: '#e2e8f0' },
    },
    legend: {
      bottom: 0, textStyle: { color: '#94a3b8', fontSize: 9 },
      type: 'scroll', orient: 'horizontal',
      selected: Object.fromEntries(legendData.map(n => [n, true])),
    },
    grid: { top: 10, right: 16, bottom: 30, left: 50 },
    xAxis: {
      type: 'time',
      axisLabel: { fontSize: 9, color: '#475569', formatter: (v: any) => new Date(v).toLocaleTimeString() },
      axisLine: { show: false }, splitLine: { show: false },
    },
    yAxis: {
      type: 'value', name: 'Mbps',
      nameTextStyle: { fontSize: 9, color: '#64748b' },
      axisLabel: { fontSize: 9, color: '#475569' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,.04)' } },
    },
    series,
  }, true)
}

/* ── 常驻配置 ── */
const PINNED_KEY = 'bigscreen_pinned_interfaces'
const pinnedKeys = ref<string[]>([])
function loadPinned() { try { pinnedKeys.value = JSON.parse(localStorage.getItem(PINNED_KEY)||'[]') } catch { pinnedKeys.value = [] } }
function savePinned() {
  localStorage.setItem(PINNED_KEY, JSON.stringify(pinnedKeys.value))
  ElMessage.success('配置已保存')
  showSettings.value = false
  applyPinned()
}

async function applyPinned() {
  // 停止不在 pin 中的
  const toRemove = snmpStreams.value.filter(s => !pinnedKeys.value.includes(`${s.dev?.id}_${s.iface?.index}`))
  toRemove.forEach(s => removeSnmpStream(s.key))
  // 启动 pin 中的
  for (const pk of pinnedKeys.value) {
    const [devId, idxStr] = pk.split('_')
    const ifIdx = parseInt(idxStr)
    if (snmpStreams.value.some(s => s.dev?.id===devId && s.iface?.index===ifIdx)) continue
    const dev = snmpDevices.value.find(d=>d.id===devId)
    if (!dev) continue
    if (!snmpIfaces.value[devId]) await loadIfaces(dev)
    const iface = (snmpIfaces.value[devId]||[]).find(f=>f.index===ifIdx)
    if (iface) addSnmpStream(dev, iface)
  }
}

/* ── SNMP 操作 ── */
function isSnmpActive(devId:string,ifIdx:number) { return snmpStreams.value.some(s=>s.dev?.id===devId&&s.iface?.index===ifIdx) }
function makeKey(d:Dev,f:Iface) { return `${d.id}_${f.index}` }

async function loadSnmpDevices() {
  try { const r = await fetch('/api/ros/devices'); snmpDevices.value = await r.json() } catch {}
}

async function loadIfaces(dev:Dev) {
  try {
    const ctrl = new AbortController(); setTimeout(()=>ctrl.abort(), 12000)
    const r = await fetch(`/api/ros/traffic/interfaces?host=${encodeURIComponent(dev.host)}`, {signal:ctrl.signal})
    snmpIfaces.value[dev.id] = await r.json()
  } catch { snmpIfaces.value[dev.id] = [] }
}

async function saveSnmpDev() {
  if (!devForm.host) { ElMessage.warning('请输入IP'); return }
  await fetch('/api/ros/devices',{method:'PUT',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:devForm.name||devForm.host,host:devForm.host,port:443,username:'admin',password:''})})
  devForm.name=devForm.host=''; showAddDev.value=false
  await loadSnmpDevices(); ElMessage.success('已保存')
}

function toggleSnmpStream(d:Dev,f:Iface) {
  const key = makeKey(d,f)
  const exist = snmpStreams.value.find(s=>s.key===key)
  if (exist) {
    removeSnmpStream(key)
    // 从 pin 移除
    pinnedKeys.value = pinnedKeys.value.filter(k=>k!==`${d.id}_${f.index}`)
    localStorage.setItem(PINNED_KEY, JSON.stringify(pinnedKeys.value))
  } else {
    addSnmpStream(d,f)
  }
}

function addSnmpStream(d:Dev,f:Iface) {
  const key = makeKey(d,f)
  const s:SnmpStream = { key,dev:d,iface:f,rx:0,tx:0,points:[],timer:null,errors:0 }
  snmpStreams.value.push(s)
  scheduleSnmp(s)
  nextTick(() => renderUnifiedChart())
}

function scheduleSnmp(s:SnmpStream) {
  pollSnmp(s).finally(() => {
    if (snmpStreams.value.find(x=>x.key===s.key))
      s.timer = setTimeout(()=>scheduleSnmp(s), SNMP_POLL)
  })
}

async function pollSnmp(s:SnmpStream) {
  const d=s.dev;const f=s.iface;if(!d||!f)return
  try {
    const ctrl=new AbortController();setTimeout(()=>ctrl.abort(),5000)
    const r=await fetch(`/api/ros/traffic/snapshot?host=${encodeURIComponent(d.host)}&if_index=${f.index}`,{signal:ctrl.signal})
    if(!r.ok){s.errors++;return}
    const pt=await r.json()
    if(pt.rx_mbps!==undefined){s.errors=0;s.rx=pt.rx_mbps;s.tx=pt.tx_mbps
    s.points.push({ts:pt.ts,rx:pt.rx_mbps,tx:pt.tx_mbps})
    if(s.points.length>SNMP_MAX)s.points=s.points.slice(-SNMP_MAX)
    renderUnifiedChart()}
  }catch{s.errors++}
}

function removeSnmpStream(key:string) {
  const idx=snmpStreams.value.findIndex(s=>s.key===key)
  if(idx<0)return
  const s=snmpStreams.value[idx]
  if(s.timer)clearTimeout(s.timer)
  snmpStreams.value.splice(idx,1)
  renderUnifiedChart()
}

function stopAllSnmp() {
  snmpStreams.value.forEach(s=>{if(s.timer)clearTimeout(s.timer)})
  snmpStreams.value=[]
  renderUnifiedChart()
}

function onVis() {
  if(document.visibilityState==='visible'&&snmpStreams.value.length)
    snmpStreams.value.forEach(s=>{if(s.timer)clearTimeout(s.timer);scheduleSnmp(s)})
}

/* ── 概览数据 ── */
async function loadOverview() {
  try {
    const r=await fetch('/api/bigscreen/overview');const d=await r.json()
    statCards.value=[
      {label:'设备总数',value:d.summary.total_devices,color:'#409eff'},
      {label:'在线',value:d.summary.online_devices,color:'#67c23a'},
      {label:'离线',value:d.summary.offline_devices,color:'#f56c6c'},
      {label:'今日告警',value:d.summary.alerts_today,color:'#e6a23c'},
      {label:'带宽使用',value:d.summary.bandwidth_used+'%',color:'#409eff'},
      {label:'备份完成',value:d.summary.backup_ok,color:'#67c23a'},
    ]
    events.value = d.recent_events||[]
    await nextTick()
    if(alertChartRef.value&&d.alert_distribution?.length) {
      const c=echarts.init(alertChartRef.value)
      c.setOption({backgroundColor:'transparent',tooltip:{trigger:'item',textStyle:{color:'#e2e8f0'}},
        series:[{type:'pie',radius:['40%','70%'],label:{color:'#94a3b8',fontSize:10,formatter:'{b}\n{d}%'},data:d.alert_distribution}]})
    }
    if(trendChartRef.value&&d.trend_24h?.length) {
      const c=echarts.init(trendChartRef.value)
      c.setOption({backgroundColor:'transparent',
        tooltip:{trigger:'axis',backgroundColor:'rgba(15,23,42,.95)',borderColor:'#334155',textStyle:{color:'#e2e8f0',fontSize:10}},
        grid:{left:44,right:16,top:8,bottom:24},
        xAxis:{type:'category',data:d.trend_24h.map((t:any)=>t.time),axisLabel:{fontSize:9,color:'#64748b'},axisLine:{show:false},splitLine:{show:false}},
        yAxis:{type:'value',axisLabel:{fontSize:9,color:'#64748b'},splitLine:{lineStyle:{color:'rgba(255,255,255,.05)'}}},
        series:[
          {name:'在线',type:'line',data:d.trend_24h.map((t:any)=>t.online),smooth:true,areaStyle:{color:'rgba(103,194,58,.12)'},lineStyle:{color:'#67c23a'},itemStyle:{color:'#67c23a'}},
          {name:'离线',type:'line',data:d.trend_24h.map((t:any)=>t.offline),smooth:true,areaStyle:{color:'rgba(245,108,108,.1)'},lineStyle:{color:'#f56c6c'},itemStyle:{color:'#f56c6c'}},
        ]})
    }
  }catch{}
}

onMounted(async () => {
  loadPinned()
  await Promise.all([loadOverview(), loadSnmpDevices()])
  await nextTick(); await applyPinned()
  document.addEventListener('visibilitychange',onVis)
  window.addEventListener('resize',() => { try { unifiedChart?.resize() } catch {} })
})
onUnmounted(() => {
  document.removeEventListener('visibilitychange',onVis)
  snmpStreams.value.forEach(s=>{if(s.timer)clearTimeout(s.timer)})
  unifiedChart?.dispose()
})
</script>

<style scoped>
/* ── 全局 ── */
.big-app { background: linear-gradient(160deg,#0a0f1e 0%,#0f172a 40%,#1a1030 100%); min-height: 100vh; padding: 14px 18px 18px; color: #e2e8f0; display: flex; flex-direction: column; gap: 10px; }
.big-header { display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
.big-hd-left { display: flex; align-items: center; gap: 10px; }
.big-logo { font-size: 20px; } .big-title { font-size: 18px; font-weight: 700; }
.big-badge { font-size: 10px; background: rgba(99,102,241,.2); color: #a5b4fc; padding: 1px 8px; border-radius: 10px; }
.big-hd-right { display: flex; align-items: center; gap: 10px; }
.big-clock { font-size: 12px; color: #94a3b8; font-family: monospace; }
.big-btn { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); color: #c8d2e0; padding: 4px 10px; border-radius: 6px; font-size: 11px; cursor: pointer; transition: .15s; }
.big-btn:hover { background: rgba(255,255,255,.12); }

/* ── 统计卡片 ── */
.big-cards { display: grid; grid-template-columns: repeat(6,1fr); gap: 8px; flex-shrink: 0; }
.big-card { background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.06); border-radius: 8px; padding: 10px 14px; text-align: center; }
.bc-val { font-size: 24px; font-weight: 700; } .bc-label { font-size: 10px; color: #64748b; margin-top: 2px; }

/* ── 三栏主体 ── */
.big-body { display: grid; grid-template-columns: 280px 1fr 280px; gap: 10px; flex: 1; min-height: 0; }
.big-left { display: flex; flex-direction: column; min-height: 0; }
.big-mid { display: flex; flex-direction: column; gap: 10px; min-width: 0; min-height: 0; }
.big-right { display: flex; flex-direction: column; gap: 10px; min-height: 0; }

/* ── 面板 ── */
.big-panel { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06); border-radius: 10px; padding: 12px; }
.bp-title { font-size: 12px; font-weight: 600; margin-bottom: 8px; color: #c8d2e0; }
.bp-chart { width: 100%; height: 160px; }
.bp-chart-trend { width: 100%; height: 140px; }
.chart-panel { flex: 1; display: flex; flex-direction: column; min-height: 0; }

/* ── 设备树 ── */
.dev-panel { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.dev-scroll { flex: 1; overflow-y: auto; font-size: 12px; }
.dev-scroll::-webkit-scrollbar { width: 4px; }
.dev-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,.08); border-radius: 2px; }
.snmp-empty { text-align: center; padding: 20px; color: #64748b; font-size: 12px; }

.dev-fold { border-bottom: 1px solid rgba(255,255,255,.04); }
.dev-fold-hd {
  display: flex; align-items: center; gap: 6px; padding: 7px 4px;
  cursor: pointer; transition: .1s; user-select: none;
}
.dev-fold-hd:hover { background: rgba(255,255,255,.03); }
.dev-fold-arrow { font-size: 9px; color: #475569; width: 12px; }
.dev-fold-dot { width: 5px; height: 5px; border-radius: 50%; background: #475569; flex-shrink: 0; }
.dev-fold-dot.pinned { background: #6366f1; box-shadow: 0 0 6px #6366f1; }
.dev-fold-name { font-weight: 600; font-size: 12px; color: #c8d2e0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.dev-fold-body { padding: 2px 0 6px 22px; }
.dev-tags { display: flex; flex-wrap: wrap; gap: 4px; }

.snmp-tag {
  display: inline-block; padding: 2px 9px; border-radius: 10px; font-size: 10px;
  cursor: pointer; background: rgba(255,255,255,.05); color: #94a3b8;
  border: 1px solid rgba(255,255,255,.08); transition: .12s; white-space: nowrap;
}
.snmp-tag:hover { background: rgba(255,255,255,.1); color: #c8d2e0; }
.snmp-tag.on { background: #6366f1; color: #fff; border-color: #6366f1; }

/* ── 统一图表 ── */
.unified-chart { flex: 1; min-height: 250px; width: 100%; }

/* ── 事件 ── */
.ev-list { max-height: 140px; overflow-y: auto; font-size: 11px; }
.ev-row { display: flex; align-items: center; gap: 6px; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,.04); }
.ev-t { color: #475569; font-family: monospace; font-size: 9px; min-width: 32px; }
.ev-dot { width: 4px; height: 4px; border-radius: 50%; }
.ev-dot.err { background: #f56c6c; } .ev-dot.warn { background: #e6a23c; } .ev-dot.info { background: #409eff; }

/* ── 实时速率 ── */
.rate-list { max-height: 260px; overflow-y: auto; font-size: 11px; }
.rate-list::-webkit-scrollbar { width: 4px; }
.rate-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,.06); border-radius: 2px; }
.rate-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,.03); }
.rate-dev { color: #94a3b8; font-size: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 110px; }
.rate-vals { display: flex; gap: 8px; flex-shrink: 0; }
.rv { font-size: 11px; font-family: monospace; font-weight: 600; }
.rv.rx { color: #22d3ee; } .rv.tx { color: #a78bfa; }
</style>

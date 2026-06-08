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
      <!-- 左栏：设备树 -->
      <div class="big-left">
        <div class="big-panel dev-panel">
          <div class="bp-title" style="display:flex;justify-content:space-between;align-items:center">
            🔌 设备 / 接口
            <el-button link size="small" @click="expandAll">{{ allExpanded ? '全部折叠' : '全部展开' }}</el-button>
          </div>
          <div class="dev-scroll">
            <div v-if="!snmpDevices.length" class="snmp-empty">点击 <b>+ 添加设备</b></div>
            <div v-for="dev in snmpDevices" :key="dev.id" class="dev-fold">
              <div class="dev-fold-hd" @click="toggleDev(dev.id)">
                <span class="dev-fold-arrow">{{ expandedDevs.has(dev.id) ? '▼' : '▶' }}</span>
                <span class="dev-fold-dot" :class="{pinned:devHasPinned(dev.id)}"></span>
                <span class="dev-fold-name">{{ dev.name || dev.host }}</span>
                <span v-if="devActiveCount(dev.id)" class="dev-fold-count">{{ devActiveCount(dev.id) }} 路</span>
              </div>
              <div class="dev-fold-body" v-show="expandedDevs.has(dev.id)">
                <div v-if="snmpIfaces[dev.id] === undefined" style="font-size:10px;color:#64748b">加载中...</div>
                <div v-else-if="!snmpIfaces[dev.id]!.length" style="font-size:10px;color:#ef4444">⚠ 不可达</div>
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

      <!-- 中栏：独立接口卡片网格 + 底部24h趋势 -->
      <div class="big-mid">
        <!-- 卡片网格 -->
        <div class="card-grid" v-if="snmpStreams.length">
          <div v-for="s in snmpStreams" :key="s.key" class="if-card">
            <div class="if-card-hd">
              <span class="if-card-name">{{ s.dev?.name||s.dev?.host }} / {{ s.iface?.name }}</span>
              <span v-if="s.errors>2" class="if-card-err">⚠ {{ s.errors }}次</span>
              <span v-else class="if-card-pts">{{ s.points.length }}点</span>
              <span class="if-card-close" @click.stop="removeSnmpStream(s.key)">✕</span>
            </div>
            <div class="if-card-vals">
              <span class="if-val rx">▼ {{ s.rx>=0?s.rx.toFixed(1):'—' }}<em>Mbps</em></span>
              <span class="if-val tx">▲ {{ s.tx>=0?s.tx.toFixed(1):'—' }}<em>Mbps</em></span>
            </div>
            <div :id="'chart-'+s.key" class="if-card-chart"></div>
          </div>
        </div>
        <div v-else class="card-empty">
          <div class="card-empty-icon">📊</div>
          左侧展开设备 → 点击接口标签
        </div>

        <!-- 24h 趋势 -->
        <div class="big-panel" style="flex-shrink:0">
          <div class="bp-title">📈 24 小时设备在线趋势</div>
          <div ref="trendChartRef" class="bp-chart-trend"></div>
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
        勾选的接口在每次打开大屏时自动启动监控。
      </div>
      <div v-if="!snmpDevices.length" style="text-align:center;color:#64748b;padding:20px">暂无设备</div>
      <div v-for="dev in snmpDevices" :key="dev.id" style="margin-bottom:10px;background:rgba(255,255,255,.02);border-radius:8px;padding:10px 12px">
        <div style="font-weight:600;font-size:13px;margin-bottom:6px;color:#c8d2e0">
          {{ dev.name || dev.host }} <span style="font-size:10px;color:#64748b">{{ dev.host }}</span>
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

/* ── 设备树 ── */
const expandedDevs = ref(new Set<string>())
const allExpanded = computed(() => expandedDevs.value.size === snmpDevices.value.length && snmpDevices.value.length > 0)
function toggleDev(id: string) {
  if (expandedDevs.value.has(id)) expandedDevs.value.delete(id)
  else {
    expandedDevs.value.add(id)
    const dev = snmpDevices.value.find(d => d.id === id)
    if (dev && !snmpIfaces.value[id]) loadIfaces(dev)
  }
}
function expandAll() {
  if (allExpanded.value) { expandedDevs.value = new Set() }
  else {
    expandedDevs.value = new Set(snmpDevices.value.map(d => d.id))
    snmpDevices.value.forEach(d => { if (!snmpIfaces.value[d.id]) loadIfaces(d) })
  }
}
function devActiveCount(devId: string) { return snmpStreams.value.filter(s => s.dev?.id === devId).length }
function devHasPinned(devId: string) { return pinnedKeys.value.some(k => k.startsWith(devId + '_')) }

/* ── SNMP ── */
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

// 设置弹窗打开时，主动加载所有设备接口
watch(showSettings, (v) => {
  if (v) snmpDevices.value.forEach(d => { if (!snmpIfaces.value[d.id]) loadIfaces(d) })
})
const devForm = reactive({name:'',host:''})
const SNMP_POLL = 3000; const SNMP_MAX = 100
const C = ['#6366f1','#06b6d4','#f59e0b','#10b981','#ef4444','#ec4899','#8b5cf6','#14b8a6']

/* ── 常驻配置 ── */
const PINNED_KEY = 'bigscreen_pinned_interfaces'
const pinnedKeys = ref<string[]>([])
function loadPinned() { try { pinnedKeys.value = JSON.parse(localStorage.getItem(PINNED_KEY)||'[]') } catch { pinnedKeys.value = [] } }
function savePinned() {
  localStorage.setItem(PINNED_KEY, JSON.stringify(pinnedKeys.value))
  ElMessage.success('配置已保存'); showSettings.value = false
  applyPinned()
}

async function applyPinned() {
  const toRemove = snmpStreams.value.filter(s => !pinnedKeys.value.includes(`${s.dev?.id}_${s.iface?.index}`))
  toRemove.forEach(s => removeSnmpStream(s.key))
  for (const pk of pinnedKeys.value) {
    const [devId, idxStr] = pk.split('_'); const ifIdx = parseInt(idxStr)
    if (snmpStreams.value.some(s => s.dev?.id===devId && s.iface?.index===ifIdx)) continue
    const dev = snmpDevices.value.find(d=>d.id===devId); if (!dev) continue
    if (!snmpIfaces.value[devId]) await loadIfaces(dev)
    const iface = (snmpIfaces.value[devId]||[]).find(f=>f.index===ifIdx)
    if (iface) addSnmpStream(dev, iface)
  }
}

/* ── 操作 ── */
function isSnmpActive(devId:string,ifIdx:number) { return snmpStreams.value.some(s=>s.dev?.id===devId&&s.iface?.index===ifIdx) }
function makeKey(d:Dev,f:Iface) { return `${d.id}_${f.index}` }

async function loadSnmpDevices() { try { const r=await fetch('/api/ros/devices'); snmpDevices.value = await r.json() } catch {} }
async function loadIfaces(dev:Dev) {
  try { const ctrl=new AbortController();setTimeout(()=>ctrl.abort(),12000);const r=await fetch(`/api/ros/traffic/interfaces?host=${encodeURIComponent(dev.host)}`,{signal:ctrl.signal});snmpIfaces.value[dev.id]=await r.json() } catch { snmpIfaces.value[dev.id]=[] }
}
async function saveSnmpDev() {
  if(!devForm.host){ElMessage.warning('请输入IP');return}
  await fetch('/api/ros/devices',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:devForm.name||devForm.host,host:devForm.host,port:443,username:'admin',password:''})})
  devForm.name=devForm.host='';showAddDev.value=false;await loadSnmpDevices();ElMessage.success('已保存')
}

function toggleSnmpStream(d:Dev,f:Iface) {
  const key=makeKey(d,f); const exist=snmpStreams.value.find(s=>s.key===key)
  if(exist) { pinnedKeys.value=pinnedKeys.value.filter(k=>k!==`${d.id}_${f.index}`);localStorage.setItem(PINNED_KEY,JSON.stringify(pinnedKeys.value));removeSnmpStream(key) }
  else addSnmpStream(d,f)
}
function addSnmpStream(d:Dev,f:Iface) {
  const key=makeKey(d,f)
  const s:SnmpStream={key,dev:d,iface:f,rx:0,tx:0,points:[],timer:null,errors:0,chart:null}
  snmpStreams.value.push(s)
  nextTick(() => setTimeout(() => initChart(s), 200))
  scheduleSnmp(s)
}
function scheduleSnmp(s:SnmpStream) {
  pollSnmp(s).finally(() => { if(snmpStreams.value.find(x=>x.key===s.key)) s.timer=setTimeout(()=>scheduleSnmp(s), SNMP_POLL) })
}
async function pollSnmp(s:SnmpStream) {
  const d=s.dev;const f=s.iface;if(!d||!f)return
  try { const ctrl=new AbortController();setTimeout(()=>ctrl.abort(),5000);const r=await fetch(`/api/ros/traffic/snapshot?host=${encodeURIComponent(d.host)}&if_index=${f.index}`,{signal:ctrl.signal});if(!r.ok){s.errors++;return};const pt=await r.json();if(pt.rx_mbps!==undefined){s.errors=0;s.rx=pt.rx_mbps;s.tx=pt.tx_mbps;s.points.push({ts:pt.ts,rx:pt.rx_mbps,tx:pt.tx_mbps});if(s.points.length>SNMP_MAX)s.points=s.points.slice(-SNMP_MAX);updateChart(s)} } catch { s.errors++ }
}
function removeSnmpStream(key:string) { const idx=snmpStreams.value.findIndex(s=>s.key===key);if(idx<0)return;const s=snmpStreams.value[idx];if(s.timer)clearTimeout(s.timer);s.chart?.dispose();snmpStreams.value.splice(idx,1) }
function stopAllSnmp() { snmpStreams.value.forEach(s=>{if(s.timer)clearTimeout(s.timer);s.chart?.dispose()});snmpStreams.value=[] }

/* ── 独立图表 ── */
function initChart(s:SnmpStream) {
  const el=document.getElementById('chart-'+s.key);if(!el)return
  if(s.chart){s.chart.resize();return}
  s.chart=echarts.init(el)
}
function updateChart(s:SnmpStream) {
  if(!s.chart){initChart(s);return}
  const idx=snmpStreams.value.indexOf(s)
  const color=C[idx % C.length]
  s.chart.setOption({
    backgroundColor:'transparent',
    tooltip:{trigger:'axis',backgroundColor:'rgba(15,23,42,.95)',borderColor:'#334155',textStyle:{fontSize:9,color:'#e2e8f0'}},
    grid:{top:4,right:4,bottom:4,left:36},
    xAxis:{type:'time',show:false},
    yAxis:{type:'value',axisLabel:{fontSize:7,color:'#475569'},splitLine:{lineStyle:{color:'rgba(255,255,255,.04)'}}},
    series:[
      {name:'▼',type:'line',data:s.points.map(p=>[p.ts*1000,p.rx]),smooth:true,symbol:'none',lineStyle:{color,width:1.5}},
      {name:'▲',type:'line',data:s.points.map(p=>[p.ts*1000,p.tx]),smooth:true,symbol:'none',lineStyle:{color,width:1,type:'dashed'}},
    ],
  },true)
}

function onVis() { if(document.visibilityState==='visible'&&snmpStreams.value.length) snmpStreams.value.forEach(s=>{if(s.timer)clearTimeout(s.timer);scheduleSnmp(s)}) }

/* ── 概览 ── */
async function loadOverview() {
  try {
    const r=await fetch('/api/bigscreen/overview');const d=await r.json()
    statCards.value=[{label:'设备总数',value:d.summary.total_devices,color:'#409eff'},{label:'在线',value:d.summary.online_devices,color:'#67c23a'},{label:'离线',value:d.summary.offline_devices,color:'#f56c6c'},{label:'今日告警',value:d.summary.alerts_today,color:'#e6a23c'},{label:'带宽使用',value:d.summary.bandwidth_used+'%',color:'#409eff'},{label:'备份完成',value:d.summary.backup_ok,color:'#67c23a'}]
    events.value=d.recent_events||[]
    await nextTick()
    if(alertChartRef.value&&d.alert_distribution?.length){const c=echarts.init(alertChartRef.value);c.setOption({backgroundColor:'transparent',tooltip:{trigger:'item',textStyle:{color:'#e2e8f0'}},series:[{type:'pie',radius:['40%','70%'],label:{color:'#94a3b8',fontSize:10,formatter:'{b}\n{d}%'},data:d.alert_distribution}]})}
    if(trendChartRef.value&&d.trend_24h?.length){const c=echarts.init(trendChartRef.value);c.setOption({backgroundColor:'transparent',tooltip:{trigger:'axis',backgroundColor:'rgba(15,23,42,.95)',borderColor:'#334155',textStyle:{color:'#e2e8f0',fontSize:10}},grid:{left:44,right:16,top:8,bottom:24},xAxis:{type:'category',data:d.trend_24h.map((t:any)=>t.time),axisLabel:{fontSize:9,color:'#64748b'},axisLine:{show:false},splitLine:{show:false}},yAxis:{type:'value',axisLabel:{fontSize:9,color:'#64748b'},splitLine:{lineStyle:{color:'rgba(255,255,255,.05)'}}},series:[{name:'在线',type:'line',data:d.trend_24h.map((t:any)=>t.online),smooth:true,areaStyle:{color:'rgba(103,194,58,.12)'},lineStyle:{color:'#67c23a'},itemStyle:{color:'#67c23a'}},{name:'离线',type:'line',data:d.trend_24h.map((t:any)=>t.offline),smooth:true,areaStyle:{color:'rgba(245,108,108,.1)'},lineStyle:{color:'#f56c6c'},itemStyle:{color:'#f56c6c'}}]})}
  }catch{}
}

onMounted(async()=>{loadPinned();await Promise.all([loadOverview(),loadSnmpDevices()]);await nextTick();await applyPinned();document.addEventListener('visibilitychange',onVis);window.addEventListener('resize',()=>{snmpStreams.value.forEach(s=>{try{s.chart?.resize()}catch{}})})})
onUnmounted(()=>{document.removeEventListener('visibilitychange',onVis);snmpStreams.value.forEach(s=>{if(s.timer)clearTimeout(s.timer);s.chart?.dispose()})})
</script>

<style scoped>
.big-app{background:linear-gradient(160deg,#0a0f1e 0%,#0f172a 40%,#1a1030 100%);min-height:100vh;padding:14px 18px 18px;color:#e2e8f0;display:flex;flex-direction:column;gap:10px}
.big-header{display:flex;justify-content:space-between;align-items:center;flex-shrink:0}
.big-hd-left{display:flex;align-items:center;gap:10px}.big-logo{font-size:20px}.big-title{font-size:18px;font-weight:700}
.big-badge{font-size:10px;background:rgba(99,102,241,.2);color:#a5b4fc;padding:1px 8px;border-radius:10px}
.big-hd-right{display:flex;align-items:center;gap:10px}.big-clock{font-size:12px;color:#94a3b8;font-family:monospace}
.big-btn{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);color:#c8d2e0;padding:4px 10px;border-radius:6px;font-size:11px;cursor:pointer;transition:.15s}
.big-btn:hover{background:rgba(255,255,255,.12)}

.big-cards{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;flex-shrink:0}
.big-card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:10px 14px;text-align:center}
.bc-val{font-size:24px;font-weight:700}.bc-label{font-size:10px;color:#64748b;margin-top:2px}

.big-body{display:grid;grid-template-columns:260px 1fr 260px;gap:10px;flex:1;min-height:0}
.big-left{display:flex;flex-direction:column;min-height:0}
.big-mid{display:flex;flex-direction:column;gap:10px;min-width:0;min-height:0;overflow:hidden}
.big-right{display:flex;flex-direction:column;gap:10px;min-height:0}

.big-panel{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:12px}
.bp-title{font-size:12px;font-weight:600;margin-bottom:8px;color:#c8d2e0}
.bp-chart{width:100%;height:160px}.bp-chart-trend{width:100%;height:130px}

/* 设备树 */
.dev-panel{flex:1;display:flex;flex-direction:column;min-height:0}
.dev-scroll{flex:1;overflow-y:auto;font-size:12px}
.dev-scroll::-webkit-scrollbar{width:4px}
.dev-scroll::-webkit-scrollbar-thumb{background:rgba(255,255,255,.08);border-radius:2px}
.snmp-empty{text-align:center;padding:20px;color:#64748b;font-size:12px}
.dev-fold{border-bottom:1px solid rgba(255,255,255,.04)}
.dev-fold-hd{display:flex;align-items:center;gap:6px;padding:6px 4px;cursor:pointer;transition:.1s;user-select:none}
.dev-fold-hd:hover{background:rgba(255,255,255,.03)}
.dev-fold-arrow{font-size:9px;color:#475569;width:12px}
.dev-fold-dot{width:5px;height:5px;border-radius:50%;background:#475569;flex-shrink:0}
.dev-fold-dot.pinned{background:#6366f1;box-shadow:0 0 6px #6366f1}
.dev-fold-name{font-weight:600;font-size:12px;color:#c8d2e0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dev-fold-count{font-size:9px;background:rgba(99,102,241,.15);color:#a5b4fc;padding:1px 6px;border-radius:8px;margin-left:4px;flex-shrink:0}
.dev-fold-body{padding:2px 0 6px 22px}
.dev-tags{display:flex;flex-wrap:wrap;gap:4px}
.snmp-tag{display:inline-block;padding:2px 9px;border-radius:10px;font-size:10px;cursor:pointer;background:rgba(255,255,255,.05);color:#94a3b8;border:1px solid rgba(255,255,255,.08);transition:.12s;white-space:nowrap}
.snmp-tag:hover{background:rgba(255,255,255,.1);color:#c8d2e0}
.snmp-tag.on{background:#6366f1;color:#fff;border-color:#6366f1}

/* 卡片网格 — 可滚动 */
.card-grid{flex:1;overflow-y:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px;align-content:start;padding-right:2px}
.card-grid::-webkit-scrollbar{width:4px}
.card-grid::-webkit-scrollbar-thumb{background:rgba(255,255,255,.08);border-radius:2px}
.card-empty{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#64748b;font-size:13px;gap:8px}
.card-empty-icon{font-size:40px;opacity:.12}

/* 单张接口卡片 */
.if-card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:6px 8px;display:flex;flex-direction:column}
.if-card-hd{display:flex;align-items:center;gap:4px;font-size:10px;color:#94a3b8;margin-bottom:3px}
.if-card-name{font-weight:600;color:#c8d2e0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:120px}
.if-card-err{font-size:8px;color:#ef4444;flex-shrink:0}.if-card-pts{font-size:8px;color:#475569;flex-shrink:0}
.if-card-close{margin-left:auto;cursor:pointer;font-size:10px;opacity:.4;transition:.15s}
.if-card-close:hover{opacity:.8;color:#ef4444}
.if-card-vals{display:flex;gap:10px;margin-bottom:3px}
.if-val{font-size:11px;font-weight:700}
.if-val.rx{color:#22d3ee}.if-val.tx{color:#a78bfa}
.if-val em{font-size:8px;font-weight:400;opacity:.5;margin-left:1px}
.if-card-chart{height:90px;width:100%}

/* 事件 */
.ev-list{max-height:140px;overflow-y:auto;font-size:11px}.ev-row{display:flex;align-items:center;gap:6px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04)}.ev-t{color:#475569;font-family:monospace;font-size:9px;min-width:32px}.ev-dot{width:4px;height:4px;border-radius:50%}.ev-dot.err{background:#f56c6c}.ev-dot.warn{background:#e6a23c}.ev-dot.info{background:#409eff}
</style>

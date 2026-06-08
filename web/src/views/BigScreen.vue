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
      <!-- 左栏：SNMP 流量监控 -->
      <div class="big-left">
        <div class="big-panel snmp-panel">
          <div class="bp-title">📊 SNMP 实时流量</div>
          <!-- 设备选择 + 接口标签 -->
          <div class="snmp-ctl">
            <el-select v-model="snmpDev" placeholder="选择设备" size="small" style="width:180px" @change="onSnmpDev">
              <el-option v-for="d in snmpDevices" :key="d.id" :label="d.name||d.host" :value="d.id" />
            </el-select>
            <span v-if="snmpDev && snmpIfaces[snmpDev]" class="snmp-ctl-sep"></span>
            <span v-for="f in (snmpIfaces[snmpDev]||[])" :key="f.index" class="snmp-tag"
              :class="{on: isSnmpActive(snmpDev, f.index)}"
              @click="toggleSnmpStream(snmpDevices.find((x:any)=>x.id===snmpDev)!, f)">
              {{ f.name }}
            </span>
            <span v-if="!snmpDev" style="font-size:11px;opacity:.5">选设备后点接口标签</span>
          </div>
          <!-- 流量图表 -->
          <div ref="snmpChartRef" class="snmp-chart" v-show="snmpStreams.length"></div>
          <div v-if="!snmpStreams.length" class="snmp-empty">选择设备后添加接口即可监控</div>
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
      </el-form>
      <template #footer>
        <el-button @click="showAddDev=false">取消</el-button>
        <el-button type="primary" @click="saveSnmpDev">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
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

/* ── SNMP 流量监控（从 RosConsole 移植） ── */
interface Dev { id:string; name:string; host:string; port:number }
interface Iface { index:number; name:string; speed:number; speed_label:string }
interface SnmpStream {
  key:string; dev:Dev|null; iface:Iface|null; rx:number; tx:number
  points:{ts:number;rx:number;tx:number}[]
  timer:ReturnType<typeof setTimeout>|null; errors:number
}

const snmpDevices = ref<Dev[]>([])
const snmpDev = ref('')
const snmpIfaces = ref<Record<string,Iface[]>>({})
const snmpStreams = ref<SnmpStream[]>([])
const snmpChartRef = ref<HTMLElement|null>(null)
let snmpChart: echarts.ECharts|null = null
const SNMP_POLL = 3000; const SNMP_MAX = 100
const SNMP_COLORS = ['#6366f1','#06b6d4']
const showAddDev = ref(false)
const devForm = reactive({name:'',host:''})

function isSnmpActive(devId:string, ifIdx:number){ return snmpStreams.value.some(s=>s.dev?.id===devId&&s.iface?.index===ifIdx) }
function makeKey(d:Dev,f:Iface){ return `${d.id}_${f.index}` }

async function loadSnmpDevices(){
  try{const r=await fetch('/api/ros/devices');snmpDevices.value=await r.json()}catch{}
}
async function saveSnmpDev(){
  if(!devForm.host){ElMessage.warning('请输入IP');return}
  await fetch('/api/ros/devices',{method:'PUT',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:devForm.name||devForm.host,host:devForm.host,port:443,username:'admin',password:''})})
  devForm.name=devForm.host=''; showAddDev.value=false; await loadSnmpDevices(); ElMessage.success('已保存')
}
async function onSnmpDev(id:string){
  if(!id||snmpIfaces.value[id])return
  const d=snmpDevices.value.find(x=>x.id===id)
  if(!d)return
  try{
    const ctrl=new AbortController();setTimeout(()=>ctrl.abort(),12000)
    const r=await fetch(`/api/ros/traffic/interfaces?host=${encodeURIComponent(d.host)}`,{signal:ctrl.signal})
    snmpIfaces.value[id]=await r.json()
  }catch{snmpIfaces.value[id]=[]}
}

function toggleSnmpStream(d:Dev,f:Iface){
  const key=makeKey(d,f)
  if(snmpStreams.value.find(s=>s.key===key)) return  // already active
  addSnmpStream(d,f)
}
function addSnmpStream(d:Dev,f:Iface){
  const key=makeKey(d,f)
  const s:SnmpStream={key,dev:d,iface:f,rx:0,tx:0,points:[],timer:null,errors:0}
  snmpStreams.value.push(s)
  renderSnmpChart()
  scheduleSnmp(s)
}
function scheduleSnmp(s:SnmpStream){
  pollSnmp(s).finally(()=>{
    if(snmpStreams.value.find(x=>x.key===s.key))
      s.timer=setTimeout(()=>scheduleSnmp(s),SNMP_POLL)
  })
}
async function pollSnmp(s:SnmpStream){
  const d=s.dev;const f=s.iface;if(!d||!f)return
  try{
    const ctrl=new AbortController();setTimeout(()=>ctrl.abort(),5000)
    const r=await fetch(`/api/ros/traffic/snapshot?host=${encodeURIComponent(d.host)}&if_index=${f.index}`,{signal:ctrl.signal})
    if(!r.ok){s.errors++;return}
    const pt=await r.json()
    if(pt.rx_mbps!==undefined){s.errors=0;s.rx=pt.rx_mbps;s.tx=pt.tx_mbps;s.points.push({ts:pt.ts,rx:pt.rx_mbps,tx:pt.tx_mbps})
    if(s.points.length>SNMP_MAX)s.points=s.points.slice(-SNMP_MAX);renderSnmpChart()}
  }catch{s.errors++}
}
function stopAllSnmp(){
  snmpStreams.value.forEach(s=>{if(s.timer)clearTimeout(s.timer)})
  snmpStreams.value=[]
  renderSnmpChart()
}
function renderSnmpChart(){
  if(!snmpChartRef.value)return
  if(!snmpChart){snmpChart=echarts.init(snmpChartRef.value)}
  const series:any[]=[]
  snmpStreams.value.forEach((s,i)=>{
    const label=`${s.dev?.name||s.dev?.host}/${s.iface?.name}`
    series.push({name:label+' ▼',type:'line',data:s.points.map(p=>[p.ts*1000,p.rx]),smooth:true,symbol:'none',lineStyle:{color:SNMP_COLORS[i%2],width:2}})
    series.push({name:label+' ▲',type:'line',data:s.points.map(p=>[p.ts*1000,p.tx]),smooth:true,symbol:'none',lineStyle:{color:SNMP_COLORS[i%2],width:1,type:'dashed'}})
  })
  snmpChart.setOption({
    backgroundColor:'transparent',
    tooltip:{trigger:'axis',backgroundColor:'rgba(15,23,42,.95)',borderColor:'#334155',textStyle:{fontSize:10,color:'#e2e8f0'}},
    legend:{bottom:0,textStyle:{color:'#94a3b8',fontSize:9},type:'scroll'},
    grid:{top:12,right:12,bottom:32,left:44},
    xAxis:{type:'time',axisLabel:{fontSize:9,color:'#64748b'},axisLine:{show:false},splitLine:{show:false}},
    yAxis:{type:'value',name:'Mbps',nameTextStyle:{fontSize:9,color:'#64748b'},axisLabel:{fontSize:9,color:'#64748b'},splitLine:{lineStyle:{color:'rgba(255,255,255,.05)'}}},
    series
  },true)
}

/* ── 可见性恢复 ── */
function onVis(){ if(document.visibilityState==='visible'&&snmpStreams.value.length){ snmpStreams.value.forEach(s=>{if(s.timer)clearTimeout(s.timer);scheduleSnmp(s)}) } }

/* ── 大屏概览数据 ── */
async function loadOverview(){
  try{
    const r=await fetch('/api/bigscreen/overview');const d=await r.json()
    statCards.value=[
      {label:'设备总数',value:d.summary.total_devices,color:'#409eff'},
      {label:'在线',value:d.summary.online_devices,color:'#67c23a'},
      {label:'离线',value:d.summary.offline_devices,color:'#f56c6c'},
      {label:'今日告警',value:d.summary.alerts_today,color:'#e6a23c'},
      {label:'带宽使用',value:d.summary.bandwidth_used+'%',color:'#409eff'},
      {label:'备份完成',value:d.summary.backup_ok,color:'#67c23a'},
    ]
    events.value=d.recent_events||[]
    await nextTick()
    // 告警饼图
    if(alertChartRef.value&&d.alert_distribution?.length){
      const c=echarts.init(alertChartRef.value)
      c.setOption({backgroundColor:'transparent',tooltip:{trigger:'item',textStyle:{color:'#e2e8f0'}},series:[{type:'pie',radius:['40%','70%'],center:['50%','50%'],label:{color:'#94a3b8',fontSize:10,formatter:'{b}\n{d}%'},data:d.alert_distribution}]})
    }
    // 24h趋势
    if(trendChartRef.value&&d.trend_24h?.length){
      const c=echarts.init(trendChartRef.value)
      c.setOption({backgroundColor:'transparent',tooltip:{trigger:'axis',backgroundColor:'rgba(15,23,42,.95)',borderColor:'#334155',textStyle:{color:'#e2e8f0',fontSize:10}},grid:{left:44,right:16,top:8,bottom:24},xAxis:{type:'category',data:d.trend_24h.map((t:any)=>t.time),axisLabel:{fontSize:9,color:'#64748b'},axisLine:{show:false},splitLine:{show:false}},yAxis:{type:'value',axisLabel:{fontSize:9,color:'#64748b'},splitLine:{lineStyle:{color:'rgba(255,255,255,.05)'}}},series:[{name:'在线',type:'line',data:d.trend_24h.map((t:any)=>t.online),smooth:true,areaStyle:{color:'rgba(103,194,58,.12)'},lineStyle:{color:'#67c23a'},itemStyle:{color:'#67c23a'}},{name:'离线',type:'line',data:d.trend_24h.map((t:any)=>t.offline),smooth:true,areaStyle:{color:'rgba(245,108,108,.1)'},lineStyle:{color:'#f56c6c'},itemStyle:{color:'#f56c6c'}}]})
    }
  }catch{}
}

onMounted(()=>{
  loadOverview(); loadSnmpDevices()
  document.addEventListener('visibilitychange',onVis)
  window.addEventListener('resize',()=>{snmpChart?.resize()})
})
onUnmounted(()=>{
  document.removeEventListener('visibilitychange',onVis)
  snmpStreams.value.forEach(s=>{if(s.timer)clearTimeout(s.timer)})
})
</script>

<style scoped>
.big-app{background:linear-gradient(160deg,#0a0f1e 0%,#0f172a 40%,#1a1030 100%);min-height:100vh;padding:16px 20px 20px;color:#e2e8f0;display:flex;flex-direction:column;gap:14px}
.big-header{display:flex;justify-content:space-between;align-items:center}
.big-hd-left{display:flex;align-items:center;gap:12px}
.big-logo{font-size:22px}.big-title{font-size:20px;font-weight:700}
.big-badge{font-size:11px;background:rgba(99,102,241,.2);color:#a5b4fc;padding:2px 10px;border-radius:10px}
.big-hd-right{display:flex;align-items:center;gap:12px}
.big-clock{font-size:13px;color:#94a3b8;font-family:monospace}
.big-btn{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);color:#c8d2e0;padding:5px 12px;border-radius:6px;font-size:12px;cursor:pointer;transition:.15s}
.big-btn:hover{background:rgba(255,255,255,.12)}

.big-cards{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}
.big-card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:14px 16px;text-align:center}
.bc-val{font-size:28px;font-weight:700}.bc-label{font-size:11px;color:#64748b;margin-top:4px}

.big-body{display:grid;grid-template-columns:1fr 360px;gap:14px;flex:1;min-height:0}
.big-left{min-width:0}
.big-right{display:flex;flex-direction:column;gap:14px}

.big-panel{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:14px}
.bp-title{font-size:13px;font-weight:600;margin-bottom:8px;color:#c8d2e0}
.bp-chart{width:100%;height:220px}
.bp-chart-trend{width:100%;height:180px}
.big-footer-panel{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:14px}

/* SNMP 控制条 */
.snmp-panel{display:flex;flex-direction:column;flex:1;min-height:0}
.snmp-ctl{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:6px 0;margin-bottom:8px}
.snmp-ctl-sep{width:1px;height:14px;background:rgba(255,255,255,.1);margin:0 2px}
.snmp-tag{padding:2px 8px;border-radius:10px;font-size:10px;cursor:pointer;background:rgba(255,255,255,.05);color:#94a3b8;border:1px solid rgba(255,255,255,.08);transition:.15s;white-space:nowrap}
.snmp-tag:hover{background:rgba(255,255,255,.1)}
.snmp-tag.on{background:#6366f1;color:#fff;border-color:#6366f1}
.snmp-chart{flex:1;min-height:200px;width:100%}
.snmp-empty{flex:1;display:flex;align-items:center;justify-content:center;font-size:13px;color:#64748b}

.ev-list{max-height:220px;overflow-y:auto;font-size:12px}.ev-row{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.04)}.ev-t{color:#475569;font-family:monospace;font-size:10px;min-width:36px}.ev-dot{width:5px;height:5px;border-radius:50%}.ev-dot.err{background:#f56c6c}.ev-dot.warn{background:#e6a23c}.ev-dot.info{background:#409eff}
</style>

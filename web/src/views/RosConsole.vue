<template>
  <div class="monitor-page">
    <!-- 顶栏控制区 -->
    <div class="top-bar">
      <div class="bar-left">
        <el-select v-model="deviceId" placeholder="选择设备" size="default" style="width:200px" @change="onDeviceChange">
          <el-option v-for="d in devices" :key="d.id" :label="d.name||d.host" :value="d.id"/>
        </el-select>
        <el-select v-model="ifIndex" placeholder="接口" size="default" style="width:160px" :disabled="!deviceId" @change="restartMon">
          <el-option v-for="f in interfaces" :key="f.index" :label="f.name" :value="f.index"/>
        </el-select>
        <div class="btn-group">
          <button class="ctrl-btn play" @click="restartMon" :disabled="!ifIndex">▶ 开始</button>
          <button class="ctrl-btn stop" @click="stopMon">⏹ 停止</button>
        </div>
      </div>
      <div class="bar-center" v-if="monitoring">
        <span class="live-dot"></span>
        <span class="live-text">实时监控中</span>
        <span class="live-count">{{ points.length }} 点</span>
      </div>
      <div class="bar-right">
        <el-button size="default" @click="showAdd=true">+ 设备</el-button>
        <span style="font-size:11px;color:#94a3b8">需路由器启用 SNMP: /snmp set enabled=yes; /snmp community add name=public</span>
      </div>
    </div>

    <!-- 即时速率卡片 -->
    <div class="stat-cards" v-if="monitoring">
      <div class="stat-card rx">
        <div class="stat-icon">▼</div>
        <div class="stat-body">
          <div class="stat-label">下载速率</div>
          <div class="stat-value">{{ currentRx }}</div>
          <div class="stat-unit">Mbps</div>
        </div>
      </div>
      <div class="stat-card tx">
        <div class="stat-icon">▲</div>
        <div class="stat-body">
          <div class="stat-label">上传速率</div>
          <div class="stat-value">{{ currentTx }}</div>
          <div class="stat-unit">Mbps</div>
        </div>
      </div>
      <div class="stat-card info">
        <div class="stat-body">
          <div class="stat-label">设备</div>
          <div class="stat-value-sm">{{ currentDevice?.host }}</div>
        </div>
      </div>
      <div class="stat-card info">
        <div class="stat-body">
          <div class="stat-label">接口</div>
          <div class="stat-value-sm">{{ currentIfaceName }}</div>
        </div>
      </div>
    </div>

    <!-- 图表区：常驻 -->
    <div class="chart-area">
      <div ref="chartRef" class="chart-box"></div>
      <div v-if="!monitoring && !deviceId" class="chart-hint">
        <p>添加 RouterOS 设备并选择接口开始监控</p>
      </div>
      <div v-else-if="!monitoring" class="chart-hint">
        <p>选择接口后点击「开始」监测实时流量</p>
      </div>
    </div>

    <!-- 添加设备对话框 -->
    <el-dialog v-model="showAdd" title="添加设备" width="360px">
      <el-form label-width="60px" size="default">
        <el-form-item label="名称"><el-input v-model="form.name" placeholder="Core-R1"/></el-form-item>
        <el-form-item label="IP"><el-input v-model="form.host" placeholder="192.168.88.1"/></el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="form.port" :min="1" :max="65535"/>
          <span style="font-size:11px;color:#909399;margin-left:8px">WebFig端口</span>
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
import { ref, reactive, onMounted, nextTick, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'

/* ── 设备管理 ── */
interface Dev { id: string; name: string; host: string; port: number }
const devices = ref<Dev[]>([])
const deviceId = ref('')
const currentDevice = computed(() => devices.value.find(d => d.id === deviceId.value))

const form = reactive({ name: '', host: '', port: 443 })
const showAdd = ref(false)

onMounted(loadDevices)

async function loadDevices() {
  try { const r = await fetch('/api/ros/devices'); devices.value = await r.json() } catch {}
}

async function saveDev() {
  if (!form.host) { ElMessage.warning('请输入IP'); return }
  await fetch('/api/ros/devices',{method:'PUT',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:form.name,host:form.host,port:form.port,username:'admin',password:''})})
  form.name = form.host = ''; showAdd.value = false
  await loadDevices(); ElMessage.success('已保存')
}

/* ── 接口列表 ── */
interface Iface { index: number; name: string; speed: number; speed_label: string }
const interfaces = ref<Iface[]>([])
const ifIndex = ref(0)
const currentIfaceName = computed(() =>
  interfaces.value.find(f => f.index === ifIndex.value)?.name || '')

async function onDeviceChange() {
  stopMon()
  interfaces.value = []
  ifIndex.value = 0
  if (!deviceId.value) return
  const d = currentDevice.value!
  try {
    const r = await fetch(`/api/ros/traffic/interfaces?host=${encodeURIComponent(d.host)}`)
    interfaces.value = await r.json()
    if (interfaces.value.length) ifIndex.value = interfaces.value[0].index
  } catch { ElMessage.error('获取接口失败') }
}

/* ── 流量监控 ── */
const monitoring = ref(false)
const currentRx = ref(0)
const currentTx = ref(0)
const points = ref<{ts:number; rx:number; tx:number}[]>([])
const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
let abortCtrl: AbortController | null = null

watch(() => points.value.length, () => { nextTick(renderChart) })

function renderChart() {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const data = [...points.value]
  const ts = data.map((d:any) => new Date(d.ts*1000).toLocaleTimeString())
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['下载', '上传'], bottom: 0, textStyle: { fontSize: 11 } },
    grid: { top: 12, right: 16, bottom: 32, left: 50 },
    xAxis: { type: 'category', data: ts, axisLabel: { fontSize: 10, color: '#94a3b8' } },
    yAxis: { type: 'value', name: 'Mbps', nameTextStyle: { fontSize: 10, color: '#94a3b8' },
      axisLabel: { fontSize: 10, color: '#94a3b8' }, splitLine: { lineStyle: { color: '#f1f5f9' } } },
    series: [
      { name: '下载', type: 'line', data: data.map(d=>d.rx), smooth: true, symbol: 'none',
        lineStyle: { color: '#6366f1', width: 2 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,
          [{offset:0,color:'rgba(99,102,241,.18)'},{offset:1,color:'rgba(99,102,241,0)'}]) } },
      { name: '上传', type: 'line', data: data.map(d=>d.tx), smooth: true, symbol: 'none',
        lineStyle: { color: '#f59e0b', width: 2 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,
          [{offset:0,color:'rgba(245,158,11,.18)'},{offset:1,color:'rgba(245,158,11,0)'}]) } },
    ],
  }, true)
}

function stopMon() {
  abortCtrl?.abort()
  abortCtrl = null
  monitoring.value = false
}

async function restartMon() {
  stopMon()
  if (!deviceId.value || !ifIndex.value) return
  monitoring.value = true
  points.value = []
  currentRx.value = 0; currentTx.value = 0
  abortCtrl = new AbortController()
  const d = currentDevice.value!

  try {
    const url = `/api/ros/traffic/stream?host=${encodeURIComponent(d.host)}&if_index=${ifIndex.value}&duration_s=300`
    const resp = await fetch(url, { signal: abortCtrl.signal })
    const reader = resp.body!.getReader()
    const dec = new TextDecoder()
    let buf = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += dec.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const pt = JSON.parse(line.slice(6))
            if (pt.rx_mbps !== undefined) {
              points.value.push({ ts: pt.ts, rx: pt.rx_mbps, tx: pt.tx_mbps })
              currentRx.value = pt.rx_mbps
              currentTx.value = pt.tx_mbps
            }
          } catch {}
        }
      }
    }
  } catch { /* aborted */ }
  finally { monitoring.value = false }
}
</script>

<style scoped>
.monitor-page {
  padding: 20px 24px; height: calc(100vh - 60px);
  display: flex; flex-direction: column; gap: 16px;
  background: #f8fafc; font-family: 'Inter', 'Microsoft YaHei', sans-serif;
}
/* 顶栏 */
.top-bar {
  display: flex; align-items: center; gap: 16px;
  padding: 12px 16px; background: #fff; border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.bar-left { display: flex; align-items: center; gap: 10px; }
.btn-group { display: flex; gap: 4px; }
.ctrl-btn {
  border: none; padding: 7px 14px; border-radius: 6px; font-size: 12px;
  font-weight: 600; cursor: pointer; transition: all .15s;
}
.ctrl-btn.play { background: #6366f1; color: #fff; }
.ctrl-btn.play:hover { background: #4f46e5; }
.ctrl-btn.play:disabled { background: #cbd5e1; cursor: default; }
.ctrl-btn.stop { background: #fee2e2; color: #ef4444; }
.ctrl-btn.stop:hover { background: #fecaca; }
.bar-center { display: flex; align-items: center; gap: 8px; margin-left: 8px; }
.live-dot { width: 8px; height: 8px; border-radius: 50%; background: #10b981; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.live-text { font-size: 12px; font-weight: 600; color: #10b981; }
.live-count { font-size: 11px; color: #94a3b8; }
.bar-right { margin-left: auto; display: flex; align-items: center; gap: 12px; }

/* 速率卡片 */
.stat-cards { display: flex; gap: 12px; }
.stat-card {
  flex: 1; padding: 16px 20px; border-radius: 10px; background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,.04); display: flex; align-items: center; gap: 14px;
}
.stat-card.rx { border-left: 4px solid #6366f1; }
.stat-card.tx { border-left: 4px solid #f59e0b; }
.stat-card.info { border-left: 4px solid #e2e8f0; }
.stat-icon { font-size: 20px; width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center;
  justify-content: center; background: #f1f5f9; color: #64748b; }
.stat-body { display: flex; flex-direction: column; }
.stat-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: .5px; }
.stat-value { font-size: 28px; font-weight: 700; color: #1e293b; font-family: monospace; line-height: 1.1; }
.stat-unit { font-size: 11px; color: #94a3b8; }
.stat-value-sm { font-size: 15px; font-weight: 600; color: #1e293b; font-family: monospace; }

/* 图表 */
.chart-area { flex: 1; position: relative; background: #fff; border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,.04); overflow: hidden; }
.chart-box { width: 100%; height: 100%; }
.chart-hint { position: absolute; inset: 0; display: flex; align-items: center;
  justify-content: center; color: #94a3b8; font-size: 13px; }
</style>

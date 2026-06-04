<template>
  <div class="ros-launcher">
    <div class="ros-header">
      <h2>RouterOS 设备管理器</h2>
      <div style="display:flex;gap:8px">
        <el-button type="primary" size="default" @click="showAdd=true">+ 添加设备</el-button>
        <el-button size="default" @click="showTraffic=true" :disabled="!selectedDevice">📊 流量监控</el-button>
      </div>
    </div>

    <!-- 设备卡片网格 -->
    <div class="device-grid">
      <div
        v-for="d in devices" :key="d.id"
        class="device-card"
        :class="{selected: selectedDevice?.id === d.id}"
        @click="selectedDevice = d"
        @dblclick="openWebfig(d)"
      >
        <div class="card-top">
          <span class="card-name">{{ d.name || d.host }}</span>
          <span class="card-status" :class="d.online !== false ? 'online' : 'offline'">
            {{ d.online !== false ? '● 在线' : '○ 离线' }}
          </span>
        </div>
        <div class="card-info">
          <span>{{ d.host }}:{{ d.port }}</span>
          <span>用户: {{ d.username }}</span>
        </div>
        <div class="card-actions" @click.stop>
          <el-button size="small" link @click="openWebfig(d)">🔗 WebFig</el-button>
          <el-button size="small" link @click="showTraffic=true">📊 流量</el-button>
          <el-button size="small" link type="danger" @click="delDevice(d)">删除</el-button>
        </div>
      </div>

      <div v-if="!devices.length" class="empty-hint">
        <p>暂未添加设备</p>
        <p style="font-size:12px;color:#999">点击「添加设备」保存 RouterOS 信息，之后一键打开 WebFig</p>
      </div>
    </div>

    <!-- 添加设备 -->
    <el-dialog v-model="showAdd" title="添加 RouterOS 设备" width="400px">
      <el-form label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" placeholder="Core-R1" /></el-form-item>
        <el-form-item label="IP">
          <el-input v-model="form.host" placeholder="192.168.88.1" />
        </el-form-item>
        <el-form-item label="端口">
          <el-select v-model="form.port" style="width:120px">
            <el-option :value="80" label="80 (HTTP)" />
            <el-option :value="443" label="443 (HTTPS)" />
          </el-select>
          <span style="font-size:11px;color:#909399;margin-left:8px">WebFig 端口</span>
        </el-form-item>
        <el-form-item label="用户名"><el-input v-model="form.user" placeholder="admin" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd=false">取消</el-button>
        <el-button type="primary" @click="saveDevice">保存</el-button>
      </template>
    </el-dialog>

    <!-- 🆕 流量监控弹窗 -->
    <el-dialog v-model="showTraffic" :title="`📊 实时流量 — ${selectedDevice?.name || selectedDevice?.host}`" width="860px" top="5vh">
      <div style="display:flex;gap:12px;align-items:center;margin-bottom:12px" v-if="selectedDevice">
        <el-select v-model="trafficIfIndex" placeholder="选择接口" size="small" style="width:180px" @change="restartMonitor">
          <el-option v-for="iface in interfaces" :key="iface.index" :label="iface.name" :value="iface.index" />
        </el-select>
        <el-button size="small" @click="restartMonitor" :disabled="!trafficIfIndex">▶ 开始</el-button>
        <el-button size="small" @click="stopMonitor" :disabled="!monitoring">⏹ 停止</el-button>
        <span style="font-size:11px;color:#909399;margin-left:auto">需在 RouterOS 启用 SNMP: /snmp set enabled=yes; /snmp community add name=public</span>
      </div>
      <!-- 即时速率 -->
      <div v-if="monitoring" style="display:flex;gap:24px;margin-bottom:10px;padding:8px 12px;background:#f8fafc;border-radius:6px">
        <span style="font-weight:600">▼ 下载 <span style="color:#6366f1;font-size:18px">{{ currentRx }} Mbps</span></span>
        <span style="font-weight:600">▲ 上传 <span style="color:#f59e0b;font-size:18px">{{ currentTx }} Mbps</span></span>
        <span style="margin-left:auto;font-size:11px;color:#94a3b8">已采集 {{ trafficData.length }} 点</span>
      </div>
      <div ref="trafficChartRef" style="height:320px" v-show="monitoring"></div>
      <div v-if="!monitoring" style="height:100px;display:flex;align-items:center;justify-content:center;color:#94a3b8">
        选择接口后点击「开始」监测流量
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'

/* ── 设备管理 ── */
interface Device { id: string; name: string; host: string; port: number; username: string; online?: boolean }
const devices = ref<Device[]>([])
const selectedDevice = ref<Device | null>(null)
const showAdd = ref(false)
const form = reactive({ name: '', host: '', port: 443, user: 'admin' })
const showTraffic = ref(false)

onMounted(loadDevices)

async function loadDevices() {
  try { const r = await fetch('/api/ros/devices'); devices.value = await r.json() } catch {}
}

async function saveDevice() {
  if (!form.host) { ElMessage.warning('请输入IP'); return }
  await fetch('/api/ros/devices', { method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: form.name, host: form.host, port: form.port, username: form.user, password: '' }) })
  form.name = form.host = ''; form.port = 443
  showAdd.value = false
  await loadDevices()
  ElMessage.success('已保存')
}

async function delDevice(d: Device) {
  await ElMessageBox.confirm(`删除 ${d.name || d.host}？`, '确认', { type: 'warning' })
  await fetch(`/api/ros/devices/${d.id}`, { method: 'DELETE' })
  if (selectedDevice.value?.id === d.id) selectedDevice.value = null
  await loadDevices()
}

function openWebfig(d: Device) {
  const proto = d.port === 443 ? 'https' : 'http'
  window.open(`${proto}://${d.host}:${d.port}`, '_blank')
}

/* ── 流量监控 ── */
const trafficIfIndex = ref(0)
const interfaces = ref<any[]>([])
const monitoring = ref(false)
const currentRx = ref(0)
const currentTx = ref(0)
const trafficData = ref<any[]>([])
const trafficChartRef = ref<HTMLDivElement>()
let trafficChart: echarts.ECharts | null = null
let abortCtrl: AbortController | null = null

watch(showTraffic, async (val) => {
  if (val && selectedDevice.value) {
    stopMonitor()
    // 加载接口列表
    try {
      const r = await fetch(`/api/ros/traffic/interfaces?host=${selectedDevice.value.host}`)
      interfaces.value = await r.json()
      if (interfaces.value.length > 0) trafficIfIndex.value = interfaces.value[0].index
    } catch { interfaces.value = [] }
  }
})

async function restartMonitor() {
  stopMonitor()
  monitoring.value = true
  trafficData.value = []
  currentRx.value = 0; currentTx.value = 0
  abortCtrl = new AbortController()
  const d = selectedDevice.value!
  const url = `/api/ros/traffic/stream?host=${encodeURIComponent(d.host)}&if_index=${trafficIfIndex.value}&duration_s=120`

  try {
    const resp = await fetch(url, { signal: abortCtrl.signal })
    const reader = resp.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const point = JSON.parse(line.slice(6))
            if (point.rx_mbps !== undefined) {
              trafficData.value.push(point)
              currentRx.value = point.rx_mbps
              currentTx.value = point.tx_mbps
              await nextTick(); updateTrafficChart()
            }
          } catch {}
        }
      }
    }
  } catch { /* aborted or error */ }
  finally { monitoring.value = false }
}

function stopMonitor() {
  abortCtrl?.abort()
  monitoring.value = false
}

function updateTrafficChart() {
  if (!trafficChartRef.value) return
  if (!trafficChart) trafficChart = echarts.init(trafficChartRef.value)
  const ts = trafficData.value.map((d: any) => new Date(d.ts * 1000).toLocaleTimeString())
  const rx = trafficData.value.map((d: any) => d.rx_mbps)
  const tx = trafficData.value.map((d: any) => d.tx_mbps)

  trafficChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['下载', '上传'], bottom: 0 },
    grid: { top: 8, right: 12, bottom: 28, left: 44 },
    xAxis: { type: 'category', data: ts, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', name: 'Mbps', nameTextStyle: { fontSize: 10 } },
    series: [
      { name: '下载', type: 'line', data: rx, smooth: true, symbol: 'none', lineStyle: { color: '#6366f1', width: 2 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(99,102,241,.2)'},{offset:1,color:'rgba(99,102,241,0)'}]) } },
      { name: '上传', type: 'line', data: tx, smooth: true, symbol: 'none', lineStyle: { color: '#f59e0b', width: 2 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(245,158,11,.2)'},{offset:1,color:'rgba(245,158,11,0)'}]) } },
    ],
  }, true)
}
</script>

<style scoped>
.ros-launcher { padding: 24px; max-width: 900px; margin: 0 auto; }
.ros-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.ros-header h2 { margin: 0; font-size: 18px; color: #1e293b; }
.device-grid { display: flex; flex-wrap: wrap; gap: 12px; }
.device-card {
  width: 260px; padding: 14px; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 8px; cursor: pointer; transition: all .15s;
}
.device-card:hover { border-color: #3b82f6; box-shadow: 0 2px 8px rgba(59,130,246,.1); }
.device-card.selected { border-color: #3b82f6; background: #eff6ff; }
.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-name { font-weight: 600; font-size: 14px; }
.card-status { font-size: 11px; padding: 2px 6px; border-radius: 4px; }
.card-status.online { color: #10b981; background: rgba(16,185,129,.1); }
.card-status.offline { color: #94a3b8; background: rgba(148,163,184,.1); }
.card-info { font-size: 11px; color: #64748b; display: flex; flex-direction: column; gap: 2px; }
.card-actions { margin-top: 10px; display: flex; gap: 4px; border-top: 1px solid #f1f5f9; padding-top: 8px; }
.empty-hint { width: 100%; text-align: center; padding: 40px; color: #64748b; }
</style>

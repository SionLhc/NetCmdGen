<template>
  <div class="page">
    <h2>📡 无线检测</h2>

    <!-- ── 本机 WiFi 诊断（自动加载） ── -->
    <el-card style="margin-bottom:14px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>💻 本机 WiFi 诊断</span>
          <div style="display:flex;align-items:center;gap:8px">
            <el-switch v-model="wifi.auto" size="small" active-text="自动刷新" inactive-text="手动"/>
            <el-button size="small" @click="getWifiBatch" :loading="wifi.ld">🔄 刷新</el-button>
            <el-button size="small" @click="getWifiEvents" :loading="wifi.ld">📋 事件日志</el-button>
          </div>
        </div>
      </template>

      <!-- 信号卡片 -->
      <div v-if="wifi.status" class="wifi-cards">
        <div class="wc">
          <div class="wc-label">连接状态</div>
          <div class="wc-val" :style="{color:wifi.status.connected?'#10b981':'#ef4444'}">
            {{ wifi.status.connected ? '● 已连接' : '○ 未连接' }}
          </div>
        </div>
        <div class="wc">
          <div class="wc-label">SSID</div>
          <div class="wc-val">{{ wifi.status.ssid || '--' }}</div>
        </div>
        <div class="wc">
          <div class="wc-label">信号强度</div>
          <div class="wc-val" :style="{color:wifi.status.signal>60?'#10b981':wifi.status.signal>30?'#e6a23c':'#ef4444'}">
            {{ wifi.status.signal }}%
          </div>
          <el-progress :percentage="wifi.status.signal||0" :stroke-width="6" :show-text="false"
            :color="(wifi.status.signal||0)>60?'#10b981':(wifi.status.signal||0)>30?'#e6a23c':'#ef4444'"/>
        </div>
        <div class="wc">
          <div class="wc-label">信道</div>
          <div class="wc-val">{{ wifi.status.channel || '--' }}</div>
        </div>
        <div class="wc">
          <div class="wc-label">协议</div>
          <div class="wc-val">{{ wifi.status.radio || '--' }}</div>
        </div>
        <div class="wc">
          <div class="wc-label">速率 ▼/▲</div>
          <div class="wc-val">{{ wifi.status.rx_rate||0 }} / {{ wifi.status.tx_rate||0 }} Mbps</div>
        </div>
      </div>
      <div v-else-if="!wifi.ld" style="text-align:center;padding:16px;color:#94a3b8;font-size:12px">
        {{ wifi.er ? '⚠ 获取失败（仅支持 Windows）' : '正在获取本机 WiFi 状态...' }}
      </div>

      <!-- 周围 AP 列表 -->
      <div v-if="wifi.networks.length" style="margin-top:12px">
        <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:#64748b">🔍 周围 WiFi 网络 ({{ wifi.networks.length }})</div>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
          <div v-for="n in wifi.networks.slice(0,20)" :key="n.bssid" class="ap-chip"
            :style="{borderColor:n.signal>60?'#10b981':n.signal>30?'#e6a23c':'#e2e8f0'}">
            <span class="ap-chip-ssid">{{ n.ssid }}</span>
            <span class="ap-chip-ch" :style="{color:n.channel>14?'#6366f1':'#94a3b8'}">CH{{ n.channel }}</span>
            <span class="ap-chip-sig">{{ n.signal }}%</span>
          </div>
        </div>
        <!-- 信道分布图 -->
        <div ref="channelChartRef" class="channel-chart" v-if="wifi.networks.length"></div>
      </div>

      <!-- 事件日志 -->
      <el-table v-if="wifi.events.length" :data="wifi.events" size="small" border max-height="280" style="margin-top:12px">
        <el-table-column prop="time" label="时间" width="160"/>
        <el-table-column prop="event_id" label="事件ID" width="80" align="center">
          <template #default="{row}">
            <el-tag :type="row.event_id===10000?'success':row.event_id===10001||row.event_id===10003?'danger':'warning'" size="small">{{ row.event_id }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="级别" width="70" align="center">
          <template #default="{row}"><span :style="{color:row.level?.includes('Error')?'#f56c6c':row.level?.includes('Warning')?'#e6a23c':'#67c23a'}">{{ row.level||'--' }}</span></template>
        </el-table-column>
        <el-table-column prop="desc" label="描述" min-width="200"/>
      </el-table>

      <!-- 日志范围设置 -->
      <div v-if="wifi.events.length" style="display:flex;align-items:center;gap:4px;margin-top:4px;font-size:11px;color:#94a3b8">
        查询范围
        <el-input-number v-model="wifi.minutes" :min="1" :max="1440" size="small" style="width:80px" controls-position="right"/>
        分钟
      </div>
    </el-card>

    <!-- ── AC 设备采集 ── -->
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>🏢 AC 设备远程采集</span>
          <el-button size="small" @click="showAcForm=!showAcForm">{{ showAcForm?'收起':'展开' }}</el-button>
        </div>
      </template>

      <!-- 已保存设备快捷入口 -->
      <div v-if="acDevices.length" style="margin-bottom:12px;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <span style="font-size:12px;color:#94a3b8">快捷选择:</span>
        <el-select v-model="selectedAcDevice" placeholder="选择已保存设备" size="small" style="width:240px" @change="onSelectAcDevice" clearable>
          <el-option v-for="d in acDevices" :key="d.ip" :label="`${d.name} (${d.ip})`" :value="d.ip"/>
        </el-select>
        <el-button link size="small" type="primary" @click="$router.push('/health')">管理设备 →</el-button>
      </div>

      <div v-show="showAcForm || !acDevices.length">
        <el-form :inline="true" size="small">
          <el-form-item label="IP"><el-input v-model="devIp" placeholder="192.168.1.1" style="width:140px"/></el-form-item>
          <el-form-item label="用户名"><el-input v-model="username" placeholder="admin" style="width:100px"/></el-form-item>
          <el-form-item label="密码"><el-input v-model="password" type="password" placeholder="SSH密码" style="width:100px"/></el-form-item>
          <el-form-item label="厂商">
            <el-select v-model="vendor" style="width:90px">
              <el-option label="华为" value="huawei"/><el-option label="华三" value="h3c"/>
            </el-select>
          </el-form-item>
          <el-form-item label="采集项">
            <el-checkbox-group v-model="selectedItems" size="small">
              <el-checkbox v-for="t in inspectItems" :key="t.id" :label="t.id" border>{{ t.name }}</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="runInspect" :loading="inspecting">🔍 开始采集</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- AC 采集进度 -->
    <el-alert v-if="inspecting" type="info" :closable="false" show-icon style="margin:12px 0">
      <template #title>采集进行中... {{ inspectProgress }}</template>
    </el-alert>
    <el-alert v-if="inspectResult && !inspecting" :type="inspectResult.errors?'warning':'success'" :closable="false" show-icon style="margin:12px 0">
      <template #title>采集完成 · {{ inspectResult.elapsed_ms }}ms · <span v-if="inspectResult.errors" style="color:#f56c6c">{{ inspectResult.errors }} 项失败</span></template>
    </el-alert>

    <!-- AC 采集结果 -->
    <el-card v-if="apData.length" style="margin-bottom:14px">
      <template #header>📻 AP 设备列表 · {{ apData.length }} 台（<span style="color:#67c23a">在线 {{ apOnline }}</span> / <span style="color:#f56c6c">离线 {{ apData.length-apOnline }}</span>）</template>
      <el-table :data="apData" size="small" border>
        <el-table-column prop="ap_id" label="ID" width="50" align="center"/>
        <el-table-column prop="name" label="名称" width="140"/>
        <el-table-column prop="model" label="型号" width="140"/>
        <el-table-column prop="mac" label="MAC" width="150"/>
        <el-table-column prop="ip" label="IP" width="130"/>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{row}"><span class="ap-dot" :class="row.status"/>{{ row.status==='online'?'在线':'离线' }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px" v-if="radioData.length||clientData.length">
      <el-card v-if="radioData.length">
        <template #header>📶 射频状态</template>
        <el-table :data="radioData" size="small" border>
          <el-table-column prop="ap_name" label="AP" width="100"/>
          <el-table-column prop="band" label="频段" width="70"/>
          <el-table-column prop="channel" label="信道" width="60" align="center"/>
          <el-table-column prop="power" label="功率" width="80"/>
          <el-table-column label="状态" width="60" align="center">
            <template #default="{row}"><span class="ap-dot" :class="row.status==='on'?'online':'offline'"/></template>
          </el-table-column>
        </el-table>
      </el-card>
      <el-card v-if="clientData.length">
        <template #header>📱 客户端列表 · {{ clientData.length }} 台</template>
        <el-table :data="clientData" size="small" border max-height="300">
          <el-table-column prop="mac" label="MAC" width="150"/>
          <el-table-column prop="ip" label="IP" width="130"/>
          <el-table-column label="信号" width="80" align="center">
            <template #default="{row}">
              <el-tag :type="row.rssi>=-55?'success':row.rssi>=-70?'warning':'danger'" size="small">{{ row.rssi }} dBm</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="rate" label="速率" width="90"/>
        </el-table>
      </el-card>
    </div>

    <el-card v-if="ssidData.length" style="margin-top:14px">
      <template #header>🔐 SSID 配置</template>
      <el-table :data="ssidData" size="small" border>
        <el-table-column prop="ssid" label="SSID" width="180"/>
        <el-table-column prop="security" label="安全策略" width="100" align="center">
          <template #default="{row}"><el-tag :type="row.security==='Open'?'danger':'success'" size="small">{{ row.security }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="vlan" label="VLAN" width="80" align="center"/>
        <el-table-column prop="hidden" label="隐藏" width="60" align="center"/>
      </el-table>
    </el-card>

    <el-card v-if="utilData.length" style="margin-top:14px">
      <template #header>📊 信道利用率/底噪</template>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <div v-for="u in utilData" :key="u.type" style="background:#f8fafc;border-radius:8px;padding:12px 18px;text-align:center">
          <div style="font-size:10px;color:#94a3b8">{{ u.type==='channel_utilization'?'信道利用率':'底噪' }}</div>
          <div style="font-size:22px;font-weight:700;color:#6366f1">{{ u.value }}{{ u.unit }}</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

/* ── 本机 WiFi（页面加载自动获取） ── */
const wifi = reactive({
  ld: false, er: false, auto: false,
  status: null as any,
  networks: [] as any[],
  events: [] as any[],
  minutes: 30,
})
let _wifiTimer: ReturnType<typeof setInterval>|null = null

const channelChartRef = ref<HTMLElement|null>(null)
let channelChart: echarts.ECharts|null = null

async function getWifiBatch() {
  wifi.ld = true; wifi.er = false; wifi.status = null; wifi.networks = []
  try {
    const r = await fetch('/api/tools/wifi/batch')
    const d = await r.json()
    if (d.detail) { wifi.er = true; return }  // 非 Windows
    wifi.status = d; wifi.networks = d.networks || []
    await nextTick()
    renderChannelChart()
  } catch { wifi.er = true }
  finally { wifi.ld = false }
}

function renderChannelChart() {
  if (!channelChartRef.value || !wifi.networks.length) return
  // 按信道统计 AP 数量
  const chanMap: Record<number, number> = {}
  wifi.networks.forEach(n => {
    if (n.channel > 0) chanMap[n.channel] = (chanMap[n.channel] || 0) + 1
  })
  const ch24: number[] = [], ch50: number[] = [], labels24: string[] = [], labels50: string[] = []
  Object.entries(chanMap).sort((a,b) => parseInt(a[0])-parseInt(b[0])).forEach(([ch, cnt]) => {
    const c = parseInt(ch)
    if (c <= 14) { labels24.push(`CH${c}`); ch24.push(cnt) }
    else { labels50.push(`CH${c}`); ch50.push(cnt) }
  })

  if (!channelChart) channelChart = echarts.init(channelChartRef.value)
  // 双图：2.4G 上 + 5G 下
  const grid24 = { top: 8, right: 12, bottom: 4, left: 40, height: '38%' }
  const grid50 = { top: '56%', right: 12, bottom: 24, left: 40, height: '38%' }

  const x24 = labels24.length ? {
    type: 'category' as const, data: labels24, axisLabel: { fontSize: 9, color: '#94a3b8' }, axisTick: { show: false },
  } : { show: false as const }
  const x50 = labels50.length ? {
    type: 'category' as const, data: labels50, axisLabel: { fontSize: 9, color: '#6366f1' }, axisTick: { show: false },
  } : { show: false as const }

  channelChart.setOption({
    backgroundColor: 'transparent',
    title: { text: '📊 信道占用分布', left: 'center', top: 0, textStyle: { fontSize: 12, color: '#64748b', fontWeight: 600 } },
    grid: [grid24, grid50],
    xAxis: [
      { ...x24, gridIndex: 0, position: 'bottom' as const },
      { ...x50, gridIndex: 1, position: 'bottom' as const },
    ],
    yAxis: [
      { type: 'value' as const, gridIndex: 0, axisLabel: { fontSize: 9, color: '#94a3b8' }, splitLine: { lineStyle: { color: '#f1f5f9' } } },
      { type: 'value' as const, gridIndex: 1, axisLabel: { fontSize: 9, color: '#94a3b8' }, splitLine: { lineStyle: { color: '#f1f5f9' } } },
    ],
    series: [
      { name: '2.4GHz AP数', type: 'bar', data: ch24, xAxisIndex: 0, yAxisIndex: 0, itemStyle: { color: '#f59e0b', borderRadius: [3,3,0,0] }, barWidth: 20 },
      { name: '5GHz AP数', type: 'bar', data: ch50, xAxisIndex: 1, yAxisIndex: 1, itemStyle: { color: '#6366f1', borderRadius: [3,3,0,0] }, barWidth: 20 },
    ],
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  }, true)
}

async function getWifiEvents() {
  wifi.ld = true; wifi.events = []
  try { const r = await fetch(`/api/tools/wifi/events?minutes=${wifi.minutes}`); wifi.events = await r.json() } catch {}
  finally { wifi.ld = false }
}

watch(() => wifi.auto, (v) => {
  if (v) { getWifiBatch(); _wifiTimer = setInterval(getWifiBatch, 10000) }
  else { if (_wifiTimer) { clearInterval(_wifiTimer); _wifiTimer = null } }
})

/* ── AC 设备管理 ── */
const acDevices = ref<any[]>([])
const selectedAcDevice = ref('')
const showAcForm = ref(true)

async function loadAcDevices() {
  try { const r = await fetch('/api/health/devices'); acDevices.value = await r.json() } catch {}
}
function onSelectAcDevice(ip: string) {
  if (!ip) return
  const d = acDevices.value.find(x => x.ip === ip)
  if (d) {
    devIp.value = d.ip
    username.value = d.username || 'admin'
    password.value = d.password || ''
    showAcForm.value = false
  }
}

/* ── AC 采集 ── */
const inspectItems = ref([
  { id: 'ap_list', name: 'AP列表' }, { id: 'ap_radio', name: '射频' },
  { id: 'client_list', name: '客户端' }, { id: 'ssid_list', name: 'SSID' },
  { id: 'radio_util', name: '信道利用率' },
])
const devIp = ref(''), username = ref('admin'), password = ref(''), vendor = ref('huawei')
const selectedItems = ref(['ap_list','ap_radio','client_list','ssid_list','radio_util'])
const inspecting = ref(false), inspectResult = ref<any>(null), inspectProgress = ref('')

const apData = computed(() => inspectResult.value?.results?.ap_list?.data || [])
const apOnline = computed(() => apData.value.filter((a:any)=>a.status==='online').length)
const radioData = computed(() => inspectResult.value?.results?.ap_radio?.data || [])
const clientData = computed(() => inspectResult.value?.results?.client_list?.data || [])
const ssidData = computed(() => inspectResult.value?.results?.ssid_list?.data || [])
const utilData = computed(() => inspectResult.value?.results?.radio_util?.data || [])

async function runInspect() {
  if (!devIp.value) { ElMessage.warning('请输入 AC 设备 IP'); return }
  if (!username.value) { ElMessage.warning('请输入用户名'); return }
  if (!password.value) { ElMessage.warning('请输入密码'); return }
  if (!selectedItems.value.length) { ElMessage.warning('请勾选采集项'); return }

  inspecting.value = true; inspectResult.value = null
  inspectProgress.value = `连接 ${devIp.value}...`
  try {
    const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 120000)
    inspectProgress.value = '执行命令中...'
    const r = await fetch(`/api/wireless/inspect?device_ip=${encodeURIComponent(devIp.value)}&device_port=22&username=${encodeURIComponent(username.value)}&password=${encodeURIComponent(password.value)}&vendor=${vendor.value}&items=${selectedItems.value.join(',')}`, { method: 'POST', signal: ctrl.signal })
    if (!r.ok) { ElMessage.error(`失败: HTTP ${r.status}`); return }
    inspectProgress.value = '解析结果...'
    const data = await r.json(); inspectResult.value = data
    ElMessage[data.errors?'warning':'success'](data.errors ? `完成，${data.errors} 项失败` : '采集完成')
  } catch (e: any) { ElMessage.error(e.name==='AbortError'?'超时(2分钟)':`失败: ${e.message}`) }
  finally { inspecting.value = false; inspectProgress.value = '' }
}

onMounted(async () => {
  getWifiBatch()
  await loadAcDevices()
})
onUnmounted(() => { if (_wifiTimer) clearInterval(_wifiTimer); channelChart?.dispose() })
</script>

<style scoped>
.page { padding: 24px; max-width: 1400px; margin: 0 auto; }
h2 { margin: 0 0 14px; font-size: 20px; }

/* WiFi 卡片 */
.wifi-cards { display: grid; grid-template-columns: repeat(auto-fill,minmax(160px,1fr)); gap: 10px; }
.wc { background: #f8fafc; border-radius: 8px; padding: 10px 14px; }
.wc-label { font-size: 10px; color: #94a3b8; margin-bottom: 4px; }
.wc-val { font-size: 15px; font-weight: 700; color: #1e293b; }

/* AP chip */
.ap-chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 14px; border: 1.5px solid #e2e8f0; background: #fff; font-size: 11px; }
.ap-chip-ssid { font-weight: 600; color: #1e293b; }
.ap-chip-ch { font-size: 10px; }
.ap-chip-sig { font-size: 10px; color: #64748b; }

/* 信道分布图 */
.channel-chart { width: 100%; height: 220px; margin-top: 10px; }

/* AP 状态点 */
.ap-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; margin-right: 4px; }
.ap-dot.online { background: #10b981; } .ap-dot.offline { background: #ef4444; }
</style>

<template>
  <div class="page">
    <h2>📡 无线检测</h2>

    <!-- ── 本机 WiFi 诊断 ── -->
    <el-card style="margin-bottom:14px">
      <template #header>💻 本机 WiFi 诊断（Windows netsh/WMI）</template>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <el-button @click="getWifiStatus" :loading="wifi.ld">📶 实时状态</el-button>
        <el-button @click="getWifiScan" :loading="wifi.ld">🔍 信道扫描</el-button>
        <span style="font-size:12px;color:#94a3b8;display:flex;align-items:center;gap:4px">
          日志范围
          <el-input-number v-model="wifi.minutes" :min="1" :max="1440" size="small" style="width:90px"/>
          分钟
        </span>
        <el-button @click="getWifiEvents" :loading="wifi.ld">📋 事件日志</el-button>
      </div>

      <!-- WiFi 实时状态 -->
      <el-descriptions v-if="wifi.status" :column="3" border size="small" style="margin-top:12px">
        <el-descriptions-item label="状态">
          <el-tag :type="wifi.status.connected?'success':'danger'">{{ wifi.status.connected?'已连接':'未连接' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="SSID">{{ wifi.status.ssid||'--' }}</el-descriptions-item>
        <el-descriptions-item label="BSSID">{{ wifi.status.bssid||'--' }}</el-descriptions-item>
        <el-descriptions-item label="信号">
          <el-progress :percentage="wifi.status.signal||0" :stroke-width="16"
            :color="(wifi.status.signal||0)>60?'#67c23a':(wifi.status.signal||0)>30?'#e6a23c':'#f56c6c'"/>
        </el-descriptions-item>
        <el-descriptions-item label="信道">{{ wifi.status.channel||'--' }}</el-descriptions-item>
        <el-descriptions-item label="无线类型">{{ wifi.status.radio||'--' }}</el-descriptions-item>
        <el-descriptions-item label="速率">▼{{ wifi.status.rx_rate||0 }}M / ▲{{ wifi.status.tx_rate||0 }}M</el-descriptions-item>
        <el-descriptions-item label="认证">{{ wifi.status.auth||'--' }}</el-descriptions-item>
        <el-descriptions-item label="网卡">{{ wifi.status.adapter?.name||'--' }}</el-descriptions-item>
      </el-descriptions>

      <!-- WiFi 信道扫描 -->
      <el-table v-if="wifi.networks.length" :data="wifi.networks" size="small" border max-height="300" style="margin-top:12px">
        <el-table-column prop="ssid" label="SSID" width="160"/>
        <el-table-column prop="bssid" label="BSSID" width="150"/>
        <el-table-column label="信号" width="120" align="center">
          <template #default="{row}">
            <el-progress :percentage="row.signal" :stroke-width="14"
              :color="row.signal>60?'#67c23a':row.signal>30?'#e6a23c':'#f56c6c'"/>
          </template>
        </el-table-column>
        <el-table-column prop="channel" label="信道" width="60" align="center">
          <template #default="{row}"><el-tag :type="row.channel>14?'success':''" size="small">{{ row.channel }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="radio" label="类型" width="100"/>
        <el-table-column prop="rate" label="速率" width="90"/>
      </el-table>

      <!-- WiFi 事件日志 -->
      <el-table v-if="wifi.events.length" :data="wifi.events" size="small" border max-height="300" style="margin-top:12px">
        <el-table-column prop="time" label="时间" width="160"/>
        <el-table-column prop="event_id" label="EventID" width="80" align="center">
          <template #default="{row}">
            <el-tag :type="row.event_id===10000?'success':row.event_id===10001||row.event_id===10003?'danger':'warning'" size="small">{{ row.event_id }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="级别" width="70" align="center">
          <template #default="{row}">
            <span :style="{color:row.level?.includes('Error')?'#f56c6c':row.level?.includes('Warning')?'#e6a23c':'#67c23a'}">{{ row.level||'--' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="desc" label="描述" min-width="200"/>
      </el-table>
    </el-card>

    <!-- ── AC 设备采集 ── -->
    <el-card>
      <template #header>🏢 AC 设备远程采集（SSH）</template>
      <el-form :inline="true" size="default">
        <el-form-item label="AC设备IP">
          <el-input v-model="devIp" placeholder="192.168.1.1" style="width:150px"/>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="username" placeholder="admin" style="width:110px"/>
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" placeholder="SSH密码" style="width:110px"/>
        </el-form-item>
        <el-form-item label="厂商">
          <el-select v-model="vendor" style="width:100px">
            <el-option label="华为" value="huawei"/><el-option label="华三" value="h3c"/>
          </el-select>
        </el-form-item>
        <el-form-item label="采集项">
          <el-checkbox-group v-model="selectedItems" style="display:flex;flex-wrap:wrap;gap:6px">
            <el-checkbox v-for="t in inspectItems" :key="t.id" :label="t.id" border size="small">{{ t.name }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="runInspect" :loading="inspecting">🔍 开始采集</el-button>
        </el-form-item>
      </el-form>
      <div style="font-size:11px;color:#94a3b8">设备需开启 WLAN 功能并支持 SSH 登录。</div>
    </el-card>

    <!-- AC 采集结果 -->
    <el-alert v-if="inspecting" type="info" title="采集进行中..." :closable="false" show-icon style="margin:12px 0"/>
    <el-alert v-if="inspectResult && !inspecting" :type="inspectResult.errors?'warning':'success'" :closable="false" show-icon style="margin:12px 0">
      <template #title>采集完成 · {{ inspectResult.elapsed_ms }}ms · <span v-if="inspectResult.errors" style="color:#f56c6c">{{ inspectResult.errors }} 项失败</span></template>
    </el-alert>

    <el-card v-if="apData.length" style="margin-bottom:14px">
      <template #header>
        📻 AP 设备列表 · {{ apData.length }} 台（<span style="color:#67c23a">在线 {{ apOnline }}</span> / <span style="color:#f56c6c">离线 {{ apData.length-apOnline }}</span>）
      </template>
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
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'

/* ── 本机 WiFi ── */
const wifi = reactive({
  ld: false,
  status: null as any,
  networks: [] as any[],
  events: [] as any[],
  minutes: 30,
})

/** 批量获取：一次 netsh && 拿到状态 + AP 列表，减少 HTTP 往返 */
async function getWifiStatus() {
  wifi.ld = true; wifi.status = null
  try {
    const r = await fetch('/api/tools/wifi/batch')
    const d = await r.json()
    wifi.status = d
    wifi.networks = d.networks || []
  } catch { } finally { wifi.ld = false }
}
/** 单独扫描（更详细） */
async function getWifiScan() {
  wifi.ld = true; wifi.networks = []
  try { const r = await fetch('/api/tools/wifi/networks'); wifi.networks = await r.json() } catch {}
  finally { wifi.ld = false }
}
async function getWifiEvents() {
  wifi.ld = true; wifi.events = []
  try { const r = await fetch(`/api/tools/wifi/events?minutes=${wifi.minutes}`); wifi.events = await r.json() } catch {}
  finally { wifi.ld = false }
}

/* ── AC 采集 ── */
const inspectItems = ref([
  { id: 'ap_list', name: 'AP列表' }, { id: 'ap_radio', name: '射频' },
  { id: 'client_list', name: '客户端' }, { id: 'ssid_list', name: 'SSID' },
  { id: 'radio_util', name: '信道利用率' },
])

const devIp = ref(''), username = ref('admin'), password = ref(''), vendor = ref('huawei')
const selectedItems = ref(['ap_list', 'ap_radio', 'client_list', 'ssid_list', 'radio_util'])
const inspecting = ref(false), inspectResult = ref<any>(null)

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
  try {
    const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 120000)
    const r = await fetch(`/api/wireless/inspect?device_ip=${encodeURIComponent(devIp.value)}&device_port=22&username=${encodeURIComponent(username.value)}&password=${encodeURIComponent(password.value)}&vendor=${vendor.value}&items=${selectedItems.value.join(',')}`, { method: 'POST', signal: ctrl.signal })
    if (!r.ok) { ElMessage.error(`失败: HTTP ${r.status}`); return }
    const data = await r.json(); inspectResult.value = data
    ElMessage[data.errors?'warning':'success'](data.errors ? `完成，${data.errors} 项失败` : '采集完成')
  } catch (e: any) { ElMessage.error(e.name==='AbortError'?'超时(2分钟)':`失败: ${e.message}`) }
  finally { inspecting.value = false }
}
</script>

<style scoped>
.page { padding: 24px; max-width: 1400px; margin: 0 auto; }
h2 { margin: 0 0 14px; font-size: 20px; }
.ap-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; margin-right: 4px; }
.ap-dot.online { background: #10b981; } .ap-dot.offline { background: #ef4444; }
</style>

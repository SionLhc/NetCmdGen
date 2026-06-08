<template>
  <div class="page">
    <h2>📡 无线检测</h2>

    <!-- 采集表单 -->
    <el-card style="margin-bottom:14px">
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
            <el-option label="华为" value="huawei"/>
            <el-option label="华三" value="h3c"/>
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
      <div style="font-size:11px;color:#94a3b8">
        提示：请确保设备已开启 WLAN 功能（AC 或 FAT AP），支持 SSH 登录。
      </div>
    </el-card>

    <!-- 采集进度 -->
    <el-alert v-if="inspecting" type="info" title="采集进行中..." :closable="false" show-icon style="margin-bottom:12px"/>
    <el-alert v-if="inspectResult && !inspecting" :type="inspectResult.errors ? 'warning' : 'success'"
      :closable="false" show-icon style="margin-bottom:12px">
      <template #title>
        采集完成 · 耗时 {{ inspectResult.elapsed_ms }}ms ·
        <span v-if="inspectResult.errors" style="color:#f56c6c">{{ inspectResult.errors }} 项失败</span>
      </template>
    </el-alert>

    <!-- AP 设备列表 -->
    <el-card v-if="apData.length" style="margin-bottom:14px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>📻 AP 设备列表</span>
          <span style="font-size:12px;color:#94a3b8">
            {{ apData.length }} 台 · 
            <span style="color:#67c23a">在线 {{ apOnline }}</span> ·
            <span style="color:#f56c6c">离线 {{ apData.length - apOnline }}</span>
          </span>
        </div>
      </template>
      <el-table :data="apData" size="small" border>
        <el-table-column prop="ap_id" label="ID" width="50" align="center"/>
        <el-table-column prop="name" label="名称" width="140"/>
        <el-table-column prop="model" label="型号" width="140"/>
        <el-table-column prop="mac" label="MAC" width="150"/>
        <el-table-column prop="ip" label="IP" width="130"/>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{row}">
            <span class="ap-dot" :class="row.status"></span>
            {{ row.status === 'online' ? '在线' : '离线' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 射频状态 + 客户端 双栏 -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px" v-if="radioData.length || clientData.length">
      <el-card v-if="radioData.length">
        <template #header>📶 射频状态</template>
        <el-table :data="radioData" size="small" border>
          <el-table-column prop="ap_name" label="AP" width="100"/>
          <el-table-column prop="band" label="频段" width="70"/>
          <el-table-column prop="channel" label="信道" width="60" align="center"/>
          <el-table-column prop="power" label="功率" width="80"/>
          <el-table-column label="状态" width="60" align="center">
            <template #default="{row}">
              <span class="ap-dot" :class="row.status === 'on' ? 'online' : 'offline'"></span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card v-if="clientData.length">
        <template #header>
          📱 客户端列表
          <span style="font-size:12px;color:#94a3b8;margin-left:8px">{{ clientData.length }} 台</span>
        </template>
        <el-table :data="clientData" size="small" border max-height="300">
          <el-table-column prop="mac" label="MAC" width="150"/>
          <el-table-column prop="ip" label="IP" width="130"/>
          <el-table-column label="信号" width="80" align="center">
            <template #default="{row}">
              <el-tag :type="row.rssi>=-55?'success':row.rssi>=-70?'warning':'danger'" size="small">
                {{ row.rssi }} dBm
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="rate" label="速率" width="90"/>
        </el-table>
      </el-card>
    </div>

    <!-- SSID 配置 -->
    <el-card v-if="ssidData.length" style="margin-top:14px">
      <template #header>🔐 SSID 配置</template>
      <el-table :data="ssidData" size="small" border>
        <el-table-column prop="ssid" label="SSID" width="180"/>
        <el-table-column prop="security" label="安全策略" width="100" align="center">
          <template #default="{row}">
            <el-tag :type="row.security==='Open'?'danger':'success'" size="small">{{ row.security }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="vlan" label="VLAN" width="80" align="center"/>
        <el-table-column prop="hidden" label="隐藏" width="60" align="center"/>
      </el-table>
    </el-card>

    <!-- 信道利用率 -->
    <el-card v-if="utilData.length" style="margin-top:14px">
      <template #header>📊 信道利用率 / 底噪</template>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <div v-for="u in utilData" :key="u.type" style="background:#f8fafc;border-radius:8px;padding:12px 18px;text-align:center">
          <div style="font-size:10px;color:#94a3b8">{{ u.type === 'channel_utilization' ? '信道利用率' : '底噪' }}</div>
          <div style="font-size:22px;font-weight:700;color:#6366f1">
            {{ u.value }}{{ u.unit }}
          </div>
        </div>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-if="!inspecting && !inspectResult && !apData.length" description="输入 AC 设备 IP + SSH 凭证，点击开始采集"/>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'

/* ── 采集项 ── */
const inspectItems = ref([
  { id: 'ap_list', name: 'AP列表' },
  { id: 'ap_radio', name: '射频' },
  { id: 'client_list', name: '客户端' },
  { id: 'ssid_list', name: 'SSID' },
  { id: 'radio_util', name: '信道利用率' },
])

const devIp = ref('')
const username = ref('admin')
const password = ref('')
const vendor = ref('huawei')
const selectedItems = ref(['ap_list', 'ap_radio', 'client_list', 'ssid_list', 'radio_util'])
const inspecting = ref(false)
const inspectResult = ref<any>(null)

const apData = computed(() => inspectResult.value?.results?.ap_list?.data || [])
const apOnline = computed(() => apData.value.filter((a: any) => a.status === 'online').length)
const radioData = computed(() => inspectResult.value?.results?.ap_radio?.data || [])
const clientData = computed(() => inspectResult.value?.results?.client_list?.data || [])
const ssidData = computed(() => inspectResult.value?.results?.ssid_list?.data || [])
const utilData = computed(() => inspectResult.value?.results?.radio_util?.data || [])

async function runInspect() {
  if (!devIp.value) { ElMessage.warning('请输入 AC 设备 IP'); return }
  if (!username.value) { ElMessage.warning('请输入用户名'); return }
  if (!password.value) { ElMessage.warning('请输入密码'); return }
  if (!selectedItems.value.length) { ElMessage.warning('请勾选至少一个采集项'); return }

  inspecting.value = true
  inspectResult.value = null
  try {
    const items = selectedItems.value.join(',')
    const ctrl = new AbortController()
    setTimeout(() => ctrl.abort(), 120000)
    const r = await fetch(
      `/api/wireless/inspect?device_ip=${encodeURIComponent(devIp.value)}&device_port=22&username=${encodeURIComponent(username.value)}&password=${encodeURIComponent(password.value)}&vendor=${vendor.value}&items=${items}`,
      { method: 'POST', signal: ctrl.signal },
    )
    if (!r.ok) { ElMessage.error(`采集失败: HTTP ${r.status}`); return }
    const data = await r.json()
    inspectResult.value = data
    if (data.errors) ElMessage.warning(`采集完成，${data.errors} 项失败`)
    else ElMessage.success('采集完成')
  } catch (e: any) {
    if (e.name === 'AbortError') ElMessage.error('采集超时(2分钟)')
    else ElMessage.error(`采集失败: ${e.message}`)
  } finally {
    inspecting.value = false
  }
}
</script>

<style scoped>
.page { padding: 24px; max-width: 1400px; margin: 0 auto; }
h2 { margin: 0 0 14px; font-size: 20px; }
.ap-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; margin-right: 4px; }
.ap-dot.online { background: #10b981; }
.ap-dot.offline { background: #ef4444; }
</style>

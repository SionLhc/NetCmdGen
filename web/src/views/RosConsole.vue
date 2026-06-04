<template>
  <div class="ros-page">
    <div class="ros-header">
      <h2>🖥 RouterOS 控制台</h2>
      <span style="color:#909399;font-size:13px">Web 端 Winbox — 管理 MikroTik 设备</span>
    </div>

    <!-- 工具栏 -->
    <div class="ros-toolbar">
      <el-button type="primary" @click="showAddDialog = true">+ 添加设备</el-button>
      <el-button @click="handleMndpScan" :loading="scanning">🔍 扫描局域网</el-button>
      <span v-if="!currentDevice" style="color:#909399;font-size:13px;margin-left:12px">选择设备或添加新设备后开始管理</span>
    </div>

    <!-- 设备列表 -->
    <div class="ros-device-grid" v-if="devices.length > 0">
      <div
        v-for="d in devices"
        :key="d.id"
        class="device-card"
        :class="{ active: currentDevice?.id === d.id, online: d.online }"
        @click="selectDevice(d)"
      >
        <div class="dc-status"><span class="dc-dot" :class="{ on: d.online }"></span></div>
        <div class="dc-name">{{ d.name }}</div>
        <div class="dc-host">{{ d.host }}:{{ d.port }}</div>
        <div class="dc-actions" @click.stop>
          <el-button link size="small" type="danger" @click="removeDevice(d)">删除</el-button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无设备，点击「添加设备」或「扫描局域网」" />

    <!-- 当前设备仪表盘 -->
    <div v-if="currentDevice && sysInfo" class="ros-dashboard">
      <el-divider />
      <h3 style="margin:0 0 12px">{{ currentDevice.name }} — 系统信息</h3>
      <div class="sys-grid">
        <div class="sys-card"><div class="sys-label">CPU 负载</div><div class="sys-value">{{ sysInfo.cpu_load || '—' }}%</div></div>
        <div class="sys-card"><div class="sys-label">内存</div><div class="sys-value">{{ sysInfo.free_memory }} / {{ sysInfo.total_memory }}</div></div>
        <div class="sys-card"><div class="sys-label">运行时间</div><div class="sys-value">{{ sysInfo.uptime || '—' }}</div></div>
        <div class="sys-card"><div class="sys-label">版本</div><div class="sys-value">{{ sysInfo.version || '—' }}</div></div>
        <div class="sys-card"><div class="sys-label">型号</div><div class="sys-value">{{ sysInfo.board_name || '—' }}</div></div>
        <div class="sys-card"><div class="sys-label">接口数</div><div class="sys-value">{{ interfaces.length }}</div></div>
      </div>

      <!-- 接口列表 -->
      <h4 style="margin:16px 0 8px">接口状态</h4>
      <el-table :data="interfaces" size="small" border stripe max-height="300">
        <el-table-column prop="name" label="接口" width="140" />
        <el-table-column prop="type" label="类型" width="80" />
        <el-table-column label="状态" width="80">
          <template #default="{row}">
            <el-tag :type="row.running==='true'?'success':'info'" size="small">{{ row.running==='true'?'运行':'关闭' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="mac-address" label="MAC 地址" width="150" />
        <el-table-column prop="rx-byte" label="RX" width="110" />
        <el-table-column prop="tx-byte" label="TX" width="110" />
        <el-table-column label="已禁用" width="80">
          <template #default="{row}">{{ row.disabled==='true'?'是':'否' }}</template>
        </el-table-column>
      </el-table>

      <div style="margin-top:12px">
        <el-button size="small" @click="loadSystemInfo">🔄 刷新</el-button>
        <el-button size="small" type="warning" @click="currentDevice=null">切换设备</el-button>
      </div>
    </div>

    <!-- 添加设备对话框 -->
    <el-dialog v-model="showAddDialog" title="添加 RouterOS 设备" width="450px">
      <el-form label-width="80px" size="default" @submit.prevent="handleAddDevice">
        <el-form-item label="设备名称"><el-input v-model="formName" placeholder="Core-R1" /></el-form-item>
        <el-form-item label="IP 地址"><el-input v-model="formHost" placeholder="192.168.88.1" /></el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="formPort" :min="1" :max="65535" />
          <span style="font-size:11px;color:#909399;margin-left:8px">REST API (443), 非 Winbox (8291)</span>
        </el-form-item>
        <el-form-item label="用户名"><el-input v-model="formUser" placeholder="admin" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="formPass" type="password" placeholder="输入密码" show-password /></el-form-item>
        <el-form-item label="使用 SSL"><el-switch v-model="formSsl" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddDevice" :loading="adding">保存并连接</el-button>
      </template>
    </el-dialog>

    <!-- MNDP 扫描结果 -->
    <el-dialog v-model="showScanResults" title="扫描结果" width="500px">
      <el-table :data="scanDevices" size="small" border>
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="identity" label="设备名" min-width="140" />
        <el-table-column prop="version" label="版本" width="120" />
        <el-table-column prop="platform" label="平台" width="100" />
        <el-table-column label="操作" width="80">
          <template #default="{row}">
            <el-button link type="primary" size="small" @click="quickAdd(row)">添加</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="scanDevices.length === 0 && !scanning" description="未发现 RouterOS 设备" />
      <template #footer><el-button @click="showScanResults=false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 设备列表
interface RosDevice {
  id: string; name: string; host: string; port: number; username: string
  use_ssl: boolean; group: string; online?: boolean
}
const devices = ref<RosDevice[]>([])
const currentDevice = ref<RosDevice | null>(null)
const sysInfo = ref<any>(null)
const interfaces = ref<any[]>([])

// 表单
const showAddDialog = ref(false)
const formName = ref('')
const formHost = ref('')
const formPort = ref(443)
const formUser = ref('admin')
const formPass = ref('')
const formSsl = ref(true)
const adding = ref(false)

// MNDP
const scanning = ref(false)
const showScanResults = ref(false)
const scanDevices = ref<any[]>([])

onMounted(() => loadDevices())

async function loadDevices() {
    try {
        const r = await fetch('/api/ros/devices')
        devices.value = await r.json()
    } catch { /* ignore */ }
}

async function handleAddDevice() {
    if (!formHost.value.trim()) { ElMessage.warning('请输入 IP 地址'); return }
    adding.value = true
    try {
        // 保存设备
        await fetch('/api/ros/devices', {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                host: formHost.value, port: formPort.value,
                username: formUser.value, password: formPass.value,
                use_ssl: formSsl.value,
            }),
        })
        await loadDevices()
        showAddDialog.value = false

        // 自动连接
        const dev = devices.value.find(d => d.host === formHost.value && d.port === formPort.value)
        if (dev) selectDevice(dev)
    } catch {
        ElMessage.error('添加失败')
    } finally { adding.value = false }
}

async function selectDevice(d: RosDevice) {
    currentDevice.value = d
    sysInfo.value = null
    try {
        const r = await fetch(`/api/ros/devices/${d.id}/connect`)
        const data = await r.json()
        if (data.success) {
            d.online = true
            sysInfo.value = data
            // 加载接口
            const ifR = await fetch(`/api/ros/interfaces?device_id=${d.id}`)
            interfaces.value = await ifR.json()
            ElMessage.success(`已连接 ${d.name || d.host}`)
        } else {
            d.online = false
            sysInfo.value = { error: data.error }
            ElMessage.error('连接失败: ' + data.error)
        }
    } catch {
        d.online = false
        ElMessage.error('无法连接设备')
    }
}

async function loadSystemInfo() {
    if (!currentDevice.value) return
    await selectDevice(currentDevice.value)
}

async function removeDevice(d: RosDevice) {
    try {
        await ElMessageBox.confirm(`确定删除设备 "${d.name}"?`, '确认删除', { type: 'warning' })
        await fetch(`/api/ros/devices/${d.id}`, { method: 'DELETE' })
        devices.value = devices.value.filter(x => x.id !== d.id)
        if (currentDevice.value?.id === d.id) currentDevice.value = null
        ElMessage.success('已删除')
    } catch { /* cancelled */ }
}

async function handleMndpScan() {
    scanning.value = true
    scanDevices.value = []
    showScanResults.value = true
    try {
        const r = await fetch('/api/ros/discover?timeout=3')
        const data = await r.json()
        scanDevices.value = data.devices || []
    } finally { scanning.value = false }
}

function quickAdd(row: any) {
    formHost.value = row.ip
    formName.value = row.identity || row.ip
    showScanResults.value = false
    showAddDialog.value = true
}
</script>

<style scoped>
.ros-page { padding: 24px; max-width: 1200px; margin: 0 auto; }
.ros-header { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.ros-header h2 { margin: 0; font-size: 20px; }
.ros-toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 16px; }
.ros-device-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 16px; }
.device-card {
  padding: 16px; border-radius: 10px; border: 2px solid #e5e7eb;
  cursor: pointer; transition: all .2s; position: relative; background: #fff;
}
.device-card:hover { border-color: #6366f1; box-shadow: 0 2px 8px rgba(99,102,241,.1); }
.device-card.active { border-color: #6366f1; background: #f5f3ff; }
.device-card.online .dc-dot.on { background: #10b981; }
.dc-status { position: absolute; top: 10px; right: 10px; }
.dc-dot { width: 10px; height: 10px; border-radius: 50%; background: #cbd5e1; display: block; }
.dc-dot.on { background: #10b981; box-shadow: 0 0 4px rgba(16,185,129,.4); }
.dc-name { font-size: 15px; font-weight: 600; color: #1e293b; }
.dc-host { font-size: 12px; color: #64748b; margin-top: 4px; font-family: monospace; }
.dc-actions { margin-top: 8px; }
.ros-dashboard { margin-top: 8px; }
.sys-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.sys-card { padding: 16px; background: #f8fafc; border-radius: 8px; border: 1px solid #f1f5f9; }
.sys-label { font-size: 11px; color: #94a3b8; margin-bottom: 4px; }
.sys-value { font-size: 18px; font-weight: 700; color: #1e293b; font-family: monospace; }
</style>

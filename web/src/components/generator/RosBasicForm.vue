<template>
  <el-form label-width="100px" size="small">
    <!-- 设备标识 -->
    <el-divider content-position="left">📋 设备标识</el-divider>
    <el-form-item label="设备名称">
      <el-input v-model="form.hostname" placeholder="ROS-Gateway" />
      <div class="ros-hint">对应命令: /system identity set name=xxx</div>
    </el-form-item>

    <!-- 远程管理 -->
    <el-divider content-position="left">🔑 远程管理</el-divider>
    <el-form-item label="SSH 服务">
      <el-switch v-model="form.enable_ssh" active-text="启用" inactive-text="禁用" />
    </el-form-item>
    <el-form-item label="SSH 端口">
      <el-input-number v-model="form.ssh_port" :min="1" :max="65535" />
    </el-form-item>
    <el-form-item label="管理 IP 限制">
      <el-input v-model="form.ssh_allow_ip" placeholder="例如: 192.168.1.0/24（留空=不限制）" />
      <div class="ros-hint">对应命令: /ip service set ssh address=xxx</div>
    </el-form-item>
    <el-form-item label="WinBox 访问">
      <el-switch v-model="form.enable_winbox" active-text="允许" inactive-text="禁用" />
    </el-form-item>
    <el-form-item label="禁用服务">
      <el-checkbox-group v-model="form.disable_services">
        <el-checkbox label="telnet" />
        <el-checkbox label="ftp" />
        <el-checkbox label="www" />
        <el-checkbox label="api" />
      </el-checkbox-group>
      <div class="ros-hint">建议全部禁用，仅保留 SSH 和 WinBox</div>
    </el-form-item>

    <!-- 用户 -->
    <el-divider content-position="left">👤 管理员用户</el-divider>
    <el-form-item label="用户名">
      <el-input v-model="form.admin_user" placeholder="admin" />
    </el-form-item>
    <el-form-item label="密码">
      <el-input v-model="form.admin_password" placeholder="最低8位" show-password />
    </el-form-item>
    <el-form-item label="权限组">
      <el-select v-model="form.admin_group" style="width:100%">
        <el-option label="full（完全控制）" value="full" />
        <el-option label="read（只读）" value="read" />
        <el-option label="write（读写）" value="write" />
      </el-select>
    </el-form-item>

    <!-- 时间/DNS -->
    <el-divider content-position="left">🕐 时间与 DNS</el-divider>
    <el-form-item label="NTP 服务器">
      <el-input v-model="form.ntp_server" placeholder="119.28.183.184" />
      <div class="ros-hint">/system ntp client set enabled=yes primary-ntp=xxx</div>
    </el-form-item>
    <el-form-item label="时区">
      <el-input v-model="form.timezone" placeholder="Asia/Shanghai" />
    </el-form-item>
    <el-form-item label="DNS 服务器">
      <el-input v-model="form.dns_servers" placeholder="8.8.8.8,114.114.114.114" />
      <div class="ros-hint">/ip dns set servers=xxx</div>
    </el-form-item>
    <el-form-item label="启用 DNS 缓存">
      <el-switch v-model="form.dns_cache" />
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch, nextTick } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

const form = reactive({
  hostname: 'ROS-Gateway',
  enable_ssh: true,
  ssh_port: 22,
  ssh_allow_ip: '',
  enable_winbox: true,
  disable_services: ['telnet', 'ftp', 'www', 'api'],
  admin_user: 'admin',
  admin_password: '',
  admin_group: 'full',
  ntp_server: '',
  timezone: 'Asia/Shanghai',
  dns_servers: '',
  dns_cache: true,
})

// 从 props 初始化（syncing 锁防回环，不能用 once:true）
let _bsyncing = false
watch(() => props.modelValue, (v) => {
  if (_bsyncing || !v || Object.keys(v).length === 0) return
  _bsyncing = true
  const topKeys = ['hostname','password','enable_ssh','ssh_port','enable_telnet','enable_ntp','ntp_servers','enable_snmp','snmp_read','snmp_write','username','user_level','disable_services','router_id']
  topKeys.forEach(k => { if (k in v) (form as any)[k] = v[k] })
  if (v.disable_services && Array.isArray(v.disable_services)) {
    form.disable_services.length = 0; form.disable_services.push(...v.disable_services)
  }
  nextTick(() => { _bsyncing = false })
}, { immediate: true })

// 轻量防抖 emit
let _bt: ReturnType<typeof setTimeout> | null = null
function emitUpdate() {
  if (_bt) clearTimeout(_bt)
  _bt = setTimeout(() => emit('update:modelValue', { ...form }), 200)
}
// 只 watch 顶层属性（不用 deep）
watch(() => ({ ...form }), () => emitUpdate())
</script>

<style scoped>
.ros-hint { font-size: 11px; color: #909399; margin-top: 4px; line-height: 1.4; }
</style>

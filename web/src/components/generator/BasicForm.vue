<template>
  <el-form label-width="90px" size="small" @change="emitUpdate">
    <el-divider content-position="left">设备信息</el-divider>
    <el-form-item label="主机名">
      <el-input v-model="form.hostname" placeholder="SW-CORE-01" />
    </el-form-item>

    <el-divider content-position="left">登录认证</el-divider>
    <el-form-item label="密码">
      <el-input v-model="form.password" placeholder="明文密码" />
    </el-form-item>
    <el-form-item label="启用 SSH">
      <el-switch v-model="form.enable_ssh" />
    </el-form-item>
    <template v-if="form.enable_ssh">
      <el-form-item label="SSH 端口">
        <el-input-number v-model="form.ssh_port" :min="1" :max="65535" />
      </el-form-item>
    </template>
    <el-form-item label="启用 Telnet">
      <el-switch v-model="form.enable_telnet" />
    </el-form-item>

    <el-divider content-position="left">用户管理</el-divider>
    <el-form-item label="用户名">
      <el-input v-model="form.username" placeholder="admin" />
    </el-form-item>
    <el-form-item label="用户密码">
      <el-input v-model="form.user_password" placeholder="用户密码" show-password />
    </el-form-item>
    <el-form-item label="权限级别">
      <el-input-number v-model="form.user_level" :min="0" :max="15" />
    </el-form-item>

    <el-divider content-position="left">NTP 时间同步</el-divider>
    <el-form-item label="启用 NTP">
      <el-switch v-model="form.enable_ntp" />
    </el-form-item>
    <template v-if="form.enable_ntp">
      <el-form-item label="NTP 服务器">
        <el-input v-model="form.ntp_servers" placeholder="1.1.1.1, 2.2.2.2" />
      </el-form-item>
    </template>

    <el-divider content-position="left">SNMP</el-divider>
    <el-form-item label="启用 SNMP">
      <el-switch v-model="form.enable_snmp" />
    </el-form-item>
    <template v-if="form.enable_snmp">
      <el-form-item label="读团体字">
        <el-input v-model="form.snmp_read" placeholder="public" />
      </el-form-item>
      <el-form-item label="写团体字">
        <el-input v-model="form.snmp_write" placeholder="private" />
      </el-form-item>
    </template>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const form = reactive({
    hostname: props.modelValue.hostname || '',
    password: props.modelValue.password || '',
    enable_ssh: props.modelValue.enable_ssh || false,
    ssh_port: props.modelValue.ssh_port || 22,
    enable_telnet: props.modelValue.enable_telnet || false,
    username: props.modelValue.username || 'admin',
    user_password: props.modelValue.user_password || '',
    user_level: props.modelValue.user_level || 15,
    enable_ntp: props.modelValue.enable_ntp || false,
    ntp_servers: props.modelValue.ntp_servers || '',
    enable_snmp: props.modelValue.enable_snmp || false,
    snmp_read: props.modelValue.snmp_read || 'public',
    snmp_write: props.modelValue.snmp_write || '',
})

function emitUpdate() {
    // 构建 API 所需的 params 结构
    const params: Record<string, any> = {}
    if (form.hostname) params.hostname = form.hostname
    if (form.password) params.password = { value: form.password, encrypted: false }
    params.enable_ssh = form.enable_ssh
    if (form.enable_ssh) params.ssh = { port: form.ssh_port }
    params.enable_telnet = form.enable_telnet
    if (form.username) {
        params.user = { username: form.username, password: form.user_password, level: form.user_level }
    }
    if (form.enable_ntp && form.ntp_servers) {
        params.ntp = {
            servers: form.ntp_servers.split(',').map(s => ({ ip: s.trim() })),
        }
    }
    if (form.enable_snmp) {
        params.snmp = {
            version: 'v2c',
            community_read: form.snmp_read,
            community_write: form.snmp_write || undefined,
        }
    }
    emit('update:modelValue', params)
}

watch(() => props.modelValue, () => {
    // 外部修改时同步（如切换厂商清空）
}, { deep: true })
</script>

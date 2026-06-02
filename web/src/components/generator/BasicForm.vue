<template>
  <el-form label-width="90px" size="small" @change="emitUpdate">
    <el-divider content-position="left">设备信息</el-divider>
    <el-form-item label="主机名">
      <el-input v-model="form.hostname" placeholder="SW-CORE-01" />
    </el-form-item>
    <el-form-item v-if="props.vendor" label="设备型号">
      <el-select v-model="form.deviceModel" filterable placeholder="选型号（可搜索）" style="width:100%">
        <el-option-group v-for="g in deviceModels" :key="g.label" :label="g.label">
          <el-option v-for="m in g.options" :key="m.value" :label="m.label" :value="m.value" />
        </el-option-group>
      </el-select>
      <span style="font-size:11px;color:#909399">选对型号可确保命令100%兼容你的设备</span>
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
import { reactive, watch, computed } from 'vue'

const props = defineProps<{ modelValue: Record<string, any>; vendor?: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

// 设备型号库（用户思维：按系列分组，带描述）
const deviceModels = computed(() => {
  const m: Record<string, {label:string, options:{label:string;value:string}[]}[]> = {
    huawei: [
      { label:'AR 企业路由器', options:[
        {label:'AR1200 系列（中小分支）',value:'AR1200'},{label:'AR2200/AR3200 系列（中大型）',value:'AR2200'},
        {label:'AR6300 系列（高性能）',value:'AR6300'},{label:'NE 系列（运营商级）',value:'NE'}]},
      { label:'S 交换机', options:[
        {label:'S5700 系列（接入）',value:'S5700'},{label:'S6700 系列（汇聚）',value:'S6700'},
        {label:'S7700/12700（核心）',value:'S7700'}]},
    ],
    h3c: [
      { label:'MSR 路由器', options:[
        {label:'MSR 2600/3600 系列',value:'MSR2600'},{label:'MSR 5600 系列（高端）',value:'MSR5600'}]},
      { label:'S 交换机', options:[
        {label:'S5500/S5560 系列',value:'S5500'},{label:'S6800/S7500 系列',value:'S6800'}]},
    ],
    ruijie: [
      { label:'RSR 路由器', options:[
        {label:'RSR10/20 系列',value:'RSR10'},{label:'RSR30/50 系列',value:'RSR30'},{label:'RSR77 系列',value:'RSR77'}]},
      { label:'S 交换机', options:[
        {label:'S29 系列（接入）',value:'RG-S29'},{label:'S57 系列（汇聚）',value:'RG-S57'},{label:'S86 系列（核心）',value:'RG-S86'}]},
    ],
    maipu: [
      { label:'MP 路由器', options:[
        {label:'MP1800/2800 系列',value:'MP1800'},{label:'MP3800/4800 系列',value:'MP3800'}]},
      { label:'S 交换机', options:[
        {label:'S3000 系列（接入）',value:'S3000'},{label:'S5000 系列（核心）',value:'S5000'}]},
    ],
  }
  return m[props.vendor || ''] || []
})

const form = reactive({
    hostname: props.modelValue.hostname || '',
    deviceModel: props.modelValue.deviceModel || '',
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
    if (form.deviceModel) params.deviceModel = form.deviceModel
    if (form.password) params.password = { value: form.password, encrypted: false }
    params.enable_ssh = form.enable_ssh
    if (form.enable_ssh) params.ssh = { port: form.ssh_port }
    params.enable_telnet = form.enable_telnet
    if (form.username) {
        params.user = { username: form.username, password: form.user_password, level: form.user_level }
    }
    if (form.enable_ntp && form.ntp_servers) {
        params.ntp = {
            servers: form.ntp_servers.split(',').map((s: string) => ({ ip: s.trim() })),
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

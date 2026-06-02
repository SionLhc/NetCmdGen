<template>
  <el-form label-width="120px" size="default">
    <el-form-item label="启用DHCP">
      <el-switch v-model="form.enable_dhcp" active-text="开启" inactive-text="关闭" />
    </el-form-item>
    <template v-if="form.enable_dhcp">
      <el-divider content-position="left">地址池</el-divider>
      <el-form-item label="网络地址">
        <el-input v-model="form.network" placeholder="192.168.1.0" style="width:180px" />
        <span style="margin:0 4px">/</span>
        <el-input-number v-model="form.mask_len" :min="8" :max="30" style="width:100px" />
        <span style="font-size:12px;color:#909399;margin-left:8px">子网掩码位数，常用 24</span>
      </el-form-item>
      <el-form-item label="网关地址">
        <el-input v-model="form.gateway" placeholder="192.168.1.1" style="width:180px" />
        <span style="font-size:12px;color:#909399;margin-left:8px">通常是路由器LAN口IP</span>
      </el-form-item>
      <el-form-item label="DNS服务器">
        <el-input v-model="form.dns1" placeholder="223.5.5.5" style="width:160px" />
        <el-input v-model="form.dns2" placeholder="114.114.114.114" style="width:160px;margin-left:8px" />
        <span style="font-size:12px;color:#909399;margin-left:8px">默认阿里DNS + 114DNS</span>
      </el-form-item>
      <el-form-item label="租约时间">
        <el-select v-model="form.lease" style="width:140px">
          <el-option label="1 天" value="day 0 hour 1" />
          <el-option label="3 天" value="day 3 hour 0" />
          <el-option label="7 天" value="day 7 hour 0" />
          <el-option label="30 天" value="day 30 hour 0" />
        </el-select>
      </el-form-item>

      <el-divider content-position="left">排除地址（预留给服务器/打印机等固定IP设备）</el-divider>
      <div v-for="(item,i) in form.excluded" :key="i" style="display:flex;gap:8px;align-items:center;margin-bottom:6px">
        <el-input v-model="item.start" placeholder="起始IP 192.168.1.10" style="width:190px" size="default" />
        <span>→</span>
        <el-input v-model="item.end" placeholder="结束IP 192.168.1.20" style="width:190px" size="default" />
        <el-button link type="danger" @click="form.excluded.splice(i,1)" :disabled="form.excluded.length<=1">✕</el-button>
      </div>
      <el-button size="small" @click="form.excluded.push({start:'',end:''})" style="margin-top:4px">+ 添加排除范围</el-button>
    </template>

    <el-divider content-position="left" v-if="form.enable_dhcp">高级选项</el-divider>
    <el-form-item label="域名" v-if="form.enable_dhcp">
      <el-input v-model="form.domain" placeholder="company.local（可不填）" style="width:200px" />
    </el-form-item>
    <el-form-item label="NTP服务器" v-if="form.enable_dhcp">
      <el-input v-model="form.ntp_server" placeholder="192.168.1.1（可不填，使用路由器做NTP）" style="width:200px" />
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string,any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string,any>] }>()

const form = reactive({
  enable_dhcp: props.modelValue?.enable_dhcp ?? true,
  network: props.modelValue?.network || '192.168.1.0',
  mask_len: props.modelValue?.mask_len ?? 24,
  gateway: props.modelValue?.gateway || '192.168.1.1',
  dns1: props.modelValue?.dns1 || '223.5.5.5',
  dns2: props.modelValue?.dns2 || '114.114.114.114',
  lease: props.modelValue?.lease || 'day 0 hour 1',
  domain: props.modelValue?.domain || '',
  ntp_server: props.modelValue?.ntp_server || '',
  excluded: props.modelValue?.excluded || [{ start: '192.168.1.10', end: '192.168.1.50' }],
})

watch(() => form, () => emit('update:modelValue', { ...form }), { deep: true })
</script>

<template>
  <div class="ros-dhcp-form">
    <div class="step-card">
      <div class="step-title">DHCP 地址池</div>
      <p class="step-hint">为 LAN 接口创建 DHCP 地址池，自动分配 IP 给下游设备</p>

      <div v-for="(line, idx) in dhcpLines" :key="idx" class="dhcp-line">
        <div class="line-header">
          <span class="line-num">地址池 {{ idx + 1 }}</span>
          <el-button link type="danger" size="small" @click="removeLine(idx)">删除</el-button>
        </div>
        <el-row :gutter="12">
          <el-col :span="6">
            <div class="field"><label>接口</label>
              <el-input v-model="line.interface" placeholder="bridge1" size="small" /></div>
          </el-col>
          <el-col :span="6">
            <div class="field"><label>网络地址</label>
              <el-input v-model="line.network" placeholder="192.168.1.0" size="small" /></div>
          </el-col>
          <el-col :span="6">
            <div class="field"><label>子网掩码</label>
              <el-select v-model="line.mask" size="small" style="width:100%">
                <el-option v-for="m in masks" :key="m" :label="`/${m}`" :value="String(m)" />
              </el-select></div>
          </el-col>
          <el-col :span="6">
            <div class="field"><label>网关</label>
              <el-input v-model="line.gateway" placeholder="192.168.1.1" size="small" /></div>
          </el-col>
        </el-row>
        <el-row :gutter="12" style="margin-top:8px">
          <el-col :span="6">
            <div class="field"><label>DNS 服务器</label>
              <el-input v-model="line.dns" placeholder="8.8.8.8" size="small" /></div>
          </el-col>
          <el-col :span="6">
            <div class="field"><label>起始 IP</label>
              <el-input v-model="line.rangeStart" placeholder="192.168.1.100" size="small" /></div>
          </el-col>
          <el-col :span="6">
            <div class="field"><label>结束 IP</label>
              <el-input v-model="line.rangeEnd" placeholder="192.168.1.200" size="small" /></div>
          </el-col>
          <el-col :span="6">
            <div class="field"><label>租期</label>
              <el-input v-model="line.lease" placeholder="1d" size="small" /></div>
          </el-col>
        </el-row>
        <el-row :gutter="12" style="margin-top:8px">
          <el-col :span="12">
            <div class="field"><label>静态绑定（可选）</label>
              <el-input v-model="line.staticBindings" placeholder="MAC=IP, 如 AA:BB:CC:DD:EE:FF=192.168.1.50" size="small" /></div>
          </el-col>
        </el-row>
      </div>

      <el-button type="primary" link size="small" @click="addLine" style="margin-top:8px">+ 添加地址池</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, ref } from 'vue'

interface DhcpLine {
  interface: string
  network: string
  mask: string
  gateway: string
  dns: string
  rangeStart: string
  rangeEnd: string
  lease: string
  staticBindings: string
}

const props = defineProps<{ modelValue?: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const masks = [24, 23, 22, 21, 20, 19, 18, 17, 16, 8]

const dhcpLines = ref<DhcpLine[]>([])

/* 从已有数据初始化 */
function initFromProps(val: Record<string, any>) {
  const lines = val?.dhcpLines || val?.lines
  if (lines && Array.isArray(lines) && lines.length > 0) {
    dhcpLines.value = lines.map(l => ({
      interface: l.interface || 'bridge1',
      network: l.network || '',
      mask: l.mask || '24',
      gateway: l.gateway || '',
      dns: l.dns || '8.8.8.8',
      rangeStart: l.rangeStart || l.startIp || '',
      rangeEnd: l.rangeEnd || l.endIp || '',
      lease: l.lease || '1d',
      staticBindings: l.staticBindings || '',
    }))
  } else {
    dhcpLines.value = [
      { interface:'bridge1', network:'192.168.88.0', mask:'24', gateway:'192.168.88.1', dns:'8.8.8.8', rangeStart:'192.168.88.100', rangeEnd:'192.168.88.200', lease:'1d', staticBindings:'' }
    ]
  }
  emitUpdate()
}

function addLine() {
  dhcpLines.value.push({ interface:'bridge1', network:'', mask:'24', gateway:'', dns:'8.8.8.8', rangeStart:'', rangeEnd:'', lease:'1d', staticBindings:'' })
  emitUpdate()
}
function removeLine(idx: number) {
  dhcpLines.value.splice(idx, 1)
  emitUpdate()
}

function emitUpdate() {
  emit('update:modelValue', { dhcpLines: [...dhcpLines.value] })
}

watch(() => props.modelValue, (v) => { if (v) initFromProps(v) }, { immediate: true })
watch(dhcpLines, () => emitUpdate(), { deep: true })
</script>

<style scoped>
.ros-dhcp-form { display:flex; flex-direction:column; gap:16px }
.step-card { background:#fafbfc; border:1px solid #ebeef5; border-radius:10px; padding:14px }
.step-title { font-size:14px; font-weight:600; color:#1e293b }
.step-hint { font-size:12px; color:#94a3b8; margin:4px 0 10px }
.dhcp-line { border:1px dashed #e5e7eb; border-radius:8px; padding:12px; margin-bottom:10px; background:#fff }
.line-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px }
.line-num { font-size:13px; font-weight:600; color:#6366f1 }
.field { margin-bottom:4px }
.field label { font-size:11px; color:#94a3b8; display:block; margin-bottom:2px }
</style>

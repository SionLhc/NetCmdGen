<template>
  <div class="ros-nat-form">
    <div class="step-card">
      <div class="step-title">NAT 端口映射 (DST-NAT)</div>
      <p class="step-hint">将公网 IP 的端口映射到内网服务器（如 80→内网 Web 服务器）</p>
      <div v-for="(r, idx) in natRules" :key="idx" class="nat-rule">
        <div class="rule-header">
          <span class="rule-num">规则 {{ idx + 1 }}</span>
          <el-button link type="danger" size="small" @click="removeRule(idx)">删除</el-button>
        </div>
        <el-row :gutter="10">
          <el-col :span="5"><div class="field"><label>协议</label>
            <el-select v-model="r.protocol" size="small"><el-option v-for="p in ['tcp','udp','both']" :key="p" :label="p" :value="p"/></el-select></div></el-col>
          <el-col :span="6"><div class="field"><label>目标端口</label>
            <el-input v-model="r.dstPort" placeholder="80" size="small" /></div></el-col>
          <el-col :span="6"><div class="field"><label>内网 IP</label>
            <el-input v-model="r.toAddress" placeholder="192.168.1.10" size="small" /></div></el-col>
          <el-col :span="5"><div class="field"><label>映射端口</label>
            <el-input v-model="r.toPorts" placeholder="80" size="small" /></div></el-col>
        </el-row>
        <el-row :gutter="10" style="margin-top:6px">
          <el-col :span="6"><div class="field"><label>入接口</label>
            <el-input v-model="r.inInterface" placeholder="ether1" size="small" /></div></el-col>
          <el-col :span="12"><div class="field"><label>备注</label>
            <el-input v-model="r.comment" placeholder="Web服务器映射" size="small" /></div></el-col>
        </el-row>
      </div>
      <el-button type="primary" link size="small" @click="addRule">+ 添加映射</el-button>
    </div>

    <div class="step-card">
      <div class="step-title">源 NAT 伪装 (SNAT/Masquerade)</div>
      <p class="step-hint">内网设备上网时自动将源 IP 替换为公网 IP（通常无需修改）</p>
      <el-checkbox v-model="enableMasquerade" size="small">启用 NAT 伪装 (masquerade)</el-checkbox>
      <div style="margin-top:8px">
        <span class="field"><label>出口接口</label>
          <el-input v-model="masqInterface" placeholder="ether1" size="small" style="width:180px" /></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, ref, reactive } from 'vue'

interface NatRule {
  protocol: string; dstPort: string; toAddress: string; toPorts: string
  inInterface: string; comment: string
}

const props = defineProps<{ modelValue?: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const natRules = ref<NatRule[]>([])
const enableMasquerade = ref(true)
const masqInterface = ref('ether1')

function initFromProps(val: Record<string, any>) {
  const rules = val?.rules || val?.natRules || val?.natList
  if (rules && Array.isArray(rules) && rules.length > 0) {
    natRules.value = rules.map(r => ({
      protocol: r.protocol || 'tcp', dstPort: r.dstPort || r.externalPort || r.ext_port || '',
      toAddress: r.toAddress || r.internalIp || r.int_ip || '', toPorts: r.toPorts || r.internalPort || r.int_port || '',
      inInterface: r.inInterface || 'ether1', comment: r.comment || r.description || '',
    }))
  }
  enableMasquerade.value = val?.enableMasquerade !== false
  masqInterface.value = val?.masqInterface || 'ether1'
  emitUpdate()
}

function addRule() {
  natRules.value.push({ protocol:'tcp', dstPort:'', toAddress:'', toPorts:'', inInterface:'ether1', comment:'' })
  emitUpdate()
}
function removeRule(idx: number) {
  natRules.value.splice(idx, 1); emitUpdate()
}

function emitUpdate() {
  emit('update:modelValue', {
    rules: [...natRules.value],
    enableMasquerade: enableMasquerade.value,
    masqInterface: masqInterface.value,
  })
}

watch(() => props.modelValue, (v) => { if (v) initFromProps(v) }, { immediate: true })
watch([natRules, enableMasquerade, masqInterface], () => emitUpdate(), { deep: true })
</script>

<style scoped>
.ros-nat-form { display:flex; flex-direction:column; gap:16px }
.step-card { background:#fafbfc; border:1px solid #ebeef5; border-radius:10px; padding:14px }
.step-title { font-size:14px; font-weight:600; color:#1e293b }
.step-hint { font-size:12px; color:#94a3b8; margin:4px 0 10px }
.nat-rule { border:1px dashed #e5e7eb; border-radius:8px; padding:10px; margin-bottom:8px; background:#fff }
.rule-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px }
.rule-num { font-size:13px; font-weight:600; color:#f59e0b }
.field { margin-bottom:4px }
.field label { font-size:11px; color:#94a3b8; display:block; margin-bottom:2px }
</style>

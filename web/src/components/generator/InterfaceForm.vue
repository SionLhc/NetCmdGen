<template>
  <el-form label-width="90px" size="small" @change="emitUpdate">
    <!-- Eth-Trunk 聚合 -->
    <el-divider content-position="left">链路聚合</el-divider>
    <div v-for="(trunk, idx) in ethTrunks" :key="'et'+idx" class="sec-section">
      <div class="sec-header">
        <span>Eth-Trunk {{ trunk.trunk_id }}</span>
        <el-button text type="danger" size="small" @click="ethTrunks.splice(idx,1);emitUpdate()">删除</el-button>
      </div>
      <el-row :gutter="6">
        <el-col :span="6"><el-input-number v-model="trunk.trunk_id" :min="1" @change="emitUpdate" /></el-col>
        <el-col :span="8"><el-input v-model="trunk.description" placeholder="描述" @change="emitUpdate" /></el-col>
        <el-col :span="10"><el-input v-model="trunkMode" placeholder="成员接口(逗号分隔)" @change="updateTrunkMembers" /></el-col>
      </el-row>
    </div>
    <el-button size="small" plain @click="ethTrunks.push({trunk_id:1,description:'',members:[]});emitUpdate()" style="width:100%">+ 添加聚合组</el-button>

    <!-- LLDP -->
    <el-divider content-position="left">LLDP</el-divider>
    <el-form-item label="启用 LLDP">
      <el-switch v-model="enableLldp" @change="emitUpdate" />
    </el-form-item>

    <!-- PoE -->
    <el-divider content-position="left">PoE 供电</el-divider>
    <div v-for="(poe, idx) in poeInterfaces" :key="'poe'+idx" class="sec-section">
      <el-row :gutter="6">
        <el-col :span="10"><el-input v-model="poe.interface" placeholder="接口" @change="emitUpdate" /></el-col>
        <el-col :span="6">
          <el-select v-model="poe.priority" @change="emitUpdate">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
          </el-select>
        </el-col>
        <el-col :span="6"><el-input-number v-model="poe.power" :min="0" :max="15400" placeholder="功率" @change="emitUpdate" /></el-col>
        <el-col :span="2"><el-button text type="danger" @click="poeInterfaces.splice(idx,1);emitUpdate()">✕</el-button></el-col>
      </el-row>
    </div>
    <el-button size="small" plain @click="poeInterfaces.push({interface:'GigabitEthernet0/0/1',enable:true,priority:'low',power:15400});emitUpdate()" style="width:100%">+ 添加 PoE 接口</el-button>

    <!-- 环路检测 -->
    <el-divider content-position="left">环路检测</el-divider>
    <el-form-item label="启用检测">
      <el-switch v-model="loopDetect.enable" @change="emitUpdate" />
    </el-form-item>
    <template v-if="loopDetect.enable">
      <el-form-item label="检测间隔">
        <el-input-number v-model="loopDetect.interval" :min="1" :max="300" @change="emitUpdate" />
      </el-form-item>
      <el-form-item label="处理动作">
        <el-select v-model="loopDetect.action" @change="emitUpdate">
          <el-option label="阻塞" value="block" />
          <el-option label="关闭" value="shutdown" />
          <el-option label="告警" value="alarm" />
        </el-select>
      </el-form-item>
    </template>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const trunkMode = ref('')
const enableLldp = ref(props.modelValue.lldp?.enable ?? false)

const ethTrunks = reactive<Array<any>>(props.modelValue.eth_trunks || [])
const poeInterfaces = reactive<Array<any>>(props.modelValue.poe_interfaces || [])
const loopDetect = reactive(props.modelValue.loop_detect || { enable: false, interval: 5, action: 'block' })

function updateTrunkMembers() {
    if (ethTrunks.length > 0) {
        const last = ethTrunks[ethTrunks.length - 1]
        last.members = trunkMode.value.split(',').map((s: string) => s.trim()).filter(Boolean)
        emitUpdate()
    }
}

function emitUpdate() {
    const params: Record<string, any> = {}
    if (ethTrunks.length > 0) params.eth_trunks = [...ethTrunks]
    if (enableLldp.value) params.lldp = { enable: true }
    if (poeInterfaces.length > 0) params.poe_interfaces = [...poeInterfaces]
    if (loopDetect.enable) params.loop_detect = { ...loopDetect }
    emit('update:modelValue', params)
}

watch([ethTrunks, poeInterfaces, loopDetect], emitUpdate, { deep: true })
</script>

<style scoped>
.sec-section { margin-bottom: 10px; padding: 8px; background: #fff; border-radius: 6px; border: 1px solid #ebeef5; }
.sec-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 12px; color: #606266; }
</style>

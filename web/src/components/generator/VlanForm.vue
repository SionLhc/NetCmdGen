<template>
  <el-form label-width="90px" size="small" @change="emitUpdate">
    <el-divider content-position="left">VLAN 列表</el-divider>
    <div v-for="(vlan, idx) in vlans" :key="idx" class="vlan-row">
      <el-row :gutter="6" align="middle">
        <el-col :span="8">
          <el-input-number v-model="vlan.id" :min="1" :max="4094" placeholder="ID" controls-position="right" />
        </el-col>
        <el-col :span="12">
          <el-input v-model="vlan.name" placeholder="VLAN 名称" />
        </el-col>
        <el-col :span="4">
          <el-button text type="danger" @click="removeVlan(idx)">✕</el-button>
        </el-col>
      </el-row>
    </div>
    <el-button size="small" type="primary" plain @click="addVlan" style="width:100%">+ 添加 VLAN</el-button>

    <el-divider content-position="left">接口分配</el-divider>
    <div v-for="(iface, idx) in interfaces" :key="idx" class="iface-row">
      <el-row :gutter="6" align="middle">
        <el-col :span="10">
          <el-input v-model="iface.interface" placeholder="接口名" />
        </el-col>
        <el-col :span="6">
          <el-select v-model="iface.type">
            <el-option label="access" value="access" />
            <el-option label="trunk" value="trunk" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-input-number v-model="iface.vlan_id" :min="1" :max="4094" controls-position="right" />
        </el-col>
        <el-col :span="3">
          <el-button text type="danger" @click="removeIface(idx)">✕</el-button>
        </el-col>
      </el-row>
    </div>
    <el-button size="small" type="primary" plain @click="addIface" style="width:100%">+ 添加接口</el-button>

    <el-divider content-position="left">VLANIF 接口</el-divider>
    <div v-for="(vf, idx) in vlanifs" :key="idx" class="vlanif-row">
      <el-row :gutter="6">
        <el-col :span="6">
          <el-input-number v-model="vf.vlan_id" :min="1" :max="4094" controls-position="right" />
        </el-col>
        <el-col :span="8">
          <el-input v-model="vf.ip_address" placeholder="IP 地址" />
        </el-col>
        <el-col :span="7">
          <el-input v-model="vf.mask" placeholder="掩码" />
        </el-col>
        <el-col :span="3">
          <el-button text type="danger" @click="removeVlanif(idx)">✕</el-button>
        </el-col>
      </el-row>
    </div>
    <el-button size="small" type="primary" plain @click="addVlanif" style="width:100%">+ 添加 VLANIF</el-button>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

interface VlanItem { id: number; name: string }
interface IfaceItem { interface: string; type: string; vlan_id: number }
interface VlanifItem { vlan_id: number; ip_address: string; mask: string }

const vlans = reactive<VlanItem[]>(
    props.modelValue.vlans || [{ id: 10, name: 'Office' }]
)
const interfaces = reactive<IfaceItem[]>(
    props.modelValue.interfaces || [{ interface: 'GigabitEthernet0/0/1', type: 'access', vlan_id: 10 }]
)
const vlanifs = reactive<VlanifItem[]>(
    props.modelValue.vlanifs || []
)

function addVlan() { vlans.push({ id: 1, name: '' }) }
function removeVlan(idx: number) { vlans.splice(idx, 1); emitUpdate() }
function addIface() { interfaces.push({ interface: '', type: 'access', vlan_id: 1 }) }
function removeIface(idx: number) { interfaces.splice(idx, 1); emitUpdate() }
function addVlanif() { vlanifs.push({ vlan_id: 1, ip_address: '', mask: '255.255.255.0' }) }
function removeVlanif(idx: number) { vlanifs.splice(idx, 1); emitUpdate() }

function emitUpdate() {
    const params: Record<string, any> = {}
    // 华为用扁平结构，其他厂商用结构化结构
    params.vlans = [...vlans]
    params.interfaces = [...interfaces]
    if (vlanifs.length > 0) params.vlanifs = [...vlanifs]
    emit('update:modelValue', params)
}

watch([vlans, interfaces, vlanifs], emitUpdate, { deep: true })
</script>

<style scoped>
.vlan-row, .iface-row, .vlanif-row {
    margin-bottom: 8px;
    padding: 8px;
    background: #fff;
    border-radius: 6px;
    border: 1px solid #ebeef5;
}
</style>

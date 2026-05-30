<template>
  <el-form :model="formData" label-width="100px" size="small">
    <el-form-item label="设备名称">
      <el-input v-model="formData.hostname" placeholder="SW-CORE-01" />
    </el-form-item>
    
    <el-form-item label="厂商">
      <el-select v-model="formData.vendor" style="width: 100%">
        <el-option label="华为 Huawei" value="huawei" />
        <el-option label="H3C 华三" value="h3c" />
        <el-option label="锐捷 Ruijie" value="ruijie" />
        <el-option label="思科 Cisco" value="cisco" />
      </el-select>
    </el-form-item>
    
    <el-form-item label="角色">
      <el-tag type="primary">核心交换机</el-tag>
    </el-form-item>
    
    <el-divider content-position="left">网络配置</el-divider>
    
    <el-form-item label="管理网段">
      <el-input v-model="formData.mgmtSubnet" placeholder="192.168.1.0/24" />
    </el-form-item>
    
    <el-form-item label="STP优先级">
      <el-input-number v-model="formData.stpPriority" :min="0" :max="65535" :step="4096" style="width: 100%" />
    </el-form-item>
    
    <el-form-item label="OSPF Router-ID">
      <el-input v-model="formData.ospfRouterId" placeholder="1.1.1.1" />
    </el-form-item>
    
    <el-divider content-position="left">端口配置</el-divider>
    
    <el-form-item label="上行接口数">
      <el-input-number v-model="formData.uplinkPorts" :min="1" :max="8" style="width: 100%" />
    </el-form-item>
    
    <el-form-item label="下行接口数">
      <el-input-number v-model="formData.downlinkPorts" :min="2" :max="48" style="width: 100%" />
    </el-form-item>
    
    <el-form-item>
      <el-button type="primary" @click="handleSave" style="width: 100%">保存属性</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

const props = defineProps<{
  node: any
}>()

const emit = defineEmits<{
  update: [data: any]
}>()

const formData = ref({
  hostname: '',
  vendor: 'huawei',
  mgmtSubnet: '192.168.1.0/24',
  stpPriority: 4096,
  ospfRouterId: '',
  uplinkPorts: 2,
  downlinkPorts: 4,
})

// 初始化表单数据
onMounted(() => {
  const data = props.node.getData() || {}
  formData.value = {
    hostname: data.hostname || props.node.getAttrByPath('text/text') || props.node.id,
    vendor: data.vendor || 'huawei',
    mgmtSubnet: data.mgmtSubnet || '192.168.1.0/24',
    stpPriority: data.stpPriority || 4096,
    ospfRouterId: data.ospfRouterId || '',
    uplinkPorts: data.uplinkPorts || 2,
    downlinkPorts: data.downlinkPorts || 4,
  }
})

function handleSave() {
  emit('update', {
    ...formData.value,
    role: 'core-switch',
    type: 'core-switch',
  })
}
</script>

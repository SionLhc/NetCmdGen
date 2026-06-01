<template>
  <el-form :model="formData" label-width="100px" size="small">
    <el-form-item label="设备名称">
      <el-input v-model="formData.hostname" placeholder="SW-ACCESS-01" />
    </el-form-item>
    <el-form-item label="厂商">
      <el-select v-model="formData.vendor" style="width: 100%">
        <el-option label="华为 Huawei" value="huawei" />
        <el-option label="H3C 华三" value="h3c" />
        <el-option label="锐捷 Ruijie" value="ruijie" />
      </el-select>
    </el-form-item>
    <el-form-item label="角色">
      <el-tag type="success">接入交换机</el-tag>
    </el-form-item>
    <el-form-item label="管理IP">
      <el-input v-model="formData.mgmtIp" placeholder="自动分配" disabled />
    </el-form-item>
    <el-form-item label="默认VLAN">
      <el-input-number v-model="formData.defaultVlan" :min="1" :max="4094" style="width: 100%" />
    </el-form-item>
    <el-form-item label="接入端口数">
      <el-input-number v-model="formData.accessPorts" :min="8" :max="48" style="width: 100%" />
    </el-form-item>
    <el-form-item label="PoE支持">
      <el-switch v-model="formData.poeEnabled" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleSave" style="width: 100%">保存属性</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = defineProps<{ node: any }>()
const emit = defineEmits<{ update: [data: any] }>()

const formData = ref({
  hostname: '',
  vendor: 'huawei',
  mgmtIp: '',
  defaultVlan: 10,
  accessPorts: 24,
  poeEnabled: false,
})

onMounted(() => {
  const data = props.node.getData() || {}
  formData.value = {
    hostname: data.hostname || props.node.getAttrByPath('text/text') || props.node.id,
    vendor: data.vendor || 'huawei',
    mgmtIp: data.mgmtIp || '',
    defaultVlan: data.defaultVlan || 10,
    accessPorts: data.accessPorts || 24,
    poeEnabled: data.poeEnabled || false,
  }
})

function handleSave() {
  emit('update', { ...formData.value, role: 'access-switch', type: 'access-switch' })
}
</script>

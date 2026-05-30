<template>
  <el-form :model="formData" label-width="100px" size="small">
    <el-form-item label="设备名称">
      <el-input v-model="formData.hostname" placeholder="RT-EDGE-01" />
    </el-form-item>
    <el-form-item label="厂商">
      <el-select v-model="formData.vendor" style="width: 100%">
        <el-option label="华为 Huawei" value="huawei" />
        <el-option label="H3C 华三" value="h3c" />
        <el-option label="思科 Cisco" value="cisco" />
      </el-select>
    </el-form-item>
    <el-form-item label="角色">
      <el-tag type="danger">路由器</el-tag>
    </el-form-item>
    <el-form-item label="管理网段">
      <el-input v-model="formData.mgmtSubnet" placeholder="192.168.1.0/24" />
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
  mgmtSubnet: '192.168.1.0/24',
})

onMounted(() => {
  const data = props.node.getData() || {}
  formData.value = {
    hostname: data.hostname || props.node.getAttrByPath('text/text') || props.node.id,
    vendor: data.vendor || 'huawei',
    mgmtSubnet: data.mgmtSubnet || '192.168.1.0/24',
  }
})

function handleSave() {
  emit('update', { ...formData.value, role: 'router', type: 'router' })
}
</script>

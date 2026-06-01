<template>
  <el-form :model="formData" label-width="100px" size="small">
    <el-form-item label="设备名称">
      <el-input v-model="formData.hostname" placeholder="FW-EDGE-01" />
    </el-form-item>
    <el-form-item label="厂商">
      <el-select v-model="formData.vendor" style="width: 100%">
        <el-option label="华为 Huawei" value="huawei" />
        <el-option label="H3C 华三" value="h3c" />
        <el-option label="Fortinet" value="fortinet" />
      </el-select>
    </el-form-item>
    <el-form-item label="角色">
      <el-tag>防火墙</el-tag>
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
})

onMounted(() => {
  const data = props.node.getData() || {}
  formData.value = {
    hostname: data.hostname || props.node.getAttrByPath('text/text') || props.node.id,
    vendor: data.vendor || 'huawei',
  }
})

function handleSave() {
  emit('update', { ...formData.value, role: 'firewall', type: 'firewall' })
}
</script>

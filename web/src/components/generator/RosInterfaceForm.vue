<template>
  <el-form label-width="110px" size="small" @change="emitUpdate">
    <!-- 物理接口 -->
    <el-divider content-position="left">🔌 物理接口</el-divider>
    <div v-for="(iface, i) in form.interfaces" :key="'if'+i" class="iface-row">
      <el-row :gutter="4">
        <el-col :span="5">
          <el-input v-model="iface.name" placeholder="接口名" size="small" />
        </el-col>
        <el-col :span="5">
          <el-select v-model="iface.role" size="small" style="width:100%">
            <el-option label="WAN" value="wan" />
            <el-option label="LAN" value="lan" />
            <el-option label="Trunk" value="trunk" />
            <el-option label="未使用" value="unused" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-input v-model="iface.ip" placeholder="IP/掩码" size="small" :disabled="iface.role === 'unused'" />
        </el-col>
        <el-col :span="7">
          <el-input v-model="iface.comment" placeholder="描述" size="small" />
        </el-col>
        <el-col :span="2">
          <el-button text type="danger" size="small" @click="form.interfaces.splice(i,1);emitUpdate()">✕</el-button>
        </el-col>
      </el-row>
    </div>
    <el-button size="small" type="primary" plain @click="form.interfaces.push({name:'ether'+(form.interfaces.length+1),role:'lan',ip:'',comment:''});emitUpdate()" style="width:100%">+ 添加接口</el-button>

    <!-- Bridge 配置 -->
    <el-divider content-position="left">🌉 Bridge 桥接</el-divider>
    <el-form-item label="创建 Bridge">
      <el-button size="small" @click="form.bridges.push({name:'bridge'+(form.bridges.length+1),stp:'rstp',vlanFiltering:false,portsStr:''});emitUpdate()">+ 新建 Bridge</el-button>
    </el-form-item>
    <div v-for="(br, bi) in form.bridges" :key="'br'+bi" class="bridge-card">
      <div class="bridge-header">
        <el-input v-model="br.name" size="small" placeholder="bridge 名称" style="width:140px" />
        <el-select v-model="br.stp" size="small" style="width:120px;margin:0 8px">
          <el-option label="无 STP" value="none" />
          <el-option label="RSTP" value="rstp" />
          <el-option label="MSTP" value="mstp" />
        </el-select>
        <span class="ros-hint-sm">VLAN 过滤:</span>
        <el-switch v-model="br.vlanFiltering" size="small" style="margin-left:4px" />
        <el-button text type="danger" size="small" @click="form.bridges.splice(bi,1);emitUpdate()" style="margin-left:auto">删除</el-button>
      </div>
      <div class="bridge-ports">
        <span class="ros-hint-sm">成员端口 (逗号分隔):</span>
        <el-input v-model="br.portsStr" size="small" placeholder="例如: ether2,ether3" />
      </div>
    </div>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

const form = reactive({
  interfaces: [
    { name: 'ether1', role: 'wan', ip: '', comment: 'WAN出口' },
    { name: 'ether2', role: 'lan', ip: '192.168.1.1/24', comment: 'LAN' },
  ] as Array<{ name: string; role: string; ip: string; comment: string }>,
  bridges: [
    { name: 'bridge1', stp: 'rstp', vlanFiltering: false, portsStr: 'ether2,ether3' },
  ] as Array<{ name: string; stp: string; vlanFiltering: boolean; portsStr: string }>,
})

watch(() => props.modelValue, (v) => { if (v && Object.keys(v).length > 0) Object.assign(form, v) }, { immediate: true })
function emitUpdate() { emit('update:modelValue', { ...form }) }
watch(form, () => emitUpdate(), { deep: true })
</script>

<style scoped>
.iface-row { margin-bottom: 6px; }
.bridge-card { border: 1px solid #e8ecf1; border-radius: 6px; padding: 8px; margin-bottom: 8px; }
.bridge-header { display: flex; align-items: center; margin-bottom: 4px; }
.bridge-ports { margin-top: 4px; }
.ros-hint-sm { font-size: 11px; color: #909399; }
</style>

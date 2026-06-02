<template>
  <div class="property-panel">
    <!-- 选中节点时显示属性编辑 -->
    <template v-if="topologyStore.selectedNode">
      <div class="panel-title">设备属性</div>
      
      <!-- 动态加载对应设备类型的表单 -->
      <component
        :is="currentFormComponent"
        :node="topologyStore.selectedNode"
        @update="handleUpdate"
      />
      
      <el-divider />
      
      <div class="panel-title">快速操作</div>
      <el-button size="small" @click="handleDelete" type="danger" style="width: 100%">
        删除此设备
      </el-button>
    </template>

    <!-- 选中连线时显示连线属性 -->
    <template v-else-if="topologyStore.selectedEdge">
      <div class="panel-title">连线属性</div>
      <el-form :model="edgeProps" label-width="80px" size="small">
        <el-form-item label="链路类型">
          <el-select v-model="edgeProps.linkType" style="width: 100%" @change="updateEdge">
            <el-option label="Access" value="access" />
            <el-option label="Trunk" value="trunk" />
            <el-option label="Hybrid" value="hybrid" />
          </el-select>
        </el-form-item>
        <el-form-item label="源端口">
          <el-input v-model="edgeProps.sourcePort" placeholder="G0/0/1" @change="updateEdge" />
        </el-form-item>
        <el-form-item label="目标端口">
          <el-input v-model="edgeProps.targetPort" placeholder="G0/0/24" @change="updateEdge" />
        </el-form-item>
        <el-form-item label="VLAN" v-if="edgeProps.linkType === 'access'">
          <el-input-number v-model="edgeProps.vlanId" :min="1" :max="4094" style="width: 100%" @change="updateEdge" />
        </el-form-item>
        <el-form-item label="带宽">
          <el-select v-model="edgeProps.bandwidth" style="width: 100%" @change="updateEdge">
            <el-option label="1G" value="1G" />
            <el-option label="10G" value="10G" />
            <el-option label="40G" value="40G" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <el-divider />
      
      <div class="panel-title">快速操作</div>
      <el-button size="small" @click="handleDeleteEdge" type="danger" style="width: 100%">
        删除此连线
      </el-button>
    </template>

    <!-- 未选中任何对象时显示提示 -->
    <template v-else>
      <div class="panel-title">设备属性</div>
      <el-empty description="点击画布中的设备或连线查看详情" :image-size="80" />
      <el-alert type="info" :closable="false" style="margin-top: 12px; font-size: 12px">
        <template #default>
          <div>
            1. 从左侧拖拽设备到画布<br/>
            2. 点击设备编辑属性<br/>
            3. 连线表示物理连接<br/>
            4. 点击"生成配置"查看命令
          </div>
        </template>
      </el-alert>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTopologyStore } from '@/stores/topology'
import CoreSwitchForm from './forms/CoreSwitchForm.vue'
import AggSwitchForm from './forms/AggSwitchForm.vue'
import AccessSwitchForm from './forms/AccessSwitchForm.vue'
import RouterForm from './forms/RouterForm.vue'
import FirewallForm from './forms/FirewallForm.vue'
import DefaultForm from './forms/DefaultForm.vue'

const topologyStore = useTopologyStore()

// 连线属性
const edgeProps = ref({
  linkType: 'trunk' as 'access' | 'trunk' | 'hybrid',
  sourcePort: '',
  targetPort: '',
  vlanId: 1,
  bandwidth: '1G',
})

// 根据设备类型动态选择表单组件
const currentFormComponent = computed(() => {
  const type = topologyStore.selectedNode?.getData()?.type
  const formMap: Record<string, any> = {
    'core-switch': CoreSwitchForm,
    'agg-switch': AggSwitchForm,
    'access-switch': AccessSwitchForm,
    'router': RouterForm,
    'routeros': RouterForm,   // RouterOS 复用路由器表单
    'firewall': FirewallForm,
  }
  return formMap[type] || DefaultForm
})

// 监听选中连线变化
watch(() => topologyStore.selectedEdge, (edge) => {
  if (edge) {
    const data = edge.getData() || {}
    edgeProps.value = {
      linkType: data.linkType || 'trunk',
      sourcePort: data.sourcePort || '',
      targetPort: data.targetPort || '',
      vlanId: data.vlanId || 1,
      bandwidth: data.bandwidth || '1G',
    }
  }
})

function handleUpdate(data: any) {
  if (!topologyStore.selectedNode) return
  const node = topologyStore.selectedNode
  node.setData({ ...node.getData(), ...data })
  
  // 更新显示名称（custom-device 节点的文本在 label 选择器）
  if (data.hostname) {
    node.setAttrByPath('label/text', data.hostname)
  }
  
  ElMessage.success('属性已更新')
}

function handleDelete() {
  if (!topologyStore.selectedNode) return
  
  ElMessageBox.confirm('确定要删除此设备吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    topologyStore.selectedNode.remove()
    topologyStore.selectedNode = null
    ElMessage.success('设备已删除')
  }).catch(() => {})
}

function updateEdge() {
  if (!topologyStore.selectedEdge) return
  topologyStore.selectedEdge.setData({ ...edgeProps.value })
  ElMessage.success('连线属性已更新')
}

function handleDeleteEdge() {
  if (!topologyStore.selectedEdge) return
  
  ElMessageBox.confirm('确定要删除此连线吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    topologyStore.selectedEdge.remove()
    topologyStore.selectedEdge = null
    ElMessage.success('连线已删除')
  }).catch(() => {})
}
</script>

<style scoped>
.property-panel {
  width: 320px;
  background: #fafafa;
  border-left: 1px solid #e4e7ed;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.panel-title {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
  color: #303133;
}
</style>

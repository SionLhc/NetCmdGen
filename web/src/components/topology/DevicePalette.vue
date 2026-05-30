<template>
  <div class="device-palette">
    <div class="palette-title">网络设备</div>
    <div class="device-list">
      <div
        v-for="device in deviceTypes"
        :key="device.type"
        class="device-item"
        draggable="true"
        @dragstart="onDragStart($event, device)"
      >
        <div class="device-icon">
          <img :src="device.iconUrl" :alt="device.name" />
        </div>
        <div class="device-info">
          <div class="device-name">{{ device.name }}</div>
          <div class="device-role">{{ getRoleName(device.type) }}</div>
        </div>
      </div>
    </div>
    
    <el-divider />
    
    <div class="palette-title">操作提示</div>
    <el-alert type="info" :closable="false" style="font-size: 12px">
      <template #default>
        <div>
          1. 拖拽设备到画布<br/>
          2. 点击设备编辑属性<br/>
          3. 连线表示物理连接<br/>
          4. 一键生成完整配置
        </div>
      </template>
    </el-alert>
  </div>
</template>

<script setup lang="ts">
import { getAllDeviceTypes } from './deviceIcons'

const deviceTypes = getAllDeviceTypes()

function onDragStart(e: DragEvent, device: any) {
  e.dataTransfer?.setData('deviceType', device.type)
  e.dataTransfer?.setData('deviceColor', device.color)
  e.dataTransfer?.setData('deviceIcon', device.iconUrl)
  e.dataTransfer?.setData('deviceRole', device.type)
}

function getRoleName(type: string): string {
  const roleMap: Record<string, string> = {
    'core-switch': '核心层',
    'agg-switch': '汇聚层',
    'access-switch': '接入层',
    'router': '路由',
    'firewall': '安全',
    'server': '服务器',
    'pc': '终端',
  }
  return roleMap[type] || type
}
</script>

<style scoped>
.device-palette {
  width: 200px;
  background: #fafafa;
  border-right: 1px solid #e4e7ed;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.palette-title {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
  color: #303133;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.device-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s;
}

.device-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
  transform: translateY(-1px);
}

.device-item:active {
  cursor: grabbing;
}

.device-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.device-icon :deep(svg),
.device-icon img {
  width: 40px;
  height: 40px;
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 2px;
}

.device-role {
  font-size: 11px;
  color: #909399;
}
</style>
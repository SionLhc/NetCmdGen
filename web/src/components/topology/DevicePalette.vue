<template>
  <div class="device-palette">
    <div class="palette-header">
      <span class="palette-title">设备库</span>
      <span class="device-count">{{ totalCount }} 种</span>
    </div>

    <!-- 搜索过滤 -->
    <el-input
      v-model="searchText"
      placeholder="搜索设备..."
      size="small"
      clearable
      class="search-input"
      :prefix-icon="Search"
    />

    <!-- 分类分组,可折叠 -->
    <el-collapse v-model="activeGroups" class="group-list">
      <el-collapse-item
        v-for="group in filteredGroups"
        :key="group.id"
        :name="group.id"
      >
        <template #title>
          <div class="group-title">
            <span class="group-name">{{ group.title }}</span>
            <span class="group-count">{{ group.devices.length }}</span>
          </div>
        </template>

        <div class="device-list">
          <div
            v-for="device in group.devices"
            :key="device.type"
            class="device-item"
            draggable="true"
            @dragstart="onDragStart($event, device)"
            @mouseenter="onHoverDevice(device)"
            @mouseleave="onHoverDevice(null)"
          >
            <div class="device-icon" :style="{ background: device.color + '15' }">
              <img :src="device.iconUrl" :alt="device.name" />
            </div>
            <div class="device-info">
              <div class="device-name">{{ device.name }}</div>
              <div class="device-type">{{ device.type }}</div>
            </div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- 操作提示 -->
    <div class="palette-tips">
      <div class="tip-item"><span class="tip-icon">⊞</span> 拖拽到画布</div>
      <div class="tip-item"><span class="tip-icon">↗</span> 拖拽端口连线</div>
      <div class="tip-item"><span class="tip-icon">🖱</span> 双击修改名称</div>
      <div class="tip-item"><span class="tip-icon">⌨</span> Ctrl+滚轮缩放</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getGroupedDevices, deviceIcons, type DeviceIcon, type DeviceGroup } from './deviceIcons'

const searchText = ref('')
/** 默认所有分组都展开 */
const activeGroups = ref(['network', 'terminal', 'cloud', 'security'])
/** 悬浮的设备（用于在画布上预览） */
const emit = defineEmits(['hover-device'])

const allGroups = getGroupedDevices()

/** 根据搜索文本过滤分组和设备 */
const filteredGroups = computed<DeviceGroup[]>(() => {
    if (!searchText.value.trim()) return allGroups

    const keyword = searchText.value.toLowerCase()
    return allGroups
        .map(group => ({
            ...group,
            devices: group.devices.filter(d =>
                d.name.includes(keyword) ||
                d.type.toLowerCase().includes(keyword)
            ),
        }))
        .filter(group => group.devices.length > 0)
})

/** 总设备数 */
const totalCount = computed(() => Object.keys(deviceIcons).length)

function onDragStart(e: DragEvent, device: DeviceIcon) {
    e.dataTransfer?.setData('deviceType', device.type)
    e.dataTransfer?.setData('deviceColor', device.color)
    e.dataTransfer?.setData('deviceIcon', device.iconUrl)
    e.dataTransfer?.setData('deviceRole', device.type)
    // 设置拖拽图像
    if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = 'copy'
    }
}

function onHoverDevice(device: DeviceIcon | null) {
    emit('hover-device', device)
}
</script>

<style scoped>
.device-palette {
    width: 220px;
    background: #fafbfc;
    border-right: 1px solid #e4e7ed;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.palette-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    border-bottom: 1px solid #e4e7ed;
    background: #fff;
}

.palette-title {
    font-size: 15px;
    font-weight: 600;
    color: #303133;
}

.device-count {
    font-size: 11px;
    color: #909399;
    background: #f0f2f5;
    padding: 2px 8px;
    border-radius: 10px;
}

.search-input {
    margin: 10px 12px;
    width: calc(100% - 24px);
}

.group-list {
    flex: 1;
    overflow-y: auto;
    padding: 0 8px;
    border-top: none;
}

.group-list :deep(.el-collapse-item__header) {
    height: 36px;
    line-height: 36px;
    font-size: 13px;
    padding: 0 8px;
    border: none;
}

.group-list :deep(.el-collapse-item__wrap) {
    border: none;
}

.group-list :deep(.el-collapse-item__content) {
    padding: 0 0 8px 0;
}

.group-title {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
}

.group-name {
    font-weight: 600;
    color: #303133;
}

.group-count {
    font-size: 11px;
    color: #909399;
    background: #f0f2f5;
    padding: 1px 6px;
    border-radius: 8px;
}

.device-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.device-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    background: #fff;
    border: 1px solid #ebeef5;
    border-radius: 6px;
    cursor: grab;
    transition: all 0.15s ease;
}

.device-item:hover {
    border-color: #409eff;
    background: #ecf5ff;
    box-shadow: 0 1px 4px rgba(64, 158, 255, 0.15);
}

.device-item:active {
    cursor: grabbing;
    transform: scale(0.97);
}

.device-icon {
    width: 36px;
    height: 36px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    padding: 3px;
}

.device-icon img {
    width: 28px;
    height: 28px;
    object-fit: contain;
}

.device-info {
    flex: 1;
    min-width: 0;
}

.device-name {
    font-size: 12px;
    font-weight: 500;
    color: #303133;
    line-height: 1.3;
}

.device-type {
    font-size: 10px;
    color: #a8abb2;
    line-height: 1.2;
}

.palette-tips {
    padding: 12px 14px;
    border-top: 1px solid #e4e7ed;
    background: #fff;
}

.tip-item {
    font-size: 11px;
    color: #909399;
    line-height: 1.8;
}

.tip-icon {
    display: inline-block;
    width: 18px;
    font-size: 12px;
    color: #c0c4cc;
}
</style>

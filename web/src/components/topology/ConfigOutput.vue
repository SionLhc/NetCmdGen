<template>
  <div class="config-output-panel">
    <div class="output-header">
      <span class="output-title">📋 生成的配置命令</span>
      <div class="output-actions">
        <el-button size="small" @click="handleCopy" :disabled="topologyStore.deviceOutputs.length === 0">
          复制当前
        </el-button>
        <el-button size="small" @click="handleCopyAll" :disabled="topologyStore.deviceOutputs.length === 0">
          复制全部
        </el-button>
        <el-button size="small" @click="handleClear" :disabled="topologyStore.deviceOutputs.length === 0">
          清空
        </el-button>
      </div>
    </div>

    <!-- 设备 Tab 切换 -->
    <div v-if="topologyStore.deviceOutputs.length > 0" class="output-body">
      <div class="device-tabs">
        <div
          v-for="(out, idx) in topologyStore.deviceOutputs"
          :key="idx"
          class="device-tab"
          :class="{ active: topologyStore.activeOutputDevice === idx }"
          @click="topologyStore.activeOutputDevice = idx"
        >
          <span class="device-name">{{ out.device }}</span>
          <span class="device-meta">
            <el-tag :type="out.error ? 'danger' : 'success'" size="small" effect="dark">
              {{ out.error ? '✗' : out.lines }}行
            </el-tag>
            <span class="vendor-badge">{{ out.vendorName }}</span>
          </span>
        </div>
      </div>

      <!-- 选中设备的输出 -->
      <div class="output-content" v-if="topologyStore.deviceOutputs[topologyStore.activeOutputDevice]">
        <div class="output-info-bar">
          <span>
            <strong>{{ topologyStore.deviceOutputs[topologyStore.activeOutputDevice].device }}</strong>
          </span>
          <span style="color:#909399;font-size:12px">
            {{ topologyStore.deviceOutputs[topologyStore.activeOutputDevice].vendorName }}
            — {{ topologyStore.deviceOutputs[topologyStore.activeOutputDevice].lines }} 行
          </span>
        </div>
        <pre class="code-block"><code>{{ topologyStore.deviceOutputs[topologyStore.activeOutputDevice].output }}</code></pre>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="output-empty">
      <el-empty description='在画布中拖入设备，选择厂商后点击"一键生成全部配置"' :image-size="60" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { useTopologyStore } from '@/stores/topology'

const topologyStore = useTopologyStore()

function handleCopy() {
  const out = topologyStore.deviceOutputs[topologyStore.activeOutputDevice]
  if (!out) return
  navigator.clipboard.writeText(out.output)
  ElMessage.success(`已复制 ${out.device} 的配置`)
}

function handleCopyAll() {
  const all = topologyStore.deviceOutputs
    .map(o => `# ===== ${o.device} (${o.vendorName}) =====\n${o.output}`)
    .join('\n\n')
  navigator.clipboard.writeText(all)
  ElMessage.success(`已复制全部 ${all.split('\n').length} 台设备配置`)
}

function handleClear() {
  topologyStore.deviceOutputs = []
  topologyStore.configOutput = ''
  ElMessage.success('已清空')
}
</script>

<style scoped>
.config-output-panel {
  border-top: 2px solid #409eff;
  background: #fafafa;
  max-height: 45vh;
  display: flex;
  flex-direction: column;
}

.output-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.output-title {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
}

.output-actions {
  display: flex;
  gap: 8px;
}

.output-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.device-tabs {
  display: flex;
  gap: 0;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  overflow-x: auto;
  flex-shrink: 0;
  padding: 0 8px;
}

.device-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all .2s;
  white-space: nowrap;
  font-size: 13px;
}

.device-tab:hover {
  background: #f5f7fa;
}

.device-tab.active {
  border-bottom-color: #409eff;
  color: #409eff;
  font-weight: 600;
}

.device-name {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.device-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}

.vendor-badge {
  font-size: 11px;
  color: #909399;
  background: #f0f2f5;
  padding: 1px 6px;
  border-radius: 3px;
}

.output-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.output-info-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 16px;
  background: #f8f9fb;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
  color: #606266;
  flex-shrink: 0;
}

.code-block {
  flex: 1;
  background: #1a1b2e;
  color: #c9d1d9;
  padding: 16px 20px;
  margin: 0;
  font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.7;
  overflow: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  min-height: 0;
}

.output-empty {
  padding: 40px 20px;
  text-align: center;
}
</style>

<template>
  <div class="config-output-panel">
    <div class="output-header">
      <span class="output-title">📋 生成的配置命令</span>
      <div class="output-actions">
        <el-button size="small" @click="handleCopy" :disabled="!topologyStore.configOutput">
          复制
        </el-button>
        <el-button size="small" @click="handleClear" :disabled="!topologyStore.configOutput">
          清空
        </el-button>
      </div>
    </div>
    
    <div v-if="topologyStore.configOutput" class="output-content">
      <pre class="code-block"><code>{{ topologyStore.configOutput }}</code></pre>
    </div>
    
    <div v-else class="output-empty">
      <el-empty description='点击"一键生成全部配置"按钮查看命令' :image-size="60" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { useTopologyStore } from '@/stores/topology'

const topologyStore = useTopologyStore()

function handleCopy() {
  if (!topologyStore.configOutput) return
  
  navigator.clipboard.writeText(topologyStore.configOutput)
  ElMessage.success('已复制到剪贴板')
}

function handleClear() {
  topologyStore.configOutput = ''
  ElMessage.success('已清空')
}
</script>

<style scoped>
.config-output-panel {
  border-top: 2px solid #409eff;
  background: #fafafa;
  max-height: 40vh;
  overflow: auto;
}

.output-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
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

.output-content {
  max-height: calc(40vh - 50px);
  overflow: auto;
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  margin: 0;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  max-height: calc(40vh - 50px);
  overflow: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.output-empty {
  padding: 40px 20px;
  text-align: center;
}
</style>

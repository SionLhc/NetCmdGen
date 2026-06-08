<template>
  <div class="page">
    <h2>💾 配置备份</h2>

    <!-- 操作区 -->
    <el-card style="margin-bottom:14px">
      <el-form :inline="true" size="default">
        <el-form-item label="选择设备">
          <el-select v-model="selectedIp" placeholder="选择已添加的设备" style="width:220px" filterable>
            <el-option v-for="d in devices" :key="d.ip" :label="`${d.name} (${d.ip})`" :value="d.ip" />
          </el-select>
          <el-button link size="small" @click="loadDevices" style="margin-left:8px" title="刷新设备列表">🔄</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchConfig" :loading="fetching" :disabled="!selectedIp">
            📥 从设备下载配置
          </el-button>
        </el-form-item>
        <el-form-item>
          <span style="font-size:12px;color:#94a3b8">
            设备需先在「网络巡检→设备管理」中添加（含 SSH/Telnet 凭证）
          </span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 备份列表 -->
    <el-table :data="list" size="small" border v-loading="loadingList" empty-text="暂无备份记录">
      <el-table-column prop="device_name" label="设备" width="150">
        <template #default="{row}">
          <el-popover trigger="hover" placement="right" :width="420" :show-after="200">
            <template #reference>
              <span style="cursor:pointer;color:#1e293b;font-weight:500">{{ row.device_name }}</span>
            </template>
            <div class="preview-pop">
              <div class="preview-head">{{ row.device_name }} · {{ row.created_at }}</div>
              <pre class="preview-content">{{ row.fullConfig || row.preview || '加载中...' }}</pre>
            </div>
          </el-popover>
        </template>
      </el-table-column>
      <el-table-column label="配置大小" width="100" align="center">
        <template #default="{row}">
          <el-tag size="small" type="info">{{ formatSize(row.config_size) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="配置预览" min-width="200">
        <template #default="{row}">
          <code style="font-size:11px;max-width:480px;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#64748b">
            {{ row.preview || '(点击查看按钮查看完整内容)' }}
          </code>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="备份时间" width="170" />
      <el-table-column label="操作" width="180" align="center">
        <template #default="{row}">
          <el-button size="small" @click="view(row)">查看</el-button>
          <el-button size="small" type="primary" @click="download(row.id)">下载</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 查看弹窗 -->
    <el-dialog v-model="showView" title="配置内容" width="800px">
      <div style="max-height:500px;overflow:auto;background:#1e293b;color:#e2e8f0;padding:16px;border-radius:8px;font-family:monospace;font-size:12px;white-space:pre-wrap;line-height:1.5">{{ viewing?.config || '(空)' }}</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const devices = ref<any[]>([])
const selectedIp = ref('')
const list = ref<any[]>([])
const loadingList = ref(false)
const fetching = ref(false)
const viewing = ref<any>(null)
const showView = ref(false)

async function loadDevices() {
  try {
    const r = await fetch('/api/health/devices')
    devices.value = await r.json()
  } catch { devices.value = [] }
}

async function loadList() {
  loadingList.value = true
  try {
    const r = await fetch('/api/backup')
    let raw = await r.json()
    // 每个备份加载前 200 字符预览
    raw = raw.map((b: any) => {
      // 异步获取完整内容做预览（保持列表快）
      fetch(`/api/backup/${b.id}`).then(r2 => r2.json()).then(d => {
        b.preview = (d.config || '').replace(/\n/g, ' ').slice(0, 200)
        b.fullConfig = d.config
      }).catch(() => {})
      return b
    })
    list.value = raw.reverse()
  } finally { loadingList.value = false }
}

async function fetchConfig() {
  if (!selectedIp.value) return
  fetching.value = true
  try {
    const r = await fetch(`/api/backup/fetch?host=${encodeURIComponent(selectedIp.value)}`, { method: 'POST' })
    if (!r.ok) {
      const err = await r.json()
      ElMessage.error(err.detail || '抓取失败')
      return
    }
    const data = await r.json()
    ElMessage.success(`配置已保存: ${data.device_name} · ${formatSize(data.size)}`)
    selectedIp.value = ''
    await loadList()
  } catch (e: any) {
    ElMessage.error(`连接失败: ${e.message || '未知错误'}`)
  } finally { fetching.value = false }
}

async function view(row: any) {
  // 获取完整内容
  const r = await fetch(`/api/backup/${row.id}`)
  if (r.ok) viewing.value = await r.json()
  showView.value = true
}

function download(id: number) {
  // 直接触发浏览器下载
  const a = document.createElement('a')
  a.href = `/api/backup/download/${id}`
  a.download = ''
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  return (bytes / 1024).toFixed(1) + ' KB'
}

onMounted(() => { loadDevices(); loadList() })
</script>

<style scoped>
.page { padding: 24px; max-width: 1300px; margin: 0 auto; }
h2 { margin: 0 0 14px; font-size: 20px; }
code { background: #f1f5f9; padding: 1px 6px; border-radius: 3px; }

/* 悬停预览卡片 */
.preview-pop { max-height: 300px; }
.preview-head { font-weight: 600; font-size: 13px; color: #1e293b; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #e2e8f0; }
.preview-content { margin: 0; font-size: 11px; font-family: monospace; line-height: 1.4; color: #475569; white-space: pre-wrap; max-height: 240px; overflow: auto; background: #f8fafc; padding: 8px; border-radius: 4px; }
</style>

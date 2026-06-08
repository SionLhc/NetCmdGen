<template>
  <div class="batch-page">
    <h2>📤 批量命令</h2>
    <p class="sub">一次编写命令，同时下发到多台交换机/路由器/防火墙</p>

    <el-card style="margin-bottom:14px">
      <el-form :inline="true" size="default">
        <el-form-item label="设备类型">
          <el-select v-model="filterType" placeholder="筛选" style="width:140px" @change="loadDevices">
            <el-option label="全部" value="all" />
            <el-option label="交换机" value="sw" />
            <el-option label="路由器" value="router" />
            <el-option label="防火墙" value="fw" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveToQueue" :disabled="!selectedDevs.length">
            加入队列 ({{ selectedDevs.length }})
          </el-button>
        </el-form-item>
      </el-form>

      <el-table :data="devices" size="small" border max-height="300" @selection-change="onSelect">
        <el-table-column type="selection" width="40" />
        <el-table-column prop="name" label="设备名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column label="协议" width="70" align="center">
          <template #default="{row}">
            <el-tag :type="row.protocol==='telnet'?'warning':'success'" size="small" effect="plain">
              {{ row.protocol === 'telnet' ? 'Telnet' : 'SSH' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="80" align="center"/>
        <el-table-column prop="port" label="端口" width="60" align="center"/>
      </el-table>
    </el-card>

    <!-- 命令编辑 + 执行队列 -->
    <div class="two-col">
      <div class="col-left">
        <div class="col-title">💻 命令编辑</div>
        <el-input
          v-model="command"
          type="textarea"
          :rows="8"
          placeholder="输入要批量执行的命令，每行一条&#10;例如：&#10;display version&#10;display interface brief&#10;display vlan"
        />
        <div style="margin-top:8px;display:flex;gap:8px">
          <el-button type="primary" @click="saveToQueue" :disabled="!selectedDevs.length || !command.trim()">
            → 加入执行队列
          </el-button>
          <el-popconfirm title="确认清空队列？" @confirm="clearQueue">
            <el-button :disabled="!queue.length">清空队列</el-button>
          </el-popconfirm>
        </div>
      </div>

      <div class="col-right">
        <div class="col-title">⏳ 执行队列 ({{ queue.length }} 台)</div>
        <div class="queue-list" v-if="queue.length">
          <div class="queue-item" v-for="(q,i) in queue" :key="i">
            <span class="qi-icon">
              {{ q.status==='done'?'✅':q.status==='running'?'⏳':q.status==='fail'?'❌':'⏸' }}
            </span>
            <span class="qi-dev">{{ q.device?.name || q.device?.ip }}</span>
            <span class="qi-status">{{ q.result || '等待执行' }}</span>
            <el-button text size="small" type="danger" @click="queue.splice(i,1)">✕</el-button>
          </div>
        </div>
        <div class="queue-empty" v-else>暂无设备，请先在左侧选择设备并加入队列</div>
        <el-button
          v-if="queue.length"
          type="success"
          style="margin-top:10px;width:100%"
          @click="executeAll"
          :loading="running"
        >
          🚀 批量执行 ({{ queue.length }} 台)
        </el-button>
      </div>
    </div>

    <!-- 执行结果 -->
    <el-card v-if="results.length" style="margin-top:14px">
      <template #header>
        📋 执行结果 ·
        <span style="color:#67c23a">✓{{ results.filter(r=>r.ok).length }}</span> /
        <span style="color:#f56c6c">✗{{ results.filter(r=>!r.ok).length }}</span>
      </template>
      <el-table :data="results" size="small" border max-height="400">
        <el-table-column prop="device" label="设备" width="140" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{row}">
            <el-tag :type="row.ok?'success':'danger'" size="small">{{ row.ok ? '成功' : '失败' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="output" label="命令输出">
          <template #default="{row}">
            <pre style="margin:0;font-size:11px;max-height:240px;overflow:auto;background:#f8fafc;padding:8px;border-radius:4px">{{ row.output }}</pre>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const filterType = ref('all')
const devices = ref<any[]>([])
const selectedDevs = ref<any[]>([])
const command = ref('')
const queue = ref<any[]>([])
const running = ref(false)
const results = ref<any[]>([])

function onSelect(vals: any[]) { selectedDevs.value = vals }

async function loadDevices() {
  try {
    // 从巡检设备库加载（有完整凭证 + 协议信息）
    const r = await fetch('/api/health/devices')
    let all: any[] = await r.json()
    if (filterType.value !== 'all') {
      const kw = filterType.value.toLowerCase()
      all = all.filter(d =>
        (d.name || '').toLowerCase().includes(kw)
      )
    }
    devices.value = all
  } catch { devices.value = [] }
}

function saveToQueue() {
  const added = selectedDevs.value.filter(
    d => !queue.value.find(q => q.device?.ip === d.ip)
  )
  for (const d of added) {
    queue.value.push({
      device: d,
      status: 'pending',
      result: '',
      commands: command.value,
    })
  }
  command.value = ''
  selectedDevs.value = []
  ElMessage.success(`已添加 ${added.length} 台设备到队列`)
}

function clearQueue() { queue.value = [] }

async function executeAll() {
  running.value = true
  results.value = []

  for (const q of queue.value) {
    q.status = 'running'
    const d = q.device
    // 凭证由后端从巡检设备库自动获取，前端只需传 IP
    const params = new URLSearchParams({
      host: d.ip,
      commands: q.commands,
    })

    try {
      const r = await fetch(`/api/batch/execute?${params}`, { method: 'POST' })
      const data = await r.json()

      if (data.ok) {
        q.status = 'done'
        q.result = '执行成功'
      } else {
        q.status = 'fail'
        q.result = data.output || '执行失败'
      }
      results.value.push({
        device: d.name || d.ip,
        ok: data.ok,
        output: data.output,
      })
    } catch (e: any) {
      q.status = 'fail'
      q.result = e.message || '连接失败'
      results.value.push({
        device: d.name || d.ip,
        ok: false,
        output: `连接错误: ${e.message || '未知'}`,
      })
    }
  }

  running.value = false
  const ok = results.value.filter(r => r.ok).length
  ElMessage.success(`执行完成: ${ok}/${results.value.length} 成功`)
}

onMounted(loadDevices)
</script>

<style scoped>
.batch-page { padding: 24px; max-width: 1300px; margin: 0 auto; }
.batch-page h2 { font-size: 20px; margin: 0 0 2px; }
.sub { color: #909399; font-size: 13px; margin-bottom: 16px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.col-title { font-weight: 600; font-size: 14px; margin-bottom: 8px; color: #303133; }
.col-left, .col-right { background: #fff; border: 1px solid #e8ecf1; border-radius: 10px; padding: 14px; }
.queue-list { max-height: 280px; overflow-y: auto; }
.queue-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #f5f5f5; font-size: 13px; }
.qi-icon { font-size: 14px; min-width: 24px; text-align: center; }
.qi-dev { font-weight: 600; min-width: 80px; }
.qi-status { color: #909399; font-size: 12px; flex: 1; }
.queue-empty { color: #c0c4cc; font-size: 13px; padding: 30px 0; text-align: center; }
pre { white-space: pre-wrap; word-break: break-all; }
@media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }
</style>

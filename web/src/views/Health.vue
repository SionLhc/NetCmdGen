<template>
  <div class="page">
    <h2>🔍 网络巡检</h2>

    <!-- Tab 切换 -->
    <el-tabs v-model="activeTab" style="margin-bottom:14px">
      <el-tab-pane label="设备管理" name="devices" />
      <el-tab-pane label="执行巡检" name="inspect" />
      <el-tab-pane label="巡检报告" name="reports" />
    </el-tabs>

    <!-- ── Tab1: 设备管理 ── -->
    <div v-show="activeTab==='devices'">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <span style="font-size:13px;color:#64748b">已添加 {{ devices.length }} 台设备</span>
        <el-button type="primary" size="small" @click="openDevForm()">+ 添加设备</el-button>
      </div>
      <el-table :data="devices" size="small" border v-loading="loadingDevs" empty-text="暂无设备，请添加交换机/路由器">
        <el-table-column prop="name" label="名称" width="130"/>
        <el-table-column prop="ip" label="IP" width="140"/>
        <el-table-column prop="username" label="用户名" width="100"/>
        <el-table-column label="密码" width="90">
          <template #default><span style="color:#94a3b8">••••••</span></template>
        </el-table-column>
        <el-table-column prop="port" label="端口" width="70" align="center"/>
        <el-table-column label="操作" width="160" align="center">
          <template #default="{row,$index}">
            <el-button type="primary" link size="small" @click="openDevForm(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="delDevice($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ── Tab2: 执行巡检 ── -->
    <div v-show="activeTab==='inspect'">
      <el-card>
        <template #header>选择设备和巡检项</template>
        <!-- 多选设备 -->
        <div style="margin-bottom:14px">
          <div style="font-size:13px;color:#64748b;margin-bottom:6px">目标设备（可多选）</div>
          <el-checkbox-group v-model="inspectDevs" style="display:flex;flex-wrap:wrap;gap:8px">
            <el-checkbox v-for="d in devices" :key="d.ip" :label="d.ip" border size="small">
              {{ d.name }} ({{ d.ip }})
            </el-checkbox>
          </el-checkbox-group>
          <span v-if="!devices.length" style="color:#94a3b8;font-size:12px">
            请先在「设备管理」中添加设备
          </span>
        </div>
        <!-- 巡检项多选 -->
        <div style="margin-bottom:14px">
          <div style="font-size:13px;color:#64748b;margin-bottom:6px;display:flex;align-items:center;gap:12px">
            巡检项
            <el-button link size="small" @click="selectAllChecks">全选</el-button>
            <el-button link size="small" @click="selectDefaultChecks">默认</el-button>
          </div>
          <el-checkbox-group v-model="inspectChecks" style="display:flex;flex-wrap:wrap;gap:8px">
            <el-checkbox v-for="t in templates" :key="t.id" :label="t.id" border size="small">
              <el-tooltip :content="t.command||''" placement="top" :show-after="500">
                {{ t.name }}
              </el-tooltip>
            </el-checkbox>
          </el-checkbox-group>
        </div>
        <el-button type="primary" @click="runBatch" :loading="inspecting" :disabled="!inspectDevs.length||!inspectChecks.length">
          🚀 执行巡检
        </el-button>
      </el-card>

      <!-- 巡检进行中的进度 -->
      <el-card v-if="inspecting" style="margin-top:14px">
        <template #header>巡检进行中...</template>
        <div style="text-align:center;padding:20px">
          <el-progress :percentage="inspectProgress" :stroke-width="20" :text-inside="true" />
          <div style="margin-top:8px;font-size:12px;color:#94a3b8">{{ inspectProgress }}% · 设备 {{ Math.ceil(inspectProgress/100*inspectDevs.length) }}/{{ inspectDevs.length }}</div>
        </div>
      </el-card>

      <!-- 批量巡检结果 -->
      <el-card v-if="batchResults.length" style="margin-top:14px">
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center">
            巡检结果
            <span style="font-size:13px;color:#94a3b8">
              总耗时 {{ totalElapsed }}s · 
              <span style="color:#67c23a">✓{{ batchStats.passed }}</span> /
              <span style="color:#e6a23c">⚠{{ batchStats.warning }}</span> /
              <span style="color:#f56c6c">✗{{ batchStats.failed }}</span>
            </span>
          </div>
        </template>
        <div v-for="(devResult,di) in batchResults" :key="di" style="margin-bottom:16px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">
          <!-- 设备头部 -->
          <div style="padding:10px 14px;background:#f8fafc;display:flex;align-items:center;gap:12px;border-bottom:1px solid #e5e7eb">
            <span style="font-weight:600;font-size:14px">{{ devResult.device_name }}</span>
            <el-tag :type="devResult.score>=90?'success':devResult.score>=60?'warning':'danger'" size="small" effect="dark">
              {{ devResult.score }} 分
            </el-tag>
            <span style="font-size:11px;color:#94a3b8;margin-left:auto">{{ devResult.elapsed_ms }}ms</span>
          </div>
          <!-- 巡检项明细表 -->
          <el-table :data="devResult.checks" size="small" style="width:100%" :show-header="true">
            <el-table-column prop="item_name" label="巡检项" width="140"/>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{row}">
                <el-tag :type="row.level==='normal'?'success':row.level==='warning'?'warning':'danger'" size="small">
                  {{ row.level==='normal'?'正常':row.level==='warning'?'警告':'异常' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="来源" width="70" align="center">
              <template #default="{row}">{{ row.source || 'SSH' }}</template>
            </el-table-column>
            <el-table-column label="详情">
              <template #default="{row}">
                <span :style="{color:row.level==='normal'?'#10b981':row.level==='warning'?'#e6a23c':'#ef4444',fontSize:'12px'}">
                  {{ row.message }}
                </span>
                <pre v-if="row.raw" style="font-size:10px;color:#94a3b8;max-height:60px;overflow:auto;margin:4px 0 0;background:#f8fafc;padding:4px 8px;border-radius:4px">{{ row.raw }}</pre>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>

    <!-- ── Tab3: 巡检报告 ── -->
    <div v-show="activeTab==='reports'">
      <el-table :data="reports" size="small" border v-loading="loadingList" empty-text="暂无巡检报告">
        <el-table-column prop="device_name" label="设备" width="150"/>
        <el-table-column prop="score" label="得分" width="80" align="center">
          <template #default="{row}">
            <el-tag :type="row.score>=90?'success':row.score>=60?'warning':'danger'" size="small">{{ row.score }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="通过/警告/失败" width="140" align="center">
          <template #default="{row}">
            <span style="color:#67c23a">✓{{ row.report?.passed || 0 }}</span>&nbsp;
            <span style="color:#e6a23c">⚠{{ row.report?.warning || 0 }}</span>&nbsp;
            <span style="color:#f56c6c">✗{{ row.report?.failed || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="巡检详情" min-width="300">
          <template #default="{row}">
            <div style="display:flex;flex-wrap:wrap;gap:4px">
              <template v-for="item in getCheckItems(row)" :key="item.item_name||item.name">
                <el-tag :type="item.level==='normal'?'success':item.level==='warning'?'warning':'danger'" size="small"
                  effect="plain">
                  {{ item.item_name || item.name }}
                </el-tag>
              </template>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="80" align="center">
          <template #default="{row}">{{ row.report?.elapsed_ms || '-' }}ms</template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="160"/>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{row,$index}">
            <el-button type="danger" link size="small" @click="delReport(row.id,$index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 设备编辑弹窗 -->
    <el-dialog v-model="showDevDialog" :title="editIdx>=0?'编辑设备':'添加设备'" width="420px">
      <el-form label-width="60px" size="default">
        <el-form-item label="名称"><el-input v-model="devForm.name" placeholder="如 Core-SW1"/></el-form-item>
        <el-form-item label="IP"><el-input v-model="devForm.ip" placeholder="192.168.1.1"/></el-form-item>
        <el-form-item label="端口"><el-input-number v-model="devForm.port" :min="1" :max="65535" style="width:100%"/></el-form-item>
        <el-form-item label="用户名"><el-input v-model="devForm.username" placeholder="admin"/></el-form-item>
        <el-form-item label="密码"><el-input v-model="devForm.password" type="password" placeholder="SSH 密码"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDevDialog=false">取消</el-button>
        <el-button type="primary" @click="saveDevice" :loading="savingDev">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRequest } from '@/composables/useRequest'

const { loading, get, post } = useRequest()

/* ── 状态 ── */
const activeTab = ref('devices')
const devices = ref<any[]>([])
const loadingDevs = ref(false)
const templates = ref<any[]>([])
const reports = ref<any[]>([])
const loadingList = ref(false)

// 巡检执行
const inspectDevs = ref<string[]>([])      // 选中设备 IP
const inspectChecks = ref<string[]>([])     // 选中巡检项
const inspecting = ref(false)
const inspectProgress = ref(0)
const batchResults = ref<any[]>([])
const totalElapsed = ref(0)

// 设备表单
const showDevDialog = ref(false)
const editIdx = ref(-1)
const devForm = reactive({ name: '', ip: '', port: 22, username: 'admin', password: '' })
const savingDev = ref(false)

// 默认巡检项
const DEFAULT_CHECKS = ['CPU使用率', '内存使用率', '温度状态', '风扇状态', '电源状态', '接口状态']
const batchStats = computed(() => {
  let passed = 0, warning = 0, failed = 0
  batchResults.value.forEach(r => {
    passed += r.passed || 0
    warning += r.warning || 0
    failed += r.failed || 0
  })
  return { passed, warning, failed }
})

/* ── 设备管理 ── */
async function loadDevices() {
  loadingDevs.value = true
  try {
    const data = await get<any[]>('/api/health/devices')
    if (data) devices.value = data
  } finally { loadingDevs.value = false }
}

function openDevForm(row?: any) {
  if (row) {
    editIdx.value = devices.value.indexOf(row)
    Object.assign(devForm, row)
  } else {
    editIdx.value = -1
    Object.assign(devForm, { name: '', ip: '', port: 22, username: 'admin', password: '' })
  }
  showDevDialog.value = true
}

async function saveDevice() {
  if (!devForm.ip) { ElMessage.warning('请输入 IP'); return }
  if (!devForm.username) { ElMessage.warning('请输入用户名'); return }
  savingDev.value = true
  const data = await post<any>('/api/health/devices',
    { ...devForm },
    { successMsg: '保存成功' }
  )
  savingDev.value = false
  if (data) {
    showDevDialog.value = false
    await loadDevices()
  }
}

async function delDevice(idx: number) {
  const ip = devices.value[idx].ip
  await ElMessageBox.confirm(`确认删除设备 ${devices.value[idx].name || ip}？`, '确认删除', { type: 'warning' })
  const ok = await post('/api/health/devices/delete', { ip }, { successMsg: '已删除' })
  if (ok) await loadDevices()
}

/* ── 巡检执行 ── */
function selectAllChecks() { inspectChecks.value = templates.value.map(t => t.id) }
function selectDefaultChecks() { inspectChecks.value = [...DEFAULT_CHECKS] }

async function runBatch() {
  if (!inspectDevs.value.length || !inspectChecks.value.length) return
  inspecting.value = true; inspectProgress.value = 0; batchResults.value = []

  const selectedDevices = devices.value.filter(d => inspectDevs.value.includes(d.ip))
  const checks = inspectChecks.value.join(',')
  const t0 = performance.now()

  for (let i = 0; i < selectedDevices.length; i++) {
    const d = selectedDevices[i]
    const data = await post<any>(
      `/api/health/run?device_id=${encodeURIComponent(d.ip)}&device_name=${encodeURIComponent(d.name||d.ip)}&device_ip=${encodeURIComponent(d.ip)}&device_port=${d.port}&username=${encodeURIComponent(d.username)}&password=${encodeURIComponent(d.password)}&checks=${checks}`,
      undefined,
      { timeout: 120 }
    )
    if (data) batchResults.value.push(data)
    inspectProgress.value = Math.round(((i + 1) / selectedDevices.length) * 100)
    // 批次间休息 1 秒，避免 SSH 连接风暴
    if (i < selectedDevices.length - 1) await new Promise(r => setTimeout(r, 1000))
  }
  totalElapsed.value = Math.round((performance.now() - t0) / 1000)
  inspecting.value = false

  if (batchResults.value.length) ElMessage.success(`巡检完成: ${batchResults.value.length} 台设备`)

  // 刷新报告列表
  loadReports()
}

/* ── 报告 ── */
async function loadReports() {
  loadingList.value = true
  try {
    const list = await get<any[]>('/api/health/reports')
    if (list) reports.value = list.reverse()
  } finally { loadingList.value = false }
}

async function delReport(id: number, idx: number) {
  await ElMessageBox.confirm('确认删除该报告？', '确认删除', { type: 'warning' })
  const ok = await post('/api/health/reports/delete', { id }, { successMsg: '已删除' })
  if (ok) reports.value.splice(idx, 1)
}

function getCheckItems(row: any): any[] {
  if (!row.report) return []
  if (Array.isArray(row.report.checks)) return row.report.checks
  if (typeof row.report === 'object') {
    return Object.values(row.report).filter((v: any) => v?.item_name || v?.name)
  }
  return []
}

/* ── 初始化 ── */
async function loadTemplates() {
  const data = await get<any[]>('/api/health/templates')
  if (data) {
    templates.value = data
    // 默认勾选常用项
    inspectChecks.value = [...DEFAULT_CHECKS]
  }
}

onMounted(async () => {
  await Promise.all([loadDevices(), loadTemplates(), loadReports()])
})
</script>

<style scoped>
.page { padding: 24px; max-width: 1400px; margin: 0 auto; }
h2 { margin: 0 0 14px; font-size: 20px; }
:deep(.el-checkbox.is-bordered) { margin-right: 0 !important; }
</style>

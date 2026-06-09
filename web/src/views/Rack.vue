<template>
  <div class="page">
    <div class="page-header">
      <h2>🗄️ 机柜管理</h2>
      <div style="display:flex;gap:8px;align-items:center">
        <!-- 区域筛选 -->
        <el-select v-model="regionFilter" placeholder="全部区域" clearable size="default" style="width:140px" @change="loadRacks">
          <el-option v-for="r in regions" :key="r" :label="r" :value="r"/>
        </el-select>
        <el-button @click="showImportDialog = true">📥 批量导入</el-button>
        <el-button type="primary" @click="showAddRack = true">+ 新增机柜</el-button>
      </div>
    </div>

    <!-- 机房视图：多机柜并排 -->
    <div class="room-view">
      <div v-for="r in filteredRacks" :key="r.id" class="rack-column" :class="{ active: cur === r.id }" @click="cur = r.id">
        <div class="rack-frame">
          <div class="rack-header">
            <span class="rack-name">{{ r.name || '未命名' }}</span>
            <span class="rack-loc">{{ r.region ? r.region + ' · ' : '' }}{{ r.location || '--' }}</span>
            <el-tag size="small" type="info">{{ r.devices?.length || 0 }} 设备</el-tag>
          </div>
          <div class="rack-body">
            <template v-for="blk in mergedBlocks(r)" :key="blk.key">
              <div v-if="blk.type === 'empty'" v-for="u in blk.count" :key="'e' + u + '_' + blk.startU" class="rack-u empty" @click.stop="onEmptyClick(r, blk.startU)">
                <span class="u-num">{{ blk.startU }}</span>
              </div>
              <el-popover v-else trigger="hover" placement="right" :width="250" :show-after="300" :hide-after="100">
                <template #reference>
                  <div class="rack-u merged" :class="getDevBlockClass(blk.device)"
                    :style="{ height: blk.count * ROW_HEIGHT + (blk.count - 1) * GAP + 'px' }"
                    @click.stop="onDevClick(r, blk.device)">
                    <span class="u-num">{{ blk.startU }}</span>
                    <div class="merged-body">
                      <span class="merged-name">{{ blk.device.name }}</span>
                      <span v-if="blk.device.model" class="merged-model">{{ blk.device.model }}</span>
                      <span v-if="blk.device.port_seat_count" class="merged-seat">🔗 {{ blk.device.port_seat_count }} 座位</span>
                    </div>
                  </div>
                </template>
                <div class="dev-popover">
                  <div class="dev-pop-title">{{ blk.device.name }}</div>
                  <el-divider style="margin:8px 0"/>
                  <div class="dev-pop-row"><span class="dev-pop-label">品牌</span><span>{{ blk.device.vendor || '--' }}</span></div>
                  <div class="dev-pop-row"><span class="dev-pop-label">型号</span><span>{{ blk.device.model || '--' }}</span></div>
                  <div class="dev-pop-row"><span class="dev-pop-label">IP</span><code>{{ blk.device.ip || '--' }}</code></div>
                  <div class="dev-pop-row"><span class="dev-pop-label">座位</span><span>{{ blk.device.port_seat_count || 0 }} 个映射</span></div>
                </div>
              </el-popover>
            </template>
          </div>
          <div class="rack-footer"><span>{{ r.rows }}U</span></div>
        </div>
        <div class="rack-actions">
          <el-button size="small" @click="editRack(r)">编辑</el-button>
          <el-button size="small" type="danger" @click="delRack(r)">删除</el-button>
        </div>
      </div>
      <el-empty v-if="!filteredRacks.length" description="暂无数据，点击右上角新增机柜" style="width:100%"/>
    </div>

    <!-- 新增/编辑机柜弹窗 -->
    <el-dialog v-model="showAddRack" :title="editingRack ? '编辑机柜' : '新增机柜'" width="420px">
      <el-form label-width="80px">
        <el-form-item label="名称"><el-input v-model="rackForm.name" placeholder="如：A1-01"/></el-form-item>
        <el-form-item label="区域">
          <el-select v-model="rackForm.region" placeholder="选择区域" filterable allow-create style="width:100%">
            <el-option v-for="r in regions" :key="r" :label="r" :value="r"/>
          </el-select>
        </el-form-item>
        <el-form-item label="位置"><el-input v-model="rackForm.loc" placeholder="如：机房A第1排"/></el-form-item>
        <el-form-item label="U位高度"><el-input-number v-model="rackForm.rows" :min="4" :max="48"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddRack = false">取消</el-button>
        <el-button type="primary" @click="saveRack" :loading="loading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑设备弹窗 -->
    <el-dialog v-model="showAddDev" :title="editingDev ? '编辑设备' : '添加设备'" width="420px">
      <el-alert v-if="selectedRack" :title="editingDev ? `编辑: ${selectedRack.name} 设备` : `添加到: ${selectedRack.name} 第 ${devForm.ustart}U`" type="info" :closable="false" style="margin-bottom:12px"/>
      <el-form label-width="80px">
        <el-form-item label="设备名称"><el-input v-model="devForm.name" placeholder="如：Core-SW-01"/></el-form-item>
        <el-form-item label="品牌"><el-input v-model="devForm.brand" placeholder="如：Huawei"/></el-form-item>
        <el-form-item label="型号"><el-input v-model="devForm.model" placeholder="如：S6730-H48X6C"/></el-form-item>
        <el-form-item label="IP地址"><el-input v-model="devForm.ip" placeholder="192.168.1.1"/></el-form-item>
        <el-form-item label="U位">U{{ devForm.ustart }} - U{{ devForm.ustart + devForm.uheight - 1 }}</el-form-item>
        <el-form-item label="高度(U)">
          <el-radio-group v-model="devForm.uheight" size="small">
            <el-radio-button :label="1">1U</el-radio-button>
            <el-radio-button :label="2">2U</el-radio-button>
            <el-radio-button :label="4">4U</el-radio-button>
            <el-radio-button :label="8">8U</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDev = false">取消</el-button>
        <el-button type="primary" @click="saveDev" :loading="loading">{{ editingDev ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>

    <!-- 设备详情弹窗（含接口-座位映射） -->
    <el-dialog v-model="showDevInfo" title="设备详情" width="600px">
      <div v-if="selectedDev">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="名称" :span="2">{{ selectedDev.name }}</el-descriptions-item>
          <el-descriptions-item label="品牌">{{ selectedDev.vendor || '--' }}</el-descriptions-item>
          <el-descriptions-item label="型号">{{ selectedDev.model || '--' }}</el-descriptions-item>
          <el-descriptions-item label="IP">{{ selectedDev.ip || '--' }}</el-descriptions-item>
          <el-descriptions-item label="U位">U{{ selectedDev.u_start }}-U{{ selectedDev.u_start + selectedDev.u_height - 1 }}（{{ selectedDev.u_height }}U）</el-descriptions-item>
        </el-descriptions>

        <!-- 接口-座位映射 -->
        <el-divider>🔗 接口→座位映射</el-divider>
        <div style="display:flex;gap:6px;margin-bottom:8px;align-items:center">
          <el-input v-model="seatForm.seat" placeholder="座位号" size="small" style="width:90px"/>
          <span style="color:#94a3b8">→</span>
          <el-input v-model="seatForm.port" placeholder="接口名" size="small" style="width:150px"/>
          <el-input v-model="seatForm.remark" placeholder="备注(可选)" size="small" style="width:120px"/>
          <el-button type="primary" size="small" @click="addSeat" :disabled="!seatForm.seat||!seatForm.port">添加</el-button>
        </div>
        <el-table :data="currentSeats" size="small" border max-height="200" empty-text="暂无映射">
          <el-table-column prop="seat" label="座位" width="80"/>
          <el-table-column prop="port" label="接口" width="160"/>
          <el-table-column prop="remark" label="备注" min-width="120"/>
          <el-table-column label="操作" width="60" align="center">
            <template #default="{row}">
              <el-button :icon="Delete" circle size="small" type="danger" @click="delSeat(row.id)"/>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showDevInfo = false">关闭</el-button>
        <el-button type="primary" @click="editDev">修改设备</el-button>
        <el-button type="danger" @click="delDev">删除设备</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="showImportDialog" title="📥 批量导入接口-座位映射" width="600px">
      <el-alert title="导入格式说明" type="info" :closable="false" style="margin-bottom:12px">
        <div style="font-size:12px;line-height:1.8">
          每行一条：<code>座位号,接口名,备注(可选)</code><br/>
          示例：<br/>
          <code>A01,GE0/0/1,办公区-张三</code><br/>
          <code>A02,GE0/0/2,办公区-李四</code><br/>
          <code>B01,GE0/0/3,会议室</code>
        </div>
      </el-alert>
      <el-form label-width="80px">
        <el-form-item label="目标机柜">
          <el-select v-model="importRackId" placeholder="选择机柜" style="width:100%">
            <el-option v-for="r in racks" :key="r.id" :label="`${r.name} (${r.region||'--'})`" :value="r.id"/>
          </el-select>
        </el-form-item>
        <el-form-item label="目标设备">
          <el-select v-model="importDevId" placeholder="选择设备" style="width:100%" :disabled="!importRackId">
            <el-option v-for="d in importDevices" :key="d.id" :label="`${d.name} (U${d.u_start})`" :value="d.id"/>
          </el-select>
        </el-form-item>
        <el-form-item label="映射数据">
          <el-input v-model="importData" type="textarea" :rows="10" placeholder="座位号,接口名,备注&#10;A01,GE0/0/1&#10;A02,GE0/0/2&#10;..."/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="doImport" :loading="importing" :disabled="!importRackId||!importDevId||!importData.trim()">
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'
import { useRequest } from '@/composables/useRequest'

const ROW_HEIGHT = 14
const GAP = 1

const { loading, get } = useRequest()
const racks = ref<any[]>([])
const cur = ref<number | null>(null)
const regions = ref<string[]>([])
const regionFilter = ref('')

const showAddRack = ref(false)
const showAddDev = ref(false)
const showDevInfo = ref(false)
const showImportDialog = ref(false)
const editingRack = ref<any>(null)
const editingDev = ref<any>(null)
const selectedRack = ref<any>(null)
const selectedDev = ref<any>(null)

const rackForm = reactive({ name: '', loc: '', rows: 42, region: '' })
const devForm = reactive({ name: '', brand: '', model: '', ip: '', ustart: 1, uheight: 1 })
const seatForm = reactive({ seat: '', port: '', remark: '' })
const currentSeats = ref<any[]>([])

// 导入
const importRackId = ref<number | null>(null)
const importDevId = ref<number | null>(null)
const importData = ref('')
const importing = ref(false)

interface Block { key: string; type: 'empty' | 'device'; startU: number; count: number; device?: any }

const filteredRacks = computed(() => {
  if (!regionFilter.value) return racks.value
  return racks.value.filter(r => r.region === regionFilter.value)
})

const importDevices = computed(() => {
  if (!importRackId.value) return []
  const rack = racks.value.find(r => r.id === importRackId.value)
  return rack?.devices || []
})

watch(importRackId, () => { importDevId.value = null })

async function loadRacks() {
  const q = regionFilter.value ? `?region=${encodeURIComponent(regionFilter.value)}` : ''
  const data = await get<any[]>(`/api/rack/racks${q}`)
  if (data) { racks.value = data; if (data.length && !cur.value) cur.value = data[0].id }
}
async function loadRegions() {
  try { const r = await fetch('/api/rack/regions'); regions.value = await r.json() } catch { regions.value = [] }
}
async function loadSeats(devId: number) {
  try { const r = await fetch(`/api/rack/seats?device_id=${devId}`); currentSeats.value = await r.json() } catch { currentSeats.value = [] }
}

// 机柜
function editRack(r: any) {
  editingRack.value = r; rackForm.name = r.name; rackForm.loc = r.location; rackForm.rows = r.rows; rackForm.region = r.region || ''
  showAddRack.value = true
}
async function saveRack() {
  if (!rackForm.name) { ElMessage.warning('请输入名称'); return }
  if (editingRack.value) {
    const p = new URLSearchParams({ rack_id: String(editingRack.value.id), name: rackForm.name, location: rackForm.loc, rows: String(rackForm.rows), region: rackForm.region })
    await fetch(`/api/rack/racks/update?${p}`, { method: 'POST' })
    ElMessage.success('已更新')
  } else {
    const p = new URLSearchParams({ name: rackForm.name, location: rackForm.loc, rows: String(rackForm.rows), region: rackForm.region })
    await fetch(`/api/rack/racks?${p}`, { method: 'POST' })
    ElMessage.success('已创建')
  }
  showAddRack.value = false; editingRack.value = null
  rackForm.name = ''; rackForm.loc = ''; rackForm.rows = 42; rackForm.region = ''
  await loadRegions(); await loadRacks()
}
async function delRack(r: any) {
  try { await ElMessageBox.confirm(`确定删除机柜 "${r.name}"？`, '确认删除', { type: 'warning' }); await fetch(`/api/rack/racks/${r.id}`, { method: 'DELETE' }); ElMessage.success('已删除'); await loadRacks() } catch { /*取消*/ }
}

// 设备
function mergedBlocks(rack: any): Block[] {
  const devices = (rack.devices || []) as any[]
  const rows = rack.rows as number
  const blocks: Block[] = []
  const sorted = [...devices].sort((a, b) => a.u_start - b.u_start)
  if (!sorted.length) { blocks.push({ key: 'empty-all', type: 'empty', startU: 1, count: rows }); return blocks }
  let cursor = 1
  for (const dev of sorted) {
    if (cursor < dev.u_start) blocks.push({ key: `empty-${cursor}`, type: 'empty', startU: cursor, count: dev.u_start - cursor })
    blocks.push({ key: `dev-${dev.id}`, type: 'device', startU: dev.u_start, count: dev.u_height, device: dev })
    cursor = dev.u_start + dev.u_height
  }
  if (cursor <= rows) blocks.push({ key: `empty-${cursor}`, type: 'empty', startU: cursor, count: rows - cursor + 1 })
  return blocks
}
function getDevBlockClass(dev: any) {
  const n = (dev.name || '').toLowerCase()
  if (n.includes('sw') || n.includes('交换')) return 'switch'
  if (n.includes('rt') || n.includes('路由') || n.includes('fw')) return 'router'
  if (n.includes('srv') || n.includes('服务')) return 'server'
  if (n.includes('ups') || n.includes('电源')) return 'ups'
  return 'generic'
}
function onEmptyClick(rack: any, u: number) {
  selectedRack.value = rack; editingDev.value = null
  devForm.ustart = u; devForm.uheight = 1; devForm.name = ''; devForm.brand = ''; devForm.model = ''; devForm.ip = ''
  showAddDev.value = true
}
async function onDevClick(rack: any, dev: any) {
  selectedRack.value = rack; selectedDev.value = dev; showDevInfo.value = true; await loadSeats(dev.id)
}
function editDev() {
  if (!selectedDev.value) return; showDevInfo.value = false; editingDev.value = selectedDev.value
  devForm.name = selectedDev.value.name; devForm.brand = selectedDev.value.vendor || ''; devForm.model = selectedDev.value.model || ''
  devForm.ip = selectedDev.value.ip || ''; devForm.ustart = selectedDev.value.u_start; devForm.uheight = selectedDev.value.u_height
  showAddDev.value = true
}
async function delDev() {
  if (!selectedDev.value) return
  try { await ElMessageBox.confirm(`确定删除 "${selectedDev.value.name}"？`, '确认删除', { type: 'warning' }); await fetch(`/api/rack/devices/${selectedDev.value.id}`, { method: 'DELETE' }); ElMessage.success('已删除'); showDevInfo.value = false; await loadRacks() } catch { /*取消*/ }
}
async function saveDev() {
  if (!devForm.name) { ElMessage.warning('请输入设备名称'); return }; if (!selectedRack.value) return
  const p = new URLSearchParams({ rack_id: String(selectedRack.value.id), name: devForm.name, vendor: devForm.brand, model: devForm.model, ip: devForm.ip, u_start: String(devForm.ustart), u_height: String(devForm.uheight) })
  if (editingDev.value) p.set('dev_id', String(editingDev.value.id))
  await fetch(`/api/rack/devices?${p}`, { method: 'POST' })
  ElMessage.success(editingDev.value ? '已更新' : '已添加'); showAddDev.value = false; editingDev.value = null
  devForm.name = ''; devForm.brand = ''; devForm.model = ''; devForm.ip = ''
  await loadRacks()
}

// 接口-座位映射
async function addSeat() {
  if (!selectedDev.value || !selectedRack.value || !seatForm.seat || !seatForm.port) return
  const p = new URLSearchParams({ rack_id: String(selectedRack.value.id), device_id: String(selectedDev.value.id), device_name: selectedDev.value.name, seat: seatForm.seat, port: seatForm.port, remark: seatForm.remark })
  await fetch(`/api/rack/seats?${p}`, { method: 'POST' })
  ElMessage.success('已添加'); seatForm.seat = ''; seatForm.port = ''; seatForm.remark = ''
  await loadSeats(selectedDev.value.id); await loadRacks()
}
async function delSeat(id: number) {
  await fetch(`/api/rack/seats/${id}`, { method: 'DELETE' })
  ElMessage.success('已删除')
  if (selectedDev.value) await loadSeats(selectedDev.value.id)
  await loadRacks()
}

// 批量导入
async function doImport() {
  if (!importRackId.value || !importDevId.value || !importData.value.trim()) return
  importing.value = true
  const rack = racks.value.find(r => r.id === importRackId.value)
  const dev = importDevices.value.find(d => d.id === importDevId.value)
  if (!rack || !dev) { ElMessage.error('请选择机柜和设备'); importing.value = false; return }
  const p = new URLSearchParams({ rack_id: String(rack.id), device_id: String(dev.id), device_name: dev.name, data: importData.value })
  const r = await fetch(`/api/rack/seats/import?${p}`, { method: 'POST' })
  const result = await r.json()
  ElMessage.success(`成功导入 ${result.imported} 条映射`)
  importing.value = false; showImportDialog.value = false; importData.value = ''; importRackId.value = null; importDevId.value = null
  await loadRacks()
}

onMounted(async () => { await loadRegions(); await loadRacks() })
</script>

<style scoped>
.page { padding: 20px; min-height: 100vh; background: #f8fafc; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 8px; }
.page-header h2 { margin: 0; font-size: 20px; }

.room-view { display: flex; gap: 24px; overflow-x: auto; padding-bottom: 20px; min-height: calc(100vh - 140px); }
.rack-column { flex-shrink: 0; display: flex; flex-direction: column; align-items: center; cursor: pointer; transition: transform .2s; }
.rack-column:hover { transform: translateY(-2px); }
.rack-column.active .rack-frame { box-shadow: 0 0 0 3px #6366f1, 0 8px 24px rgba(0,0,0,.12); }

.rack-frame { width: 165px; background: linear-gradient(180deg, #e2e8f0 0%, #f1f5f9 100%); border: 2px solid #94a3b8; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,.08); overflow: hidden; }
.rack-header { background: #334155; color: #fff; padding: 8px 10px; text-align: center; }
.rack-name { display: block; font-weight: 600; font-size: 13px; }
.rack-loc { display: block; font-size: 10px; color: #94a3b8; margin-top: 2px; }

.rack-body { display: flex; flex-direction: column; padding: 4px; gap: 1px; }
.rack-u { display: flex; align-items: center; padding: 0 6px; font-size: 9px; border: 1px solid #cbd5e1; background: #fff; transition: filter .15s; }
.rack-u.empty { background: #f8fafc; height: 14px; }
.rack-u.empty:hover { filter: brightness(.92); cursor: pointer; }
.rack-u.merged { border-radius: 3px; cursor: pointer; flex-direction: column; align-items: flex-start; padding: 4px 6px; overflow: hidden; }
.rack-u.merged:hover { filter: brightness(.9); }
.rack-u.merged .u-num { width: auto; margin-bottom: 2px; }
.merged-body { flex: 1; display: flex; flex-direction: column; gap: 1px; width: 100%; }
.merged-name { font-size: 10px; font-weight: 600; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.merged-model { font-size: 8px; color: #64748b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.merged-seat { font-size: 8px; color: #6366f1; }
.u-num { width: 22px; color: #64748b; font-family: monospace; font-size: 9px; }

.rack-u.merged.switch { background: #dcfce7; border-color: #22c55e; }
.rack-u.merged.router { background: #fef3c7; border-color: #f59e0b; }
.rack-u.merged.server { background: #ede9fe; border-color: #8b5cf6; }
.rack-u.merged.ups { background: #fee2e2; border-color: #ef4444; }
.rack-u.merged.generic { background: #dbeafe; border-color: #3b82f6; }

.rack-footer { background: #334155; color: #94a3b8; text-align: center; padding: 4px; font-size: 10px; }
.rack-actions { margin-top: 10px; display: flex; gap: 8px; }

.dev-popover { font-size: 12px; }
.dev-pop-title { font-weight: 600; font-size: 14px; color: #1e293b; }
.dev-pop-row { display: flex; justify-content: space-between; align-items: center; padding: 3px 0; color: #475569; }
.dev-pop-label { color: #94a3b8; font-size: 11px; }
.dev-pop-row code { background: #f1f5f9; padding: 1px 6px; border-radius: 3px; font-size: 11px; color: #6366f1; }
</style>

<template>
  <div class="page">
    <div class="page-header">
      <h2>🗄️ 机柜管理</h2>
      <el-button type="primary" @click="showAddRack = true">+ 新增机柜</el-button>
    </div>

    <!-- 机房视图：多机柜并排 -->
    <div class="room-view">
      <div v-for="r in racks" :key="r.id" class="rack-column" :class="{ active: cur === r.id }" @click="cur = r.id">
        <div class="rack-frame">
          <!-- 机柜顶部标签 -->
          <div class="rack-header">
            <span class="rack-name">{{ r.name || '未命名' }}</span>
            <span class="rack-loc">{{ r.location || '--' }}</span>
            <el-tag size="small" type="info">{{ r.devices?.length || 0 }} 设备</el-tag>
          </div>

          <!-- 机柜主体：合并视图（从下往上） -->
          <div class="rack-body">
            <template v-for="blk in mergedBlocks(r)" :key="blk.key">
              <!-- 空闲 U 位 -->
              <div
                v-if="blk.type === 'empty'"
                v-for="u in blk.count"
                :key="'e' + u + '_' + blk.startU"
                class="rack-u empty"
                @click.stop="onEmptyClick(r, blk.startU)"
              >
                <span class="u-num">{{ blk.startU }}</span>
              </div>
              <!-- 设备合并块 -->
              <el-popover
                v-else
                trigger="hover"
                placement="right"
                :width="250"
                :show-after="300"
                :hide-after="100"
              >
                <template #reference>
                  <div
                    class="rack-u merged"
                    :class="getDevBlockClass(blk.device)"
                    :style="{ height: blk.count * ROW_HEIGHT + (blk.count - 1) * GAP + 'px' }"
                    @click.stop="onDevClick(r, blk.device)"
                  >
                    <span class="u-num">{{ blk.startU }}</span>
                    <div class="merged-body">
                      <span class="merged-name">{{ blk.device.name }}</span>
                      <span v-if="blk.device.model" class="merged-model">{{ blk.device.model }}</span>
                    </div>
                  </div>
                </template>
                <!-- 悬停弹窗：设备详情（无密码） -->
                <div class="dev-popover">
                  <div class="dev-pop-title">{{ blk.device.name }}</div>
                  <el-divider style="margin:8px 0"/>
                  <div class="dev-pop-row">
                    <span class="dev-pop-label">品牌</span>
                    <span>{{ blk.device.vendor || '--' }}</span>
                  </div>
                  <div class="dev-pop-row">
                    <span class="dev-pop-label">型号</span>
                    <span>{{ blk.device.model || '--' }}</span>
                  </div>
                  <div class="dev-pop-row">
                    <span class="dev-pop-label">IP 地址</span>
                    <code>{{ blk.device.ip || '--' }}</code>
                  </div>
                  <div class="dev-pop-row">
                    <span class="dev-pop-label">占用 U 位</span>
                    <span>U{{ blk.device.u_start }} - U{{ blk.device.u_start + blk.device.u_height - 1 }}（{{ blk.device.u_height }}U）</span>
                  </div>
                  <div class="dev-pop-row">
                    <span class="dev-pop-label">状态</span>
                    <el-tag :type="blk.device.status === 'offline' ? 'danger' : 'success'" size="small">
                      {{ blk.device.status === 'offline' ? '离线' : '在线' }}
                    </el-tag>
                  </div>
                </div>
              </el-popover>
            </template>
          </div>

          <!-- 机柜底部 -->
          <div class="rack-footer">
            <span>{{ r.rows }}U</span>
          </div>
        </div>
        <!-- 操作按钮 -->
        <div class="rack-actions">
          <el-button size="small" @click="editRack(r)">编辑</el-button>
          <el-button size="small" type="danger" @click="delRack(r)">删除</el-button>
        </div>
      </div>

      <el-empty v-if="!racks.length" description="暂无数据，点击右上角新增机柜" style="width:100%"/>
    </div>

    <!-- 新增/编辑机柜弹窗 -->
    <el-dialog v-model="showAddRack" :title="editingRack ? '编辑机柜' : '新增机柜'" width="400px">
      <el-form label-width="80px">
        <el-form-item label="名称"><el-input v-model="rackForm.name" placeholder="如：A1-01"/></el-form-item>
        <el-form-item label="位置"><el-input v-model="rackForm.loc" placeholder="如：机房A第1排"/></el-form-item>
        <el-form-item label="U位高度"><el-input-number v-model="rackForm.rows" :min="4" :max="48"/></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddRack = false">取消</el-button>
        <el-button type="primary" @click="saveRack" :loading="loading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加设备弹窗 -->
    <el-dialog v-model="showAddDev" title="添加设备" width="420px">
      <el-alert v-if="selectedRack" :title="`添加到: ${selectedRack.name} 第 ${devForm.ustart}U`" type="info" :closable="false" style="margin-bottom:12px"/>
      <el-form label-width="80px">
        <el-form-item label="设备名称"><el-input v-model="devForm.name" placeholder="如：Core-SW-01"/></el-form-item>
        <el-form-item label="品牌"><el-input v-model="devForm.brand" placeholder="如：Huawei"/></el-form-item>
        <el-form-item label="型号"><el-input v-model="devForm.model" placeholder="如：S6730-H48X6C"/></el-form-item>
        <el-form-item label="IP地址"><el-input v-model="devForm.ip" placeholder="192.168.1.1"/></el-form-item>
        <el-form-item label="占用U位">U{{ devForm.ustart }} - U{{ devForm.ustart + devForm.uheight - 1 }}</el-form-item>
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
        <el-button type="primary" @click="addDev" :loading="loading">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRequest } from '@/composables/useRequest'

const ROW_HEIGHT = 14   // 每 1U 的高度（px）
const GAP = 1           // 行间距（px）

const { loading, get } = useRequest()
const racks = ref<any[]>([])
const cur = ref<number | null>(null)
const showAddRack = ref(false)
const showAddDev = ref(false)
const editingRack = ref<any>(null)
const selectedRack = ref<any>(null)

const rackForm = reactive({ name: '', loc: '', rows: 42 })
const devForm = reactive({ name: '', brand: '', model: '', ip: '', ustart: 1, uheight: 1 })

interface Block {
  key: string
  type: 'empty' | 'device'
  startU: number    // 起始 U 号（从上到下编号）
  count: number     // 占用多少个 1U 单元
  device?: any
}

async function loadRacks() {
  const data = await get<any[]>('/api/rack/racks')
  if (data) {
    racks.value = data
    if (data.length && !cur.value) cur.value = data[0].id
  }
}

/**
 * 核心：将机柜的 U 位按设备合并成连续块
 * 例如：设备占用 U5-U6（2U）→ 生成一个 type='device', count=2 的合并块
 */
function mergedBlocks(rack: any): Block[] {
  const devices = (rack.devices || []) as any[]
  const rows = rack.rows as number
  const blocks: Block[] = []

  // 先按 u_start 排序
  const sorted = [...devices].sort((a, b) => a.u_start - b.u_start)

  if (!sorted.length) {
    // 无设备 → 全部空闲
    blocks.push({ key: 'empty-all', type: 'empty', startU: 1, count: rows })
    return blocks
  }

  let cursor = 1  // 当前扫描到的 U 位（从上到下：1=最顶）
  for (const dev of sorted) {
    // 设备之前的空闲区域
    if (cursor < dev.u_start) {
      blocks.push({
        key: `empty-${cursor}`,
        type: 'empty',
        startU: cursor,
        count: dev.u_start - cursor,
      })
    }
    // 设备本身（合并为一块）
    blocks.push({
      key: `dev-${dev.id}`,
      type: 'device',
      startU: dev.u_start,
      count: dev.u_height,
      device: dev,
    })
    cursor = dev.u_start + dev.u_height
  }

  // 最后一个设备之后的空闲区域
  if (cursor <= rows) {
    blocks.push({
      key: `empty-${cursor}`,
      type: 'empty',
      startU: cursor,
      count: rows - cursor + 1,
    })
  }

  return blocks
}

/** 设备块颜色类型 */
function getDevBlockClass(dev: any) {
  const name = (dev.name || '').toLowerCase()
  if (name.includes('sw') || name.includes('交换')) return 'switch'
  if (name.includes('rt') || name.includes('路由') || name.includes('fw')) return 'router'
  if (name.includes('srv') || name.includes('服务')) return 'server'
  if (name.includes('ups') || name.includes('电源')) return 'ups'
  return 'generic'
}

function onEmptyClick(rack: any, u: number) {
  selectedRack.value = rack
  devForm.ustart = u
  devForm.uheight = 1
  devForm.name = ''; devForm.brand = ''; devForm.model = ''; devForm.ip = ''
  showAddDev.value = true
}

function onDevClick(rack: any, dev: any) {
  ElMessageBox.confirm(
    `设备 "${dev.name}" 位于 U${dev.u_start}-U${dev.u_start + dev.u_height - 1}，需要删除吗？`,
    '设备信息',
    { confirmButtonText: '删除', cancelButtonText: '关闭', type: 'info' }
  ).then(async () => {
    await fetch(`/api/rack/devices/${dev.id}`, { method: 'DELETE' })
    ElMessage.success('设备已删除')
    await loadRacks()
  }).catch(() => { /* 取消 */ })
}

function editRack(r: any) {
  editingRack.value = r
  rackForm.name = r.name
  rackForm.loc = r.location
  rackForm.rows = r.rows
  showAddRack.value = true
}

async function saveRack() {
  if (!rackForm.name) { ElMessage.warning('请输入机柜名称'); return }
  const params = new URLSearchParams({
    name: rackForm.name, location: rackForm.loc, rows: String(rackForm.rows),
  })
  await fetch(`/api/rack/racks?${params}`, { method: 'POST' })
  ElMessage.success(editingRack.value ? '机柜已更新' : '机柜已创建')
  showAddRack.value = false; editingRack.value = null
  rackForm.name = ''; rackForm.loc = ''; rackForm.rows = 42
  await loadRacks()
}

async function delRack(r: any) {
  try {
    await ElMessageBox.confirm(`确定删除机柜 "${r.name}" 吗？`, '确认删除', { type: 'warning' })
    await fetch(`/api/rack/racks/${r.id}`, { method: 'DELETE' })
    ElMessage.success('已删除')
    await loadRacks()
  } catch { /* 取消 */ }
}

async function addDev() {
  if (!devForm.name) { ElMessage.warning('请输入设备名称'); return }
  if (!selectedRack.value) return
  const params = new URLSearchParams({
    rack_id: String(selectedRack.value.id),
    name: devForm.name, vendor: devForm.brand, model: devForm.model, ip: devForm.ip,
    u_start: String(devForm.ustart), u_height: String(devForm.uheight),
  })
  await fetch(`/api/rack/devices?${params}`, { method: 'POST' })
  ElMessage.success('设备已添加')
  showAddDev.value = false
  devForm.name = ''; devForm.brand = ''; devForm.model = ''; devForm.ip = ''
  await loadRacks()
}

onMounted(loadRacks)
</script>

<style scoped>
.page { padding: 20px; min-height: 100vh; background: #f8fafc; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; }

/* 机房视图 */
.room-view {
  display: flex; gap: 24px; overflow-x: auto;
  padding-bottom: 20px; min-height: calc(100vh - 140px);
}
.rack-column {
  flex-shrink: 0; display: flex; flex-direction: column;
  align-items: center; cursor: pointer; transition: transform .2s;
}
.rack-column:hover { transform: translateY(-2px); }
.rack-column.active .rack-frame { box-shadow: 0 0 0 3px #6366f1, 0 8px 24px rgba(0,0,0,.12); }

/* 机柜外框 */
.rack-frame {
  width: 160px; background: linear-gradient(180deg, #e2e8f0 0%, #f1f5f9 100%);
  border: 2px solid #94a3b8; border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,.08); overflow: hidden;
}

/* 机柜头部 */
.rack-header { background: #334155; color: #fff; padding: 8px 10px; text-align: center; }
.rack-name { display: block; font-weight: 600; font-size: 13px; }
.rack-loc { display: block; font-size: 10px; color: #94a3b8; margin-top: 2px; }

/* 机柜主体 */
.rack-body {
  display: flex; flex-direction: column; padding: 4px; gap: 1px;
}

/* U 位基础样式 */
.rack-u {
  display: flex; align-items: center; padding: 0 6px;
  font-size: 9px; border: 1px solid #cbd5e1;
  background: #fff; transition: filter .15s;
}
.rack-u.empty { background: #f8fafc; height: 14px; }
.rack-u.empty:hover { filter: brightness(.92); cursor: pointer; }

/* 合并设备块 */
.rack-u.merged {
  border-radius: 3px; cursor: pointer;
  flex-direction: column; align-items: flex-start;
  padding: 4px 6px; overflow: hidden;
}
.rack-u.merged:hover { filter: brightness(.9); }
.rack-u.merged .u-num { width: auto; margin-bottom: 2px; }
.merged-body { flex: 1; display: flex; flex-direction: column; gap: 1px; width: 100%; }
.merged-name {
  font-size: 10px; font-weight: 600; color: #1e293b;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.merged-model {
  font-size: 8px; color: #64748b;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.u-num {
  width: 22px; color: #64748b; font-family: monospace; font-size: 9px;
}

/* 设备类型颜色 */
.rack-u.merged.switch   { background: #dcfce7; border-color: #22c55e; }
.rack-u.merged.router   { background: #fef3c7; border-color: #f59e0b; }
.rack-u.merged.server   { background: #ede9fe; border-color: #8b5cf6; }
.rack-u.merged.ups      { background: #fee2e2; border-color: #ef4444; }
.rack-u.merged.generic  { background: #dbeafe; border-color: #3b82f6; }

/* 机柜底部 */
.rack-footer { background: #334155; color: #94a3b8; text-align: center; padding: 4px; font-size: 10px; }

/* 操作按钮 */
.rack-actions { margin-top: 10px; display: flex; gap: 8px; }

/* ── 悬停 Popover ── */
.dev-popover { font-size: 12px; }
.dev-pop-title { font-weight: 600; font-size: 14px; color: #1e293b; }
.dev-pop-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 3px 0; color: #475569;
}
.dev-pop-label { color: #94a3b8; font-size: 11px; }
.dev-pop-row code {
  background: #f1f5f9; padding: 1px 6px; border-radius: 3px;
  font-size: 11px; color: #6366f1;
}
</style>

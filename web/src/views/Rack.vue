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
          <!-- U位单元（从下往上，符合真实机柜） -->
          <div class="rack-body">
            <div v-for="u in r.rows" :key="u" class="rack-u" :class="getUClass(r, u)" :title="getUTitle(r, u)" @click.stop="onUClick(r, u)">
              <span class="u-num">{{ r.rows - u + 1 }}</span>
              <span v-if="getUDevice(r, u)" class="u-device">{{ getUDevice(r, u).name }}</span>
            </div>
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

      <!-- 空状态 -->
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
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRequest } from '@/composables/useRequest'

const { loading, get } = useRequest()
const racks = ref<any[]>([])
const cur = ref<number | null>(null)
const showAddRack = ref(false)
const showAddDev = ref(false)
const editingRack = ref<any>(null)
const selectedRack = ref<any>(null)

const rackForm = reactive({ name: '', loc: '', rows: 42 })
const devForm = reactive({ name: '', brand: '', model: '', ip: '', ustart: 1, uheight: 1 })

async function loadRacks() {
  const data = await get<any[]>('/api/rack/racks')
  if (data) {
    racks.value = data
    if (data.length && !cur.value) cur.value = data[0].id
  }
}

function getUDevice(rack: any, u: number) {
  const realU = rack.rows - u + 1  // 界面显示从下到上，实际存储从上到下
  return (rack.devices || []).find((d: any) => realU >= d.u_start && realU < d.u_start + d.u_height)
}

function getUClass(rack: any, u: number) {
  const dev = getUDevice(rack, u)
  if (!dev) return 'empty'
  // 根据设备类型返回不同颜色
  const name = (dev.name || '').toLowerCase()
  if (name.includes('sw') || name.includes('交换')) return 'occupied switch'
  if (name.includes('rt') || name.includes('路由') || name.includes('fw')) return 'occupied router'
  if (name.includes('srv') || name.includes('服务')) return 'occupied server'
  if (name.includes('ups') || name.includes('电源')) return 'occupied ups'
  return 'occupied'
}

function getUTitle(rack: any, u: number) {
  const dev = getUDevice(rack, u)
  if (!dev) return `U${rack.rows - u + 1} 空闲`
  return `U${rack.rows - u + 1} ${dev.name} (${dev.vendor || '--'})`
}

function onUClick(rack: any, u: number) {
  const realU = rack.rows - u + 1
  if (getUDevice(rack, u)) {
    ElMessage.warning('该 U 位已被占用')
    return
  }
  // 检查上方是否有足够空间放置多U设备
  selectedRack.value = rack
  devForm.ustart = realU
  showAddDev.value = true
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
    name: rackForm.name,
    location: rackForm.loc,
    rows: String(rackForm.rows)
  })
  await fetch(`/api/rack/racks?${params}`, { method: 'POST' })
  ElMessage.success(editingRack.value ? '机柜已更新' : '机柜已创建')
  showAddRack.value = false
  editingRack.value = null
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
    name: devForm.name,
    vendor: devForm.brand,
    model: devForm.model,
    ip: devForm.ip,
    u_start: String(devForm.ustart),
    u_height: String(devForm.uheight)
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

/* 机房视图 - 多机柜并排 */
.room-view {
  display: flex;
  gap: 24px;
  overflow-x: auto;
  padding-bottom: 20px;
  min-height: calc(100vh - 140px);
}

.rack-column {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform .2s;
}
.rack-column:hover { transform: translateY(-2px); }
.rack-column.active .rack-frame { box-shadow: 0 0 0 3px #6366f1, 0 8px 24px rgba(0,0,0,.12); }

/* 机柜外框 */
.rack-frame {
  width: 160px;
  background: linear-gradient(180deg, #e2e8f0 0%, #f1f5f9 100%);
  border: 2px solid #94a3b8;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,.08);
  overflow: hidden;
}

/* 机柜头部 */
.rack-header {
  background: #334155;
  color: #fff;
  padding: 8px 10px;
  text-align: center;
}
.rack-name { display: block; font-weight: 600; font-size: 13px; }
.rack-loc { display: block; font-size: 10px; color: #94a3b8; margin-top: 2px; }

/* 机柜主体 - U位 */
.rack-body {
  display: flex;
  flex-direction: column;
  padding: 4px;
  gap: 1px;
}
.rack-u {
  height: 14px;
  display: flex;
  align-items: center;
  padding: 0 6px;
  font-size: 9px;
  border: 1px solid #cbd5e1;
  background: #fff;
  transition: all .15s;
}
.rack-u:hover { filter: brightness(.95); }

.u-num {
  width: 22px;
  color: #64748b;
  font-family: monospace;
}
.u-device {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #1e293b;
  font-weight: 500;
}

/* U位状态颜色 */
.rack-u.empty { background: #f8fafc; }
.rack-u.occupied { background: #dbeafe; border-color: #3b82f6; }
.rack-u.occupied.switch { background: #dcfce7; border-color: #22c55e; }
.rack-u.occupied.router { background: #fef3c7; border-color: #f59e0b; }
.rack-u.occupied.server { background: #ede9fe; border-color: #8b5cf6; }
.rack-u.occupied.ups { background: #fee2e2; border-color: #ef4444; }

/* 机柜底部 */
.rack-footer {
  background: #334155;
  color: #94a3b8;
  text-align: center;
  padding: 4px;
  font-size: 10px;
}

/* 操作按钮 */
.rack-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}
</style>

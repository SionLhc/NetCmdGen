<template>
  <div class="page"><h2>🗄️ 机柜管理</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="机柜"><el-select v-model="cur" placeholder="选择机柜" style="width:180px" @change="refresh"><el-option v-for="r in racks" :key="r.id" :label="r.name" :value="r.id"/></el-select></el-form-item>
      <el-form-item><el-button @click="showAddRack=true">新增机柜</el-button>
      <el-button type="primary" @click="showAddDev=true">添加设备</el-button></el-form-item>
    </el-form></el-card>
    <!-- 机柜可视化 -->
    <div class="rack-vis" v-if="rack">
      <div class="rack-box"><div v-for="u in rack.rows" :key="u" class="rack-u" :class="{ occupied: occupiedAt(u) }" @click="pickU(u)">
        <span class="ru-num">{{ u }}</span><span v-if="occupiedAt(u)" class="ru-dev">{{ devNameAt(u) }}</span></div></div>
    </div>
    <el-empty v-if="!cur" description="请先选择机柜"/>
    <!-- 弹窗 -->
    <el-dialog v-model="showAddRack" title="新增机柜" width="360px"><el-form size="default" label-width="60px">
      <el-form-item label="名称"><el-input v-model="rackForm.name" placeholder="A1-01"/></el-form-item>
      <el-form-item label="位置"><el-input v-model="rackForm.loc" placeholder="机房A"/></el-form-item>
      <el-form-item label="U数"><el-input-number v-model="rackForm.rows" :min="4" :max="48"/></el-form-item>
    </el-form><template #footer><el-button @click="showAddRack=false">取消</el-button><el-button type="primary" @click="addRack" :loading="loading">保存</el-button></template></el-dialog>
    <el-dialog v-model="showAddDev" title="添加设备" width="360px"><el-form size="default" label-width="60px">
      <el-form-item label="名称"><el-input v-model="devForm.name" placeholder="Core-01"/></el-form-item>
      <el-form-item label="品牌"><el-input v-model="devForm.brand" placeholder="Huawei"/></el-form-item>
      <el-form-item label="U位">U{{ devForm.ustart }} - U{{ devForm.ustart + devForm.uheight - 1 }}</el-form-item>
      <el-form-item label="高度(U)"><el-input-number v-model="devForm.uheight" :min="1" :max="12" @change="onHeightChange"/></el-form-item>
    </el-form><template #footer><el-button @click="showAddDev=false">取消</el-button><el-button type="primary" @click="addDev" :loading="loading">保存</el-button></template></el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRequest } from '@/composables/useRequest'
const { loading, get, post } = useRequest()
const racks = ref<any[]>([]); const cur = ref(''); const rack = ref<any>(null); const showAddRack = ref(false); const showAddDev = ref(false)
const rackForm = reactive({ name: '', loc: '', rows: 42 })
const devForm = reactive({ name: '', brand: '', ustart: 1, uheight: 1 })
async function loadRacks() { const data = await get<any[]>('/api/rack/racks'); if (data) racks.value = data }
async function refresh() { if (!cur.value) return; const r = racks.value.find((x: any) => x.id === cur.value); if (r) rack.value = { ...r, devices: r.devices || [] } }
function occupiedAt(u: number) { if (!rack.value) return false; return (rack.value.devices || []).some((d: any) => u >= d.u_start && u < d.u_start + d.u_height) }
function devNameAt(u: number) { const d = (rack.value.devices || []).find((d: any) => u >= d.u_start && u < d.u_start + d.u_height); return d?.name || '' }
function pickU(u: number) { if (occupiedAt(u)) { ElMessage.warning('该 U 位已被占用'); return } devForm.ustart = u; showAddDev.value = true }
function onHeightChange() { /* U位变更 */ }
async function addRack() { if (!rackForm.name) { ElMessage.warning('请输入名称'); return }; const params = new URLSearchParams({ name: rackForm.name, location: rackForm.loc, rows: String(rackForm.rows) }); await fetch(`/api/rack/racks?${params}`, { method: 'POST' }); showAddRack.value = false; await loadRacks() }
async function addDev() { if (!devForm.name) { ElMessage.warning('请输入设备名称'); return }; const params = new URLSearchParams({ rack_id: String(cur.value), name: devForm.name, vendor: devForm.brand, u_start: String(devForm.ustart), u_height: String(devForm.uheight) }); await fetch(`/api/rack/devices?${params}`, { method: 'POST' }); showAddDev.value = false; refresh() }
onMounted(loadRacks)
</script>
<style scoped>
.page{padding:24px;max-width:1300px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}
.rack-vis{display:flex;gap:12px;justify-content:center}.rack-box{background:#f0f2f5;border:1px solid #e5e7eb;border-radius:8px;padding:4px}
.rack-u{display:flex;align-items:center;justify-content:space-between;width:220px;padding:2px 10px;font-size:12px;border-bottom:1px solid #e5e7eb;cursor:pointer;transition:.1s}.rack-u:hover{background:#e8edf2}
.rack-u.occupied{background:#fee2e2;cursor:not-allowed}.ru-num{color:#94a3b8;font-family:monospace;width:28px}.ru-dev{color:#475569;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
</style>

<template>
  <div class="ipam">
    <div class="ipam-header">
      <h2>📋 IP 地址管理</h2>
      <div>
        <el-button type="primary" @click="showAdd=true">+ 添加子网</el-button>
        <el-button @click="checkConflicts" :loading="checking">🔍 冲突检测</el-button>
      </div>
    </div>

    <!-- 冲突提示 -->
    <el-alert v-if="conflicts.length" type="warning" :closable="false" show-icon style="margin-bottom:12px">
      <template #title>检测到 {{ conflicts.length }} 个子网冲突</template>
      <div v-for="(c,i) in conflicts" :key="i">{{ c.subnet_a }} ↔ {{ c.subnet_b }} ({{ c.overlap }})</div>
    </el-alert>

    <!-- 子网网格 -->
    <div class="subnet-grid" v-if="subnets.length">
      <div class="sn-card" v-for="s in subnets" :key="s.id" @click="selectSubnet(s)" :class="{active: selected?.id===s.id}">
        <div class="sn-top">
          <span class="sn-name">{{ s.name || s.cidr }}</span>
          <span class="sn-vlan" v-if="s.vlan_id">VLAN {{ s.vlan_id }}</span>
        </div>
        <div class="sn-cidr">{{ s.cidr }}</div>
        <div class="sn-usage">
          <div class="usage-bar">
            <div class="usage-fill" :style="{width:s.usage_pct+'%',background:s.usage_pct>80?'#f56c6c':s.usage_pct>50?'#e6a23c':'#67c23a'}" />
          </div>
          <span class="usage-text">{{ s.used_ips }} / {{ s.usable_ips }} ({{ s.usage_pct }}%)</span>
        </div>
        <div class="sn-meta">
          <span>网关: {{ s.gateway || '—' }}</span>
          <el-button text size="small" type="danger" @click.stop="delSubnet(s.id)">删除</el-button>
        </div>
      </div>
    </div>
    <el-empty v-if="!subnets.length" description="暂无子网，点击「添加子网」开始管理" />

    <!-- IP 分配表格 -->
    <div v-if="selected" class="ip-section">
      <div class="ip-header">
        <h3>{{ selected.name || selected.cidr }}</h3>
        <div>
          <el-select v-model="filterStatus" size="small" style="width:100px" @change="loadIps">
            <el-option label="全部" value="all" />
            <el-option label="已用" value="used" />
            <el-option label="空闲" value="free" />
          </el-select>
        </div>
      </div>

      <!-- 热力图 -->
      <div class="heatmap" v-if="heatmap.length">
        <div class="hm-cell" v-for="h in heatmap" :key="h.ip"
          :class="h.status" :title="h.ip + ' - ' + h.status">
        </div>
      </div>

      <!-- IP 表格 -->
      <el-table :data="ips" size="small" border max-height="400" v-loading="ipLoading">
        <el-table-column prop="ip" label="IP 地址" width="140" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{row}">
            <el-tag :type="row.status==='used'?'success':'info'" size="small">{{ row.status==='used'?'已用':'空闲' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="device_name" label="设备名" />
        <el-table-column prop="user_name" label="使用人" width="80" />
        <el-table-column prop="mac" label="MAC" width="140" />
        <el-table-column prop="note" label="备注" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{row}">
            <el-button text size="small" type="primary" @click="editIp(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination v-if="ipTotal>ipLimit"
        :page-size="ipLimit" :total="ipTotal" :current-page="ipPage"
        layout="prev,next" @current-change="p=>{ipPage=p;loadIps()}" style="margin-top:10px;justify-content:center" />
    </div>

    <!-- 添加子网对话框 -->
    <el-dialog v-model="showAdd" title="添加子网" width="420px">
      <el-form label-width="80px" size="default">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如: 办公网段" />
        </el-form-item>
        <el-form-item label="网络地址">
          <el-input v-model="form.network" placeholder="192.168.1.0" />
        </el-form-item>
        <el-form-item label="前缀">
          <el-input-number v-model="form.prefix" :min="8" :max="30" />
        </el-form-item>
        <el-form-item label="网关">
          <el-input v-model="form.gateway" placeholder="192.168.1.1" />
        </el-form-item>
        <el-form-item label="VLAN">
          <el-input-number v-model="form.vlan" :min="0" :max="4094" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd=false">取消</el-button>
        <el-button type="primary" @click="addSubnet" :loading="adding">添加</el-button>
      </template>
    </el-dialog>

    <!-- 编辑 IP 对话框 -->
    <el-dialog v-model="showEdit" title="编辑 IP" width="380px">
      <el-form label-width="80px" size="default">
        <el-form-item label="IP">{{ editForm.ip }}</el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status">
            <el-option label="已用" value="used" />
            <el-option label="空闲" value="free" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备名"><el-input v-model="editForm.device_name" /></el-form-item>
        <el-form-item label="使用人"><el-input v-model="editForm.user_name" /></el-form-item>
        <el-form-item label="MAC"><el-input v-model="editForm.mac" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="editForm.note" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEdit=false">取消</el-button>
        <el-button type="primary" @click="saveIp" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const subnets = ref<any[]>([])
const selected = ref<any>(null)
const showAdd = ref(false)
const showEdit = ref(false)
const adding = ref(false)
const saving = ref(false)
const checking = ref(false)
const conflicts = ref<any[]>([])
const ips = ref<any[]>([])
const ipPage = ref(1)
const ipTotal = ref(0)
const ipLimit = 50
const ipLoading = ref(false)
const filterStatus = ref('all')
const heatmap = ref<any[]>([])

const form = ref({ name: '', network: '', prefix: 24, gateway: '', vlan: 0 })
const editForm = ref({ id: 0, ip: '', status: 'used', device_name: '', user_name: '', mac: '', note: '' })

async function loadSubnets() {
  const r = await fetch('/api/ipam/subnets')
  subnets.value = await r.json()
}

async function addSubnet() {
  adding.value = true
  const p = new URLSearchParams({ network: form.value.network, prefix: String(form.value.prefix), name: form.value.name, gateway: form.value.gateway, vlan_id: String(form.value.vlan) })
  const r = await fetch('/api/ipam/subnets?' + p, { method: 'POST' })
  if (r.ok) { showAdd.value = false; form.value = { name: '', network: '', prefix: 24, gateway: '', vlan: 0 }; loadSubnets(); ElMessage.success('已添加') }
  else { ElMessage.error('添加失败') }
  adding.value = false
}

async function delSubnet(id: number) {
  await fetch(`/api/ipam/subnets/${id}`, { method: 'DELETE' })
  if (selected.value?.id === id) selected.value = null
  loadSubnets()
}

function selectSubnet(s: any) {
  selected.value = s
  ipPage.value = 1
  filterStatus.value = 'all'
  loadIps()
  loadHeatmap()
}

async function loadIps() {
  if (!selected.value) return
  ipLoading.value = true
  const r = await fetch(`/api/ipam/ips?subnet_id=${selected.value.id}&status=${filterStatus.value}&page=${ipPage.value}&limit=${ipLimit}`)
  const d = await r.json()
  ips.value = d.ips
  ipTotal.value = d.total
  ipLoading.value = false
}

async function loadHeatmap() {
  if (!selected.value) return
  const r = await fetch(`/api/ipam/heatmap?subnet_id=${selected.value.id}`)
  const d = await r.json()
  heatmap.value = d.data || []
}

function editIp(row: any) {
  editForm.value = { ...row, id: row.id }
  showEdit.value = true
}

async function saveIp() {
  saving.value = true
  const p = new URLSearchParams({ status: editForm.value.status, device_name: editForm.value.device_name, user_name: editForm.value.user_name, mac: editForm.value.mac, note: editForm.value.note })
  await fetch(`/api/ipam/ips/${editForm.value.id}?` + p, { method: 'PUT' })
  showEdit.value = false; loadIps(); loadHeatmap(); loadSubnets()
  saving.value = false
}

async function checkConflicts() {
  checking.value = true
  const r = await fetch('/api/ipam/conflicts')
  const d = await r.json()
  conflicts.value = d.conflicts
  checking.value = false
  ElMessage.info(d.total ? `发现 ${d.total} 个冲突` : '无冲突 ✅')
}

onMounted(loadSubnets)
</script>

<style scoped>
.ipam { padding: 24px; max-width: 1300px; margin: 0 auto; }
.ipam-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.ipam-header h2 { font-size: 20px; margin: 0; }

/* 子网网格 */
.subnet-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-bottom: 20px; }
.sn-card { background: #fff; border: 1px solid #e8ecf1; border-radius: 10px; padding: 14px; cursor: pointer; transition: .2s; }
.sn-card:hover { border-color: #409eff; }
.sn-card.active { border-color: #409eff; background: #f0f7ff; }
.sn-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.sn-name { font-weight: 600; font-size: 14px; }
.sn-vlan { font-size: 11px; background: #409eff; color: #fff; border-radius: 4px; padding: 1px 6px; }
.sn-cidr { font-family: monospace; font-size: 13px; color: #606266; margin-bottom: 8px; }
.sn-usage { margin-bottom: 6px; }
.usage-bar { height: 6px; background: #f0f0f0; border-radius: 3px; overflow: hidden; margin-bottom: 3px; }
.usage-fill { height: 100%; border-radius: 3px; transition: width .3s; }
.usage-text { font-size: 11px; color: #909399; }
.sn-meta { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #909399; }

/* IP 区域 */
.ip-section { margin-top: 20px; }
.ip-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.ip-header h3 { margin: 0; font-size: 16px; }

/* 热力图 */
.heatmap { display: flex; flex-wrap: wrap; gap: 2px; background: #f5f7fa; border-radius: 6px; padding: 4px; margin-bottom: 10px; max-height: 60px; overflow-y: auto; }
.hm-cell { width: 12px; height: 12px; border-radius: 2px; }
.hm-cell.used { background: #67c23a; }
.hm-cell.free { background: #e8ecf1; }
</style>

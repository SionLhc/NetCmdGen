<template>
  <div class="winbox-layout">
    <!-- ═══ 左侧树形菜单 ═══ -->
    <div class="wb-sidebar">
      <div class="wb-device-bar">
        <el-select v-model="deviceId" placeholder="选择设备" size="default" @change="onDeviceChange" style="width:100%">
          <el-option v-for="d in devices" :key="d.id" :label="d.name || d.host" :value="d.id" />
        </el-select>
        <el-button size="small" @click="showLogin=true" style="margin-top:6px;width:100%">+ 添加设备</el-button>
      </div>
      <div class="wb-tree">
        <div v-for="menu in menus" :key="menu.label">
          <div class="tree-folder" :class="{open:menu.open}" @click="menu.open=!menu.open">
            {{ menu.open ? '📂' : '📁' }} {{ menu.label }}
          </div>
          <div v-show="menu.open">
            <div
              v-for="item in menu.items"
              :key="item.path"
              class="tree-item" :class="{active:currentPath===item.path}"
              @click="selectMenu(item)"
            >{{ item.label }}</div>
          </div>
        </div>
      </div>
      <div class="wb-status" v-if="connected">
        <span class="status-dot on"></span> {{ deviceInfo?.version || '已连接' }}
      </div>
    </div>

    <!-- ═══ 右侧内容区 ═══ -->
    <div class="wb-main">
      <!-- 工具栏 -->
      <div class="wb-toolbar" v-if="connected">
        <span class="wb-breadcrumb">{{ currentMenuLabel }}</span>
        <div style="flex:1"></div>
        <el-button size="small" type="primary" @click="showAdd=true" :disabled="!currentPath">+ 添加</el-button>
        <el-button size="small" @click="loadData">🔄 刷新</el-button>
        <el-input v-model="filterText" size="small" placeholder="过滤..." style="width:160px;margin-left:8px" clearable />
      </div>

      <!-- 数据表格 -->
      <div class="wb-table-wrap" v-if="connected">
        <el-table :data="filteredData" size="small" border stripe max-height="calc(100vh - 220px)" @row-click="onRowClick">
          <el-table-column type="index" label="#" width="40" />
          <el-table-column v-for="col in tableColumns" :key="col" :prop="col" :label="col" min-width="120" show-overflow-tooltip />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{row}">
              <el-button link size="small" type="primary" @click.stop="editRow(row)">编辑</el-button>
              <el-button link size="small" type="danger" @click.stop="deleteRow(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!tableData.length" :description="connected?'暂无数据':'请先选择设备'"/>
      </div>

      <!-- 未连接提示 -->
      <div v-else class="wb-connect-hint">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:48px;height:48px;opacity:.3">
          <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
          <path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
        </svg>
        <p>选择设备或添加新设备后开始管理</p>
      </div>
    </div>

    <!-- ═══ 登录/添加设备对话框 ═══ -->
    <el-dialog v-model="showLogin" title="连接 RouterOS 设备" width="420px">
      <el-form label-width="80px" @submit.prevent="doConnect">
        <el-form-item label="设备名称"><el-input v-model="login.name" placeholder="Core-R1" /></el-form-item>
        <el-form-item label="IP 地址"><el-input v-model="login.host" placeholder="192.168.88.1" /></el-form-item>
        <el-form-item label="端口"><el-input-number v-model="login.port" :min="1" :max="65535" />
          <span style="font-size:11px;color:#909399;margin-left:8px">REST API (443)</span>
        </el-form-item>
        <el-form-item label="用户名"><el-input v-model="login.user" placeholder="admin" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="login.pass" type="password" show-password placeholder="输入密码" /></el-form-item>
        <el-form-item label="SSL"><el-switch v-model="login.ssl" /></el-form-item>
      </el-form>
      <el-alert v-if="loginError" :title="loginError" type="error" :closable="true" @close="loginError=''" style="margin-bottom:12px" />
      <template #footer>
        <el-button @click="showLogin=false">取消</el-button>
        <el-button type="primary" @click="doConnect" :loading="connecting">连接</el-button>
      </template>
    </el-dialog>

    <!-- ═══ 编辑对话框 ═══ -->
    <el-dialog v-model="showEdit" :title="editingMode==='add'?'添加':'编辑'" width="500px">
      <el-form label-width="100px" v-if="editFields.length">
        <el-form-item v-for="f in editFields" :key="f" :label="f">
          <el-input v-model="editForm[f]" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEdit=false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">{{ editingMode==='add'?'创建':'保存' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/* ── 菜单树定义 ── */
const menus = ref([
  { label:'接口', open:true, items:[
    {label:'接口列表', path:'interface'},
  ]},
  { label:'IP', open:false, items:[
    {label:'地址', path:'ip/address'},
    {label:'路由', path:'ip/route'},
    {label:'DNS', path:'ip/dns'},
    {label:'DHCP 服务器', path:'ip/dhcp-server'},
    {label:'DHCP 客户端', path:'ip/dhcp-client'},
    {label:'ARP', path:'ip/arp'},
    {label:'IP 池', path:'ip/pool'},
  ]},
  { label:'防火墙', open:false, items:[
    {label:'Filter 规则', path:'ip/firewall/filter'},
    {label:'NAT 规则', path:'ip/firewall/nat'},
    {label:'Mangle 规则', path:'ip/firewall/mangle'},
    {label:'地址列表', path:'ip/firewall/address-list'},
  ]},
  { label:'无线', open:false, items:[
    {label:'WiFi 接口', path:'interface/wifi'},
  ]},
  { label:'系统', open:false, items:[
    {label:'资源', path:'system/resource'},
    {label:'用户', path:'user'},
    {label:'脚本', path:'system/script'},
    {label:'日志', path:'log'},
  ]},
  { label:'工具', open:false, items:[
    {label:'Ping', path:'ping'},
  ]},
])

/* ── 状态 ── */
const devices = ref<any[]>([])
const deviceId = ref('')
const connected = ref(false)
const deviceInfo = ref<any>(null)
const currentPath = ref('')
const currentMenuLabel = ref('')
const tableData = ref<any[]>([])
const tableColumns = ref<string[]>([])
const filterText = ref('')
const loading = ref(false)

/* 登录 */
const showLogin = ref(false)
const login = reactive({ name:'',host:'',port:443,user:'admin',pass:'',ssl:true })
const connecting = ref(false)
const loginError = ref('')

/* 编辑 */
const showAdd = ref(false)
const showEdit = ref(false)
const editingMode = ref<'add'|'edit'>('add')
const editFields = ref<string[]>([])
const editForm = ref<Record<string,string>>({})
const saving = ref(false)
const editingRowId = ref('')

const filteredData = computed(() => {
  if (!filterText.value) return tableData.value
  const q = filterText.value.toLowerCase()
  return tableData.value.filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(q)))
})

onMounted(() => loadDevices())

/* ── 设备管理 ── */
async function loadDevices() {
  try { const r = await fetch('/api/ros/devices'); devices.value = await r.json() } catch {}
}
async function doConnect() {
  if (!login.host) { ElMessage.warning('请输入IP');return }
  connecting.value = true; loginError.value = ''
  try {
    // 保存设备
    await fetch('/api/ros/devices',{method:'PUT',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({host:login.host,port:login.port,username:login.user,password:login.pass,use_ssl:login.ssl})})
    // 测试连接
    const r = await fetch(`/api/ros/test?host=${encodeURIComponent(login.host)}&port=${login.port}&username=${encodeURIComponent(login.user)}&password=${encodeURIComponent(login.pass)}&use_ssl=${login.ssl}`)
    const data = await r.json()
    if (data.success) {
      await loadDevices()
      deviceId.value = devices.value.find((d:any) => d.host===login.host)?.id || ''
      connected.value = true
      deviceInfo.value = data
      showLogin.value = false
      ElMessage.success(`已连接 ${login.host} (v${data.version})`)
    } else {
      loginError.value = data.error || '连接失败'
    }
  } catch (e:any) { loginError.value = e.message || '网络错误' }
  finally { connecting.value = false }
}
async function onDeviceChange() {
  if (!deviceId.value) { connected.value=false; return }
  const r = await fetch(`/api/ros/devices/${deviceId.value}/connect`)
  const data = await r.json()
  if (data.success) { connected.value=true; deviceInfo.value=data }
  else { connected.value=false; deviceInfo.value=null; ElMessage.error(data.error) }
  currentPath.value=''; tableData.value=[]
}

/* ── 菜单 ── */
async function selectMenu(item:any) {
  currentPath.value = item.path
  currentMenuLabel.value = item.label
  await loadData()
}
async function loadData() {
  if (!deviceId.value || !currentPath.value) return
  loading.value = true
  try {
    const r = await fetch(`/api/ros/proxy?device_id=${deviceId.value}&path=${encodeURIComponent(currentPath.value)}`)
    const data = await r.json()
    tableData.value = Array.isArray(data) ? data : [data]
    // 提取列名
    if (tableData.value.length) {
      tableColumns.value = Array.from(new Set(tableData.value.flatMap((r:any) => Object.keys(r)))).filter(k => !k.startsWith('.') && k !== '.id').slice(0, 10)
    }
  } catch { tableData.value = [] }
  finally { loading.value = false }
}

/* ── CRUD ── */
function onRowClick(row:any) { editRow(row) }
function editRow(row:any) {
  editingMode.value = 'edit'
  editingRowId.value = row['.id'] || ''
  editForm.value = {...row}
  editFields.value = Object.keys(row).filter(k => !k.startsWith('.'))
  showEdit.value = true
}
function deleteRow(row:any) {
  const id = row['.id']
  if (!id) { ElMessage.warning('该记录没有 .id'); return }
  ElMessageBox.confirm('确定删除？','确认',{type:'warning'}).then(async () => {
    await fetch(`/api/ros/proxy?device_id=${deviceId.value}&path=${encodeURIComponent(currentPath.value+'/'+id)}`,{method:'DELETE'})
    ElMessage.success('已删除')
    await loadData()
  }).catch(()=>{})
}
async function saveEdit() {
  saving.value = true
  try {
    const cleanData:Record<string,string> = {}
    for (const [k,v] of Object.entries(editForm.value)) {
      if (k !== '.id' && k !== 'dynamic' && v !== undefined && v !== '') cleanData[k] = v
    }
    const params = new URLSearchParams({device_id:deviceId.value, path:currentPath.value})
    if (editingMode.value==='add') {
      params.set('data', JSON.stringify(cleanData))
      await fetch('/api/ros/proxy?'+params, {method:'PUT'})
      ElMessage.success('已创建')
    } else {
      const p = currentPath.value+'/'+editingRowId.value
      const ep = new URLSearchParams({device_id:deviceId.value, path:p})
      ep.set('data', JSON.stringify(cleanData))
      await fetch('/api/ros/proxy?'+ep, {method:'PATCH'})
      ElMessage.success('已保存')
    }
    showEdit.value = false
    await loadData()
  } catch (e:any) { ElMessage.error('保存失败: '+e.message) }
  finally { saving.value = false }
}
</script>

<style scoped>
.winbox-layout { display: flex; height: calc(100vh - 60px); background: #f5f6fa; }
.wb-sidebar { width: 220px; background: #fff; border-right: 1px solid #e5e7eb; display: flex; flex-direction: column; }
.wb-device-bar { padding: 12px; border-bottom: 1px solid #f1f5f9; }
.wb-tree { flex: 1; overflow-y: auto; padding: 8px 0; }
.tree-folder { padding: 8px 16px; cursor: pointer; font-size: 13px; font-weight: 600; color: #334155; user-select: none; }
.tree-folder:hover { background: #f1f5f9; }
.tree-item { padding: 6px 16px 6px 32px; cursor: pointer; font-size: 12px; color: #64748b; }
.tree-item:hover { background: #eff6ff; color: #3b82f6; }
.tree-item.active { background: #dbeafe; color: #2563eb; font-weight: 600; }
.wb-status { padding: 10px 16px; border-top: 1px solid #f1f5f9; font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 6px; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #cbd5e1; }
.status-dot.on { background: #10b981; }
.wb-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.wb-toolbar { padding: 10px 16px; background: #fff; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center; gap: 8px; }
.wb-breadcrumb { font-size: 14px; font-weight: 600; color: #1e293b; }
.wb-table-wrap { flex: 1; padding: 12px; overflow: auto; }
.wb-connect-hint { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; gap: 12px; }
</style>

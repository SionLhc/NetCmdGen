<template>
  <div v-if="!connected && !loading" class="winbox-shell">
    <!-- ═══ 未连接 → 设备列表 ═══ -->
    <div class="rb-titlebar">RouterOS Console</div>
    <div style="padding:24px;max-width:600px;margin:0 auto">
      <h3 style="margin:0 0 16px;font-size:18px;color:#333">已保存的设备</h3>
      <div v-if="devices.length" style="display:flex;flex-direction:column;gap:8px">
        <div v-for="d in devices" :key="d.id" class="dev-card" @click="connectDevice(d)">
          <span style="font-weight:600;font-size:14px">{{ d.name || d.host }}</span>
          <span style="color:#888;font-size:12px;font-family:monospace">{{ d.host }}:{{ d.port }}</span>
          <span style="margin-left:auto;font-size:11px;color:#666">{{ d.username }}</span>
        </div>
      </div>
      <div v-else style="color:#999;text-align:center;padding:32px 0">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:40px;height:40px;opacity:.3;margin-bottom:8px">
          <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
        </svg>
        <p>暂无已保存的设备</p>
      </div>
      <el-button type="primary" @click="showLogin=true" style="width:100%;margin-top:16px">+ 添加 RouterOS 设备</el-button>
    </div>
  </div>

  <!-- ═══ 已连接 → Winbox 风格主界面 ═══ -->
  <div v-else class="winbox-shell">
    <!-- 标题栏 -->
    <div class="rb-titlebar">
      <span class="rb-app-title">RouterOS Console</span>
      <span class="rb-conn-info">
        <span class="rb-live-dot"></span>
        {{ deviceInfo?.version || login.host }}
      </span>
      <div style="flex:1"></div>
      <button class="rb-title-btn" @click="showLogin=true">+ 新连接</button>
      <button class="rb-title-btn" @click="deviceId='';connected=false">断开</button>
    </div>

    <!-- 工具栏 -->
    <div class="rb-toolbar">
      <el-select v-model="deviceId" size="small" @change="onDeviceChange" style="width:180px" v-if="devices.length>1">
        <el-option v-for="d in devices" :key="d.id" :label="d.name||d.host" :value="d.id"/>
      </el-select>
      <span class="rb-tb-sep"></span>
      <button class="rb-tb-btn" @click="showAdd=true" :disabled="!currentPath" title="新建">New</button>
      <button class="rb-tb-btn" disabled title="启用">Enable</button>
      <button class="rb-tb-btn" disabled title="禁用">Disable</button>
      <button class="rb-tb-btn" @click="editRow(tableData[0])" :disabled="!selectedRow" title="编辑">Comment</button>
      <button class="rb-tb-btn" @click="deleteRow(selectedRow)" :disabled="!selectedRow" title="删除">Remove</button>
      <span class="rb-tb-sep"></span>
      <button class="rb-tb-btn" @click="loadData" title="刷新">Refresh</button>
      <div style="flex:1"></div>
      <input v-model="filterText" class="rb-filter" placeholder="Find..." />
    </div>

    <!-- 主体：左树 + 右内容 -->
    <div class="rb-body">
      <!-- 左侧树形菜单 -->
      <div class="rb-tree-panel">
        <div v-for="menu in menus" :key="menu.label">
          <div
            class="rb-tree-folder" :class="{open:menu.open}"
            @click="menu.open=!menu.open"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="rb-folder-icon"><path d="M5 12h14"/><path v-if="!menu.open" d="M12 5v14"/></svg>
            <span>{{ menu.label }}</span>
          </div>
          <div v-show="menu.open" class="rb-tree-children">
            <div
              v-for="item in menu.items" :key="item.path"
              class="rb-tree-item" :class="{active:currentPath===item.path}"
              @click="selectMenu(item)"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="rb-item-icon"><circle cx="12" cy="12" r="2"/></svg>
              <span>{{ item.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧内容区 -->
      <div class="rb-content">
        <!-- 子标签栏 -->
        <div class="rb-tabbar" v-if="currentPath">
          <div class="rb-tab active">{{ currentMenuLabel }}</div>
        </div>

        <!-- 数据表格 -->
        <div class="rb-grid-wrap" v-if="currentPath">
          <table class="rb-grid" v-if="tableData.length">
            <thead>
              <tr>
                <th class="rb-th rb-th-num">#</th>
                <th v-for="col in tableColumns" :key="col" class="rb-th">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, i) in filteredData" :key="row['.id'] || i"
                class="rb-tr"
                :class="{selected:selectedIndex===i}"
                @click="selectedIndex=i;selectedRow=row"
                @dblclick="editRow(row)"
              >
                <td class="rb-td rb-td-num">{{ (page-1)*pageSize+i+1 }}</td>
                <td v-for="col in tableColumns" :key="col" class="rb-td">
                  <span v-if="col === 'running' || col === 'disabled' || col === 'enabled'"
                    :style="{color:row[col]==='true'||row[col]===true?'#10b981':row[col]==='false'||row[col]===false?'#ef4444':'inherit'}"
                  >{{ row[col] }}</span>
                  <span v-else>{{ row[col] }}</span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="rb-empty">
            <p>暂无数据 — 双击空白区域或点击工具栏 "New" 创建记录</p>
          </div>
        </div>

        <!-- 未选菜单 -->
        <div v-else class="rb-empty">
          <p>从左侧菜单选择配置项开始管理</p>
        </div>
      </div>
    </div>

    <!-- 状态栏 -->
    <div class="rb-statusbar">
      <span class="rb-status-live">● Live</span>
      <span class="rb-status-dev">| {{ login.host }}:{{ login.port }}</span>
      <span v-if="tableData.length" class="rb-status-count">| {{ tableData.length }} 条记录</span>
      <div style="flex:1"></div>
      <span style="font-size:11px;color:#888">{{ currentMenuLabel }}</span>
    </div>
  </div>

  <!-- ═══ 登录对话框 ═══ -->
  <el-dialog v-model="showLogin" title="连接 RouterOS 设备" width="420px">
    <el-form label-width="80px" @submit.prevent="doConnect">
      <el-form-item label="设备名称"><el-input v-model="login.name" placeholder="Core-R1" /></el-form-item>
      <el-form-item label="IP 地址"><el-input v-model="login.host" placeholder="192.168.88.1" /></el-form-item>
      <el-form-item label="端口">
        <el-select v-model="login.port" style="width:140px">
          <el-option :value="8728" label="8728 (API 默认)" />
          <el-option :value="8729" label="8729 (API-SSL)" />
          <el-option :value="443" label="443 (REST HTTPS)" />
          <el-option :value="80" label="80 (REST HTTP)" />
        </el-select>
        <span style="font-size:11px;color:#909399;margin-left:8px">{{ login.port === 8728 ? '推荐，无需额外配置' : login.port === 8729 ? '需启用 api-ssl' : '需启用 www-ssl' }}</span>
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

  <!-- ═══ 编辑对话框（Winbox 风格） ═══ -->
  <el-dialog v-model="showEdit" :title="editingMode==='add'?'New '+currentMenuLabel:'编辑'" width="520px">
    <el-form label-width="120px" v-if="editFields.length">
      <el-form-item v-for="f in editFields" :key="f" :label="f">
        <el-input v-model="editForm[f]" :placeholder="f" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showEdit=false">Cancel</el-button>
      <el-button type="primary" @click="saveEdit" :loading="saving">{{ editingMode==='add'?'OK':'Apply' }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/* ── 菜单树（Winbox 结构） ── */
const menus = ref([
  { label:'Quick Set', open:false, items:[] },
  { label:'Interfaces', open:true, items:[
    {label:'Interface List', path:'interface'},
    {label:'Ethernet', path:'interface/ethernet'},
  ]},
  { label:'Wireless', open:false, items:[
    {label:'WiFi Interfaces', path:'interface/wifi'},
  ]},
  { label:'Bridge', open:false, items:[
    {label:'Bridge', path:'interface/bridge'},
    {label:'Ports', path:'interface/bridge/port'},
  ]},
  { label:'IP', open:false, items:[
    {label:'Addresses', path:'ip/address'},
    {label:'Routes', path:'ip/route'},
    {label:'DNS', path:'ip/dns'},
    {label:'ARP', path:'ip/arp'},
    {label:'DHCP Server', path:'ip/dhcp-server'},
    {label:'DHCP Client', path:'ip/dhcp-client'},
    {label:'Pool', path:'ip/pool'},
    {label:'Firewall → Filter', path:'ip/firewall/filter'},
    {label:'Firewall → NAT', path:'ip/firewall/nat'},
    {label:'Firewall → Mangle', path:'ip/firewall/mangle'},
    {label:'Firewall → Address Lists', path:'ip/firewall/address-list'},
    {label:'Services', path:'ip/service'},
  ]},
  { label:'System', open:false, items:[
    {label:'Resources', path:'system/resource'},
    {label:'Users', path:'user'},
    {label:'Scripts', path:'system/script'},
    {label:'Scheduler', path:'system/scheduler'},
    {label:'Log', path:'log'},
  ]},
  { label:'Tools', open:false, items:[
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
const selectedIndex = ref(-1)
const selectedRow = ref<any>(null)
const page = ref(1)
const pageSize = 50

const login = reactive({ name:'',host:'',port:8728,user:'admin',pass:'',ssl:false })
const showLogin = ref(false)
const connecting = ref(false)
const loginError = ref('')

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

async function connectDevice(d: any) {
  login.host = d.host; login.port = d.port||443; login.user = d.username||'admin'; login.pass = ''
  login.name = d.name || d.host; login.ssl = d.use_ssl !== false
  loading.value = true
  try {
    const r = await fetch(`/api/ros/devices/${d.id}/connect`)
    const data = await r.json()
    if (data.success) {
      deviceId.value = d.id
      connected.value = true
      deviceInfo.value = data
      ElMessage.success(`已连接 ${d.host}`)
    } else {
      // 连接失败但设备存在，弹出密码输入
      showLogin.value = true
    }
  } catch { showLogin.value = true }
  finally { loading.value = false }
}

async function doConnect() {
  if (!login.host) { ElMessage.warning('请输入 IP'); return }
  connecting.value = true; loginError.value = ''
  try {
    await fetch('/api/ros/devices', { method:'PUT', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name:login.name,host:login.host,port:login.port,username:login.user,password:login.pass,use_ssl:login.ssl}) })
    const r = await fetch(`/api/ros/test?host=${encodeURIComponent(login.host)}&port=${login.port}&username=${encodeURIComponent(login.user)}&password=${encodeURIComponent(login.pass)}&use_ssl=${login.ssl}`)
    const data = await r.json()
    if (data.success) {
      await loadDevices()
      deviceId.value = devices.value.find((d:any)=>d.host===login.host)?.id||''
      connected.value = true; deviceInfo.value = data; showLogin.value = false
      ElMessage.success(`已连接 ${login.host} (v${data.version})`)
    } else { loginError.value = data.error || '连接失败' }
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
async function selectMenu(item: any) {
  currentPath.value = item.path
  currentMenuLabel.value = item.label
  selectedIndex.value = -1
  selectedRow.value = null
  await loadData()
}

async function loadData() {
  if (!deviceId.value || !currentPath.value) return
  loading.value = true
  try {
    const r = await fetch(`/api/ros/proxy?device_id=${deviceId.value}&path=${encodeURIComponent(currentPath.value)}`)
    const data = await r.json()
    tableData.value = Array.isArray(data) ? data : [data]
    if (tableData.value.length) {
      tableColumns.value = Array.from(new Set(
        tableData.value.flatMap((r:any)=>Object.keys(r))
      )).filter(k => !k.startsWith('.') && k !== '.id').slice(0, 12)
    }
  } catch { tableData.value = [] }
  finally { loading.value = false }
}

/* ── CRUD ── */
function editRow(row: any) {
  editingMode.value = 'edit'
  editingRowId.value = row['.id'] || ''
  editForm.value = {...row}
  editFields.value = Object.keys(row).filter(k => !k.startsWith('.'))
  showEdit.value = true
}

function deleteRow(row: any) {
  if (!row) return
  const id = row['.id']; if (!id) { ElMessage.warning('该记录没有 .id'); return }
  ElMessageBox.confirm('确定删除？','确认',{type:'warning'}).then(async()=>{
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
      if (k!=='.id' && v!==undefined && v!=='') cleanData[k]=v
    }
    const params = new URLSearchParams({device_id:deviceId.value,path:currentPath.value})
    if (editingMode.value==='add') {
      params.set('data',JSON.stringify(cleanData))
      await fetch('/api/ros/proxy?'+params,{method:'PUT'})
      ElMessage.success('已创建')
    } else {
      const p = currentPath.value+'/'+editingRowId.value
      const ep = new URLSearchParams({device_id:deviceId.value,path:p})
      ep.set('data',JSON.stringify(cleanData))
      await fetch('/api/ros/proxy?'+ep,{method:'PATCH'})
      ElMessage.success('已保存')
    }
    showEdit.value=false
    await loadData()
  } catch (e:any) { ElMessage.error('保存失败: '+e.message) }
  finally { saving.value=false }
}
</script>

<style scoped>
/* ═══ 全局 Shell ═══ */
.winbox-shell {
  height: calc(100vh - 60px);
  display: flex; flex-direction: column;
  background: #e8e8e8;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  font-size: 12px;
  color: #222;
  overflow: hidden;
  user-select: none;
}

/* ═══ 标题栏（Winbox 顶栏风格） ═══ */
.rb-titlebar {
  background: linear-gradient(180deg, #2b5797 0%, #1e3e6b 100%);
  color: #fff;
  display: flex; align-items: center;
  padding: 0 12px; height: 32px; min-height: 32px;
  gap: 10px;
}
.rb-app-title { font-size: 12px; font-weight: 600; letter-spacing: .5px; }
.rb-conn-info { font-size: 11px; opacity: .85; display: flex; align-items: center; gap: 5px; }
.rb-live-dot { width: 6px; height: 6px; border-radius: 50%; background: #4caf50; box-shadow: 0 0 4px #4caf50; }
.rb-title-btn {
  background: none; border: 1px solid rgba(255,255,255,.2); color: #fff;
  padding: 2px 10px; font-size: 11px; cursor: pointer; border-radius: 2px;
}
.rb-title-btn:hover { background: rgba(255,255,255,.1); }

/* ═══ 工具栏 ═══ */
.rb-toolbar {
  background: #f0f0f0;
  border-bottom: 1px solid #ccc;
  display: flex; align-items: center;
  padding: 4px 8px; gap: 2px; min-height: 34px;
}
.rb-tb-btn {
  background: none; border: 1px solid transparent; color: #333;
  padding: 4px 12px; font-size: 11px; cursor: pointer; border-radius: 2px;
  white-space: nowrap;
}
.rb-tb-btn:hover { background: #d0e4f7; border-color: #9bc2e6; }
.rb-tb-btn:disabled { color: #aaa; cursor: default; }
.rb-tb-btn:disabled:hover { background: none; border-color: transparent; }
.rb-tb-sep { width: 1px; height: 20px; background: #ccc; margin: 0 4px; }
.rb-filter {
  border: 1px solid #bbb; background: #fff; padding: 4px 8px;
  font-size: 11px; width: 150px; border-radius: 2px; outline: none;
}
.rb-filter:focus { border-color: #0078d7; }

/* ═══ 主体：左树 + 右内容 ═══ */
.rb-body { flex: 1; display: flex; overflow: hidden; }

/* ═══ 左侧树 ═══ */
.rb-tree-panel {
  width: 220px; min-width: 220px;
  background: #fff; border-right: 1px solid #d0d0d0;
  overflow-y: auto; padding: 4px 0;
}
.rb-tree-folder {
  display: flex; align-items: center; gap: 4px;
  padding: 5px 8px; cursor: pointer;
  font-size: 11px; font-weight: 600; color: #333;
  border-radius: 0; margin: 0;
}
.rb-tree-folder:hover { background: #e5eff7; }
.rb-folder-icon { width: 12px; height: 12px; flex-shrink: 0; color: #666; }
.rb-tree-children { padding-left: 4px; }
.rb-tree-item {
  display: flex; align-items: center; gap: 4px;
  padding: 4px 8px 4px 20px; cursor: pointer;
  font-size: 11px; color: #333;
}
.rb-tree-item:hover { background: #d0e4f7; }
.rb-tree-item.active { background: #0078d7; color: #fff; font-weight: 600; }
.rb-tree-item.active .rb-item-icon { color: #fff; }
.rb-item-icon { width: 10px; height: 10px; flex-shrink: 0; color: #888; }

/* ═══ 右侧内容区 ═══ */
.rb-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #f8f8f8; }

/* 标签栏 */
.rb-tabbar {
  display: flex; background: #e0e0e0; border-bottom: 1px solid #ccc;
  padding: 0; gap: 0; min-height: 26px;
}
.rb-tab {
  padding: 3px 16px; font-size: 11px; font-weight: 600;
  cursor: default; color: #333;
  border-right: 1px solid #ccc;
  background: #e8e8e8;
}
.rb-tab.active { background: #fff; border-bottom: 2px solid #0078d7; color: #0078d7; }

/* ═══ 数据表格（Winbox 风格） ═══ */
.rb-grid-wrap { flex: 1; overflow: auto; background: #fff; }
.rb-grid { width: 100%; border-collapse: collapse; table-layout: auto; }
.rb-th {
  position: sticky; top: 0;
  background: #e8e8e8; color: #333; font-weight: 600;
  padding: 5px 10px; font-size: 11px; text-align: left;
  border: 1px solid #d0d0d0; white-space: nowrap;
  z-index: 1;
}
.rb-th-num { width: 36px; text-align: center; }
.rb-tr { cursor: pointer; }
.rb-tr:hover { background: #e5eff7; }
.rb-tr.selected { background: #0078d7; color: #fff; }
.rb-tr.selected .rb-td { color: #fff; }
.rb-td {
  padding: 3px 10px; font-size: 11px;
  border: 1px solid #e8e8e8; white-space: nowrap;
  font-family: 'Consolas', 'Microsoft YaHei', monospace;
  max-width: 300px; overflow: hidden; text-overflow: ellipsis;
}
.rb-td-num { width: 36px; text-align: center; color: #888; font-size: 10px; }
.rb-empty {
  flex: 1; display: flex; align-items: center; justify-content: center;
  color: #999; font-size: 12px;
}

/* ═══ 状态栏 ═══ */
.rb-statusbar {
  background: #f0f0f0; border-top: 1px solid #ccc;
  display: flex; align-items: center;
  padding: 0 12px; height: 22px; min-height: 22px;
  gap: 8px; font-size: 11px;
}
.rb-status-live { color: #10b981; font-weight: 600; }
.rb-status-dev { color: #666; }
.rb-status-count { color: #888; }

/* ═══ 设备卡片 ═══ */
.dev-card {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; background: #fff; border: 1px solid #ddd;
  border-radius: 4px; cursor: pointer; transition: all .15s;
}
.dev-card:hover { border-color: #0078d7; box-shadow: 0 1px 4px rgba(0,120,215,.15); }
</style>

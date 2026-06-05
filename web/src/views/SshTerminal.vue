<template>
  <div class="ssh-layout">
    <!-- 左侧设备列表 -->
    <div class="ssh-sidebar">
      <div class="sidebar-header">
        <h3>已保存设备</h3>
        <button class="save-btn" @click="showSave=true" :disabled="!host">+ 保存当前</button>
      </div>
      <div class="dev-list">
        <div
          v-for="d in devices" :key="d.id"
          class="dev-item" :class="{active: activeDev===d.id}"
          @click="selectDev(d)"
          @dblclick="connectDev(d)"
        >
          <div class="dev-name">{{ d.name }}</div>
          <div class="dev-info">{{ d.host }}:{{ d.port }} · {{ d.username }}</div>
          <button class="dev-del" @click.stop="delDev(d)">✕</button>
        </div>
        <div v-if="!devices.length" class="dev-empty">
          暂无已保存的设备<br>
          <span style="font-size:11px">连接成功后点击「保存当前」</span>
        </div>
      </div>
    </div>

    <!-- 右侧：表单 + 终端 -->
    <div class="ssh-main">
      <el-card class="conn-card">
        <el-form :inline="true" size="default" @submit.prevent="doConnect">
          <el-form-item label="主机">
            <el-input v-model="host" placeholder="192.168.1.1" style="width:150px" :disabled="connected" />
          </el-form-item>
          <el-form-item label="端口">
            <el-input-number v-model="port" :min="1" :max="65535" :disabled="connected" style="width:90px" />
          </el-form-item>
          <el-form-item label="用户名">
            <el-input v-model="username" placeholder="admin" style="width:120px" :disabled="connected" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="password" type="password" placeholder="****" style="width:120px" :disabled="connected" />
          </el-form-item>
          <el-form-item>
            <el-button v-if="!connected" type="primary" @click="doConnect" :loading="connecting">连接</el-button>
            <el-button v-else type="danger" @click="doDisconnect">断开</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 终端 -->
      <div class="term-wrap" :class="{ connected }">
        <div ref="termEl" class="term-container"></div>
        <div v-if="!connected" class="term-placeholder">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40" style="opacity:.4">
            <polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>
          </svg>
          <p>从左侧列表双击连接，或输入信息后点「连接」</p>
        </div>
        <div v-if="errorMsg" class="term-error">
          <el-alert :title="errorMsg" type="error" show-icon :closable="true" @close="errorMsg=''" />
        </div>
      </div>
    </div>

    <!-- 保存对话框 -->
    <el-dialog v-model="showSave" title="保存设备" width="360px">
      <el-form label-width="60px" size="default">
        <el-form-item label="名称"><el-input v-model="saveName" :placeholder="host" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSave=false">取消</el-button>
        <el-button type="primary" @click="doSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'

/* ── 设备管理 ── */
interface Dev { id: string; name: string; host: string; port: number; username: string }
const devices = ref<Dev[]>([])
const activeDev = ref('')
const showSave = ref(false)
const saveName = ref('')

onMounted(loadDevices)
async function loadDevices() {
  try { const r = await fetch('/api/ssh-devices'); devices.value = await r.json() } catch {}
}

async function selectDev(d: Dev) {
  activeDev.value = d.id
  host.value = d.host; port.value = d.port; username.value = d.username
  // 尝试获取密码
  try {
    const r = await fetch(`/api/ssh-devices/${d.id}/password`)
    const data = await r.json()
    password.value = data.password || ''
  } catch { password.value = '' }
}

async function connectDev(d: Dev) {
  await selectDev(d)
  await nextTick()
  doConnect()
}

async function doSave() {
  if (!host.value) { ElMessage.warning('无主机信息'); return }
  const params = new URLSearchParams({
    name: saveName.value || host.value, host: host.value,
    port: String(port.value), username: username.value,
    password: password.value,
  })
  await fetch('/api/ssh-devices?' + params, { method: 'PUT' })
  saveName.value = ''; showSave.value = false
  await loadDevices()
  ElMessage.success('已保存')
}

async function delDev(d: Dev) {
  await fetch(`/api/ssh-devices/${d.id}`, { method: 'DELETE' })
  if (activeDev.value === d.id) activeDev.value = ''
  await loadDevices()
}

/* ── 终端 ── */
const host = ref('')
const port = ref(22)
const username = ref('admin')
const password = ref('')
const connected = ref(false)
const connecting = ref(false)
const errorMsg = ref('')
const termEl = ref<HTMLElement | null>(null)

let term: Terminal | null = null
let fitAddon: FitAddon | null = null
let socket: WebSocket | null = null

async function doConnect() {
  if (!host.value.trim()) { ElMessage.warning('请输入主机'); return }
  connecting.value = true; errorMsg.value = ''
  await nextTick()
  if (!termEl.value) { connecting.value = false; return }

  if (!term) {
    term = new Terminal({
      cursorBlink: true, fontSize: 14,
      fontFamily: 'Consolas, monospace',
      theme: { background: '#1e1e2e', foreground: '#cdd6f4' },
      allowProposedApi: true,
    })
    fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.loadAddon(new WebLinksAddon())
    term.open(termEl.value)
    fitAddon.fit()

    term.onData((data: string) => {
      if (socket?.readyState === WebSocket.OPEN) socket.send(new TextEncoder().encode(data))
    })
    new ResizeObserver(() => {
      fitAddon!.fit()
      if (term && socket?.readyState === WebSocket.OPEN) {
        const dims = fitAddon!.proposeDimensions()
        if (dims) socket.send(JSON.stringify({ type:'resize', rows:dims.rows, cols:dims.cols }))
      }
    }).observe(termEl.value)
  }

  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  socket = new WebSocket(`${proto}://${location.host}/api/ssh/ws?host=${encodeURIComponent(host.value)}&port=${port.value}&username=${encodeURIComponent(username.value)}&password=${encodeURIComponent(password.value)}`)
  socket.binaryType = 'arraybuffer'
  socket.onopen = () => { connecting.value = false; connected.value = true; term!.focus() }
  socket.onmessage = (e) => {
    if (typeof e.data === 'string') {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'error') { errorMsg.value = msg.message; doDisconnect() }
      } catch {}
    } else { term?.write(new Uint8Array(e.data)) }
  }
  socket.onerror = () => { connecting.value = false; errorMsg.value = '连接失败' }
  socket.onclose = () => { connected.value = false; term?.clear() }
}

function doDisconnect() { socket?.close(); socket = null; connected.value = false }
onUnmounted(() => { doDisconnect(); term?.dispose() })
</script>

<style scoped>
.ssh-layout { display: flex; height: calc(100vh - 60px); }
.ssh-sidebar {
  width: 240px; min-width: 240px; background: #fff; border-right: 1px solid #e5e7eb;
  display: flex; flex-direction: column;
}
.sidebar-header { padding: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; }
.sidebar-header h3 { margin: 0; font-size: 14px; }
.save-btn { background: #6366f1; color: #fff; border: none; padding: 5px 12px; border-radius: 6px; font-size: 11px; cursor: pointer; }
.save-btn:disabled { background: #cbd5e1; cursor: default; }
.dev-list { flex: 1; overflow-y: auto; padding: 4px; }
.dev-item {
  padding: 10px 12px; cursor: pointer; border-radius: 6px; margin: 2px 0;
  position: relative; transition: .1s;
}
.dev-item:hover { background: #f1f5f9; }
.dev-item.active { background: #eff6ff; border: 1px solid #93c5fd; }
.dev-name { font-size: 13px; font-weight: 600; color: #1e293b; }
.dev-info { font-size: 11px; color: #94a3b8; font-family: monospace; margin-top: 2px; }
.dev-del {
  position: absolute; top: 8px; right: 8px; border: none; background: none;
  color: #cbd5e1; cursor: pointer; font-size: 12px; display: none;
}
.dev-item:hover .dev-del { display: block; }
.dev-del:hover { color: #ef4444; }
.dev-empty { text-align: center; padding: 24px 12px; color: #94a3b8; font-size: 12px; }

.ssh-main { flex: 1; display: flex; flex-direction: column; padding: 16px; gap: 12px; overflow: hidden; }
.conn-card { flex-shrink: 0; }
.term-wrap {
  flex: 1; position: relative; border-radius: 8px; overflow: hidden;
  border: 1px solid #e5e7eb; min-height: 400px;
}
.term-wrap.connected { border-color: #10b981; box-shadow: 0 0 0 2px rgba(16,185,129,.1); }
.term-container { height: 100%; }
.term-placeholder {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 10px;
  color: #94a3b8; background: #f8fafc; pointer-events: none;
}
.term-error { position: absolute; top: 12px; left: 50%; transform: translateX(-50%); z-index: 10; width: 90%; }
</style>

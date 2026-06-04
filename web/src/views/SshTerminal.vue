<template>
  <div class="ssh-page">
    <div class="ssh-header">
      <h2>🖥 SSH 终端</h2>
      <span style="color:#909399;font-size:13px">网页端直连网络设备</span>
    </div>

    <!-- 连接配置栏 -->
    <el-card class="conn-card">
      <el-form :inline="true" size="default" @submit.prevent="doConnect">
        <el-form-item label="主机">
          <el-input v-model="host" placeholder="192.168.1.1" style="width:160px" :disabled="connected" @keyup.enter="doConnect" />
        </el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="port" :min="1" :max="65535" :disabled="connected" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="username" placeholder="admin" style="width:130px" :disabled="connected" @keyup.enter="doConnect" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" placeholder="****" style="width:130px" :disabled="connected" @keyup.enter="doConnect" />
        </el-form-item>
        <el-form-item>
          <el-button v-if="!connected" type="primary" @click="doConnect" :loading="connecting">
            连接
          </el-button>
          <el-button v-else type="danger" @click="doDisconnect">断开</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 终端区域 -->
    <div class="term-wrap" :class="{ connected }">
      <div ref="termEl" class="term-container"></div>
      <div v-if="!connected && !connecting" class="term-placeholder">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="placeholder-icon">
          <polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>
        </svg>
        <p>输入设备信息后点击「连接」按钮</p>
      </div>
      <div v-if="errorMsg" class="term-error">
        <el-alert :title="errorMsg" type="error" show-icon :closable="true" @close="errorMsg=''" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'

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
  if (!host.value.trim()) { ElMessage.warning('请输入主机地址'); return }
  if (!username.value.trim()) { ElMessage.warning('请输入用户名'); return }

  connecting.value = true
  errorMsg.value = ''

  await nextTick()
  if (!termEl.value) { connecting.value = false; return }

  // 初始化终端
  if (!term) {
    term = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Cascadia Code, Consolas, monospace',
      theme: { background: '#1e1e2e', foreground: '#cdd6f4', cursor: '#f5e0dc' },
      allowProposedApi: true,
    })
    fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.loadAddon(new WebLinksAddon())
    term.open(termEl.value)
    fitAddon.fit()

    // 终端输入 → WebSocket
    term.onData((data: string) => {
      if (socket?.readyState === WebSocket.OPEN) {
        socket.send(new TextEncoder().encode(data))
      }
    })

    // 窗口 resize
    const ro = new ResizeObserver(() => {
      fitAddon!.fit()
      if (term && socket?.readyState === WebSocket.OPEN) {
        const dims = fitAddon!.proposeDimensions()
        if (dims) {
          socket.send(JSON.stringify({ type: 'resize', rows: dims.rows, cols: dims.cols }))
        }
      }
    })
    ro.observe(termEl.value)
  }

  // 建立 WebSocket 连接
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const wsUrl = `${proto}://${location.host}/api/ssh/ws?host=${encodeURIComponent(host.value)}&port=${port.value}&username=${encodeURIComponent(username.value)}&password=${encodeURIComponent(password.value)}`
  socket = new WebSocket(wsUrl)
  socket.binaryType = 'arraybuffer'

  socket.onopen = () => {
    connecting.value = false
    connected.value = true
    term!.focus()
  }

  socket.onmessage = (e) => {
    if (typeof e.data === 'string') {
      // JSON 控制消息
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'error') {
          errorMsg.value = msg.message
          doDisconnect()
        }
      } catch { /* SSH 输出文本 */ }
    } else {
      // 二进制 SSH 数据 → 终端显示
      term?.write(new Uint8Array(e.data))
    }
  }

  socket.onerror = () => {
    connecting.value = false
    errorMsg.value = 'WebSocket 连接失败'
  }

  socket.onclose = () => {
    connected.value = false
    term?.clear()
  }
}

function doDisconnect() {
  socket?.close()
  socket = null
  connected.value = false
}

onUnmounted(() => {
  doDisconnect()
  term?.dispose()
})
</script>

<style scoped>
.ssh-page { padding: 24px; max-width: 1200px; margin: 0 auto; }
.ssh-header { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.ssh-header h2 { margin: 0; font-size: 20px; }
.conn-card { margin-bottom: 12px; }
.term-wrap { position: relative; border-radius: 8px; overflow: hidden; border: 1px solid #e5e7eb; min-height: 480px; }
.term-wrap.connected { border-color: #10b981; box-shadow: 0 0 0 2px rgba(16,185,129,0.15); }
.term-container { height: 480px; }
.term-placeholder {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 12px;
  color: #94a3b8; background: #f8fafc;
}
.placeholder-icon { width: 40px; height: 40px; opacity: .5; }
.term-placeholder p { font-size: 13px; }
.term-error { position: absolute; top: 12px; left: 50%; transform: translateX(-50%); z-index: 10; width: 90%; }
</style>

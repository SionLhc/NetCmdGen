<template>
  <div class="diag-page">
    <div class="diag-header">
      <el-button text @click="$router.push('/diagnostics')">← 返回诊断中心</el-button>
      <h2>🌍 HTTP/HTTPS 可用性监测</h2>
    </div>

    <el-card class="param-card">
      <el-form :inline="true" size="default">
        <el-form-item label="目标 URL">
          <el-input v-model="url" placeholder="https://baidu.com" style="width:340px" />
        </el-form-item>
        <el-form-item label="方法">
          <el-select v-model="method" style="width:100px">
            <el-option label="GET" value="GET" />
            <el-option label="HEAD" value="HEAD" />
          </el-select>
        </el-form-item>
        <br>
        <el-form-item label="追踪重定向">
          <el-switch v-model="followRedirects" />&nbsp;&nbsp;
        </el-form-item>
        <el-form-item label="SSL证书">
          <el-switch v-model="checkSsl" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startDiag" :loading="isRunning">开始检测</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 进度日志 -->
    <div v-if="logs.length" style="margin:12px 0">
      <div v-for="(l,i) in logs" :key="i" style="font-size:13px;color:#909399;padding:2px 0">
        {{ l }}
      </div>
    </div>

    <!-- 结果 -->
    <el-descriptions v-if="result" :column="2" border size="small" style="margin-top:12px">
      <el-descriptions-item label="URL">{{ result.url }}</el-descriptions-item>
      <el-descriptions-item label="状态码">
        <el-tag v-if="result.status_code" :type="result.status_code<400?'success':result.status_code<500?'warning':'danger'" size="small">{{ result.status_code }}</el-tag>
        <span v-else style="color:#f56c6c">请求失败</span>
      </el-descriptions-item>
      <el-descriptions-item label="响应时间">{{ result.rtt_ms }}ms</el-descriptions-item>
      <el-descriptions-item label="内容大小">{{ (result.content_length/1024).toFixed(1) }} KB</el-descriptions-item>
      <el-descriptions-item label="Server">{{ result.server || '-' }}</el-descriptions-item>
      <el-descriptions-item label="TLS 版本">{{ result.tls_version || '-' }}</el-descriptions-item>
      <el-descriptions-item label="证书到期" :span="2">{{ result.cert_expires || '未获取' }}</el-descriptions-item>
      <el-descriptions-item label="重定向链" :span="2" v-if="result.redirect_chain?.length">
        <div v-for="(r,i) in result.redirect_chain" :key="i" style="padding:1px 0">→ {{ r }}</div>
      </el-descriptions-item>
      <el-descriptions-item v-if="result.error" label="错误" :span="2">
        <span style="color:#f56c6c">{{ result.error }}</span>
      </el-descriptions-item>
    </el-descriptions>

    <el-empty v-if="!isRunning && !result" description="输入 URL 开始 HTTP 可用性检测" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSseStream } from '@/composables/useSseStream'

const url = ref('https://baidu.com')
const method = ref('GET')
const followRedirects = ref(true)
const checkSsl = ref(true)
const logs = ref<string[]>([])
const result = ref<any>(null)

const sseUrl = computed(() => {
    const p = new URLSearchParams({
        url: url.value, method: method.value,
        follow_redirects: String(followRedirects.value),
        check_ssl: String(checkSsl.value),
    })
    return `/api/diagnostics/http/stream?${p}`
})
const stream = useSseStream<any>(sseUrl)
const { isRunning, stop } = stream

function startDiag() {
    const currentTarget = url.value.trim()
    logs.value = []
    result.value = null
    stream.onProgress = (d: any) => {
        if (d.message) logs.value.push(d.message)
        if (d.status_code !== undefined) result.value = d
    }
    stream.onError = (e: string) => { console.error('HTTP 检测失败: ' + e) }
    stream.onComplete = () => {
        const rtt = result.value?.rtt_ms ?? 0
        const status = result.value?.status_code ? 'ok' : 'error'
        const saveParams = new URLSearchParams({
            diagnostic_type: 'http', target: currentTarget,
            avg_rtt: String(typeof rtt === 'number' ? rtt : 0), loss_percent: '0',
            status,
        })
        fetch('/api/diagnostics/history/save?' + saveParams, { method: 'GET' }).catch(() => {})
    }
    stream.start()
}
</script>

<style scoped>
.diag-page { padding: 24px; max-width: 1100px; margin: 0 auto; }
.diag-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.diag-header h2 { margin: 0; font-size: 20px; }
.param-card { margin-bottom: 12px; }
</style>

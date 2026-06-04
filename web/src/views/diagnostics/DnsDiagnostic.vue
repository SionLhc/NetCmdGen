<template>
  <div class="diag-page">
    <div class="diag-header">
      <el-button text @click="$router.push('/diagnostics')">← 返回诊断中心</el-button>
      <h2>🌐 DNS 解析诊断</h2>
    </div>

    <el-card class="param-card">
      <el-form :inline="true" size="default">
        <el-form-item label="目标域名">
          <el-input v-model="target" placeholder="baidu.com" style="width:240px" />
        </el-form-item>
        <el-form-item label="记录类型">
          <el-select v-model="recordTypes" multiple placeholder="记录类型">
            <el-option v-for="t in allTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <br>
        <el-form-item label="DNS 服务器">
          <el-select v-model="dnsServers" multiple placeholder="DNS服务器">
            <el-option label="Google (8.8.8.8)" value="8.8.8.8" />
            <el-option label="Cloudflare (1.1.1.1)" value="1.1.1.1" />
            <el-option label="Quad9 (9.9.9.9)" value="9.9.9.9" />
            <el-option label="114DNS (114.114.114.114)" value="114.114.114.114" />
            <el-option label="AliDNS (223.5.5.5)" value="223.5.5.5" />
            <el-option label="DNSPod (119.29.29.29)" value="119.29.29.29" />
            <el-option label="OpenDNS (208.67.222.222)" value="208.67.222.222" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startDiag" :loading="isRunning" :icon="isRunning ? undefined : 'Search'">
            {{ isRunning ? '诊断中...' : '开始诊断' }}
          </el-button>
          <el-button v-if="isRunning" type="danger" @click="stop">停止</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 进度 -->
    <el-progress v-if="isRunning" :percentage="pct" :stroke-width="6" style="margin:12px 0" />

    <!-- 结果表格 -->
    <el-table :data="results" style="margin-top:12px" v-if="results.length" max-height="500" stripe size="small" border>
      <el-table-column prop="record_type" label="类型" width="80" />
      <el-table-column prop="server_name" label="DNS服务器" width="140">
        <template #default="{row}">{{ row.server_name }}<br><span style="font-size:11px;color:#909399">{{ row.server }}</span></template>
      </el-table-column>
      <el-table-column prop="records" label="解析结果">
        <template #default="{row}">
          <el-tag v-if="row.error" type="danger" size="small">{{ row.error }}</el-tag>
          <div v-else>
            <el-tag v-for="(r,i) in row.records" :key="i" size="small" style="margin:2px">{{ r }}</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="rtt_ms" label="响应时间" width="100" align="center">
        <template #default="{row}">
          <span v-if="row.error" style="color:#f56c6c">-</span>
          <span v-else :style="{color: row.rtt_ms<50?'#67c23a':row.rtt_ms<200?'#e6a23c':'#f56c6c'}">{{ row.rtt_ms }}ms</span>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!isRunning && !results.length" description="输入域名，多解析器对比诊断" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useSseStream } from '@/composables/useSseStream'

const target = ref('baidu.com')
const recordTypes = ref(['A', 'AAAA', 'CNAME', 'MX', 'NS'])
const dnsServers = ref(['8.8.8.8', '114.114.114.114', '223.5.5.5'])
const allTypes = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA', 'SRV']

interface DnsItem { record_type: string; server: string; server_name: string; records: string[]; rtt_ms: number; error: string }
const results = ref<DnsItem[]>([])

const sseUrl = computed(() =>
    `/api/diagnostics/dns/stream?target=${encodeURIComponent(target.value)}&record_types=${recordTypes.value.join(',')}&dns_servers=${dnsServers.value.join(',')}`
)
const stream = useSseStream<DnsItem>(sseUrl)

const isRunning = stream.isRunning
const pct = computed(() => stream.total.value ? Math.round(stream.progress.value / stream.total.value * 100) : 0)

function startDiag() {
    const currentTarget = target.value.trim()
    results.value = []
    stream.onProgress = (d: DnsItem) => { results.value.push(d) }
    stream.onError = (e: string) => { ElMessage.error('DNS 查询失败: ' + e) }
    stream.onComplete = () => {
        // 保存历史：计算平均 RTT
        const validRtts = results.value.filter(r => r.rtt_ms > 0).map(r => r.rtt_ms)
        const avgRtt = validRtts.length ? +(validRtts.reduce((a,b)=>a+b,0)/validRtts.length).toFixed(1) : 0
        const saveParams = new URLSearchParams({
            diagnostic_type: 'dns', target: currentTarget,
            avg_rtt: String(avgRtt), loss_percent: '0',
            status: 'ok',
        })
        fetch('/api/diagnostics/history/save?' + saveParams, { method: 'GET' }).catch(() => {})
    }
    stream.start()
}
function stop() { stream.stop() }
</script>

<style scoped>
.diag-page { padding: 24px; max-width: 1100px; margin: 0 auto; }
.diag-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.diag-header h2 { margin: 0; font-size: 20px; }
.param-card { margin-bottom: 12px; }
</style>

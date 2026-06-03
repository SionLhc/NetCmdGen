<template>
  <div class="diag-page">
    <div class="diag-header">
      <el-button text @click="$router.push('/diagnostics')">← 返回诊断中心</el-button>
      <h2>🔌 TCP 端口连通性检测</h2>
    </div>

    <el-card class="param-card">
      <el-form :inline="true" size="default">
        <el-form-item label="目标地址">
          <el-input v-model="target" placeholder="192.168.1.1" style="width:200px" />
        </el-form-item>
        <el-form-item label="端口列表">
          <el-input v-model="ports" placeholder="22,80,443,3306,3389" style="width:280px" />
        </el-form-item>
        <el-form-item label="超时">
          <el-input-number v-model="timeoutMs" :min="500" :max="10000" :step="500" /> 毫秒
        </el-form-item>
        <br>
        <el-form-item label="快捷预设">
          <el-button size="small" @click="ports='22,80,443'">Web</el-button>
          <el-button size="small" @click="ports='22,80,443,3306,6379,27017'">全栈</el-button>
          <el-button size="small" @click="ports='22,23,80,443,3389,8080,8443'">远程</el-button>
          <el-button size="small" @click="ports='1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,53,80,110,135,139,143,161,389,443,445,636,1433,1521,3306,3389,5432,6379,8080,8443,9090,27017'">全面 [47]</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startDiag" :loading="isRunning">开始扫描</el-button>
          <el-button v-if="isRunning" type="danger" @click="stop">停止</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-progress v-if="isRunning" :percentage="pct" :stroke-width="6" style="margin:12px 0" />

    <!-- 统计 -->
    <div class="stats-row" v-if="results.length">
      <div class="stat-box"><div class="lbl">总数</div><div class="val">{{ results.length }}</div></div>
      <div class="stat-box"><div class="lbl">开放</div><div class="val" style="color:#67c23a">{{ openCount }}</div></div>
      <div class="stat-box"><div class="lbl">关闭</div><div class="val" style="color:#909399">{{ results.length - openCount }}</div></div>
    </div>

    <el-table :data="results" style="margin-top:12px" v-if="results.length" size="small" border max-height="450">
      <el-table-column prop="port" label="端口" width="80" />
      <el-table-column prop="service" label="服务" width="100" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="状态" width="90" align="center">
        <template #default="{row}">
          <el-tag :type="row.open?'success':'info'" size="small">{{ row.open ? '开放' : '关闭' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="rtt_ms" label="延迟" width="80" align="center">
        <template #default="{row}">{{ row.open ? row.rtt_ms+'ms' : '-' }}</template>
      </el-table-column>
      <el-table-column label="风险" width="80" align="center">
        <template #default="{row}">
          <el-tag v-if="row.open" :type="row.risk==='high'?'danger':row.risk==='medium'?'warning':''" size="small">{{ row.risk==='high'?'高危':row.risk==='medium'?'中危':'低' }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!isRunning && !results.length" description="输入目标IP/域名和端口列表" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSseStream } from '@/composables/useSseStream'

const target = ref('')
const ports = ref('22,80,443,3306,3389,6379')
const timeoutMs = ref(3000)

interface PortItem { port: number; open: boolean; service: string; description: string; rtt_ms: number; risk: string }
const results = ref<PortItem[]>([])
const sseUrl = computed(() => `/api/v1/diagnostics/tcp-port/stream?target=${encodeURIComponent(target.value)}&ports=${encodeURIComponent(ports.value)}&timeout_ms=${timeoutMs.value}`)
const { isRunning, progress, total, start, stop } = useSseStream<PortItem>(sseUrl as any)

const pct = computed(() => total.value ? Math.round(progress.value / total.value * 100) : 0)
const openCount = computed(() => results.value.filter(r => r.open).length)

function startDiag() {
    results.value = []
    const s = useSseStream<PortItem>(sseUrl.value)
    s.onProgress = (d) => { results.value.push(d) }
    s.start()
}
</script>

<style scoped>
.diag-page { padding: 24px; max-width: 1100px; margin: 0 auto; }
.diag-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.diag-header h2 { margin: 0; font-size: 20px; }
.param-card { margin-bottom: 12px; }
.stats-row { display: flex; gap: 12px; margin-bottom: 8px; }
.stat-box { background: #f5f7fa; border-radius: 8px; padding: 8px 18px; text-align: center; }
.stat-box .lbl { font-size: 11px; color: #909399; }
.stat-box .val { font-size: 20px; font-weight: 700; }
</style>

<template>
  <div class="diag-page">
    <div class="diag-header">
      <el-button text @click="$router.push('/diagnostics')">← 返回诊断中心</el-button>
      <h2>📊 网络抖动分析</h2>
    </div>

    <el-card class="param-card">
      <el-form :inline="true" size="default">
        <el-form-item label="目标地址">
          <el-input v-model="target" placeholder="8.8.8.8" style="width:200px" />
        </el-form-item>
        <el-form-item label="发包次数">
          <el-slider v-model="packetCount" :min="20" :max="300" :step="10" show-input style="width:200px" />
        </el-form-item>
        <el-form-item label="发包间隔">
          <el-input-number v-model="intervalMs" :min="10" :max="500" :step="10" /> 毫秒
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startDiag" :loading="isRunning">开始分析</el-button>
          <el-button v-if="isRunning" type="danger" @click="stop">停止</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计 -->
    <div class="stats-row" v-if="results.length">
      <div class="stat-box"><div class="lbl">发包</div><div class="val">{{ results.length }}</div></div>
      <div class="stat-box"><div class="lbl">丢包</div><div class="val" style="color:#f56c6c">{{ lossCount }}</div></div>
      <div class="stat-box"><div class="lbl">丢包率</div><div class="val" :style="{color:lossPct>5?'#f56c6c':'#67c23a'}">{{ lossPct.toFixed(1) }}%</div></div>
      <div class="stat-box"><div class="lbl">平均延迟</div><div class="val" style="color:#409eff">{{ avgRtt.toFixed(1) }}ms</div></div>
      <div class="stat-box"><div class="lbl">Jitter</div><div class="val" :style="{color:jitterVal>10?'#f56c6c':'#67c23a'}">{{ jitterVal.toFixed(2) }}ms</div></div>
    </div>

    <!-- ECharts Jitter 图 -->
    <div ref="chartRef" style="width:100%;height:320px;margin-top:16px"></div>

    <!-- 实时列表 -->
    <el-table :data="recentResults" style="margin-top:12px" v-if="recentResults.length" size="small" max-height="300" border>
      <el-table-column prop="seq" label="序号" width="70" />
      <el-table-column prop="rtt_ms" label="RTT" width="90" align="center">
        <template #default="{row}">
          <span v-if="row.lost" style="color:#f56c6c">超时</span>
          <span v-else :style="{color:row.rtt_ms<50?'#67c23a':'#e6a23c'}">{{ row.rtt_ms }}ms</span>
        </template>
      </el-table-column>
      <el-table-column prop="jitter_ms" label="Jitter" width="100" align="center">
        <template #default="{row}">{{ row.jitter_ms }}ms</template>
      </el-table-column>
      <el-table-column prop="avg_rtt" label="滑动平均" width="100" align="center" />
      <el-table-column label="延迟条" min-width="150">
        <template #default="{row}">
          <div class="rtt-bar"><div :style="{width:((row.rtt_ms||0)/maxRtt*100)+'%',background:row.lost?'#f56c6c':'#67c23a'}" /></div>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!isRunning && !results.length" description="高频 Ping 计算网络抖动（Jitter）" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useSseStream } from '@/composables/useSseStream'
import * as echarts from 'echarts'

const target = ref('')
const packetCount = ref(100)
const intervalMs = ref(20)
const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

interface JitterItem { seq: number; rtt_ms: number; jitter_ms: number; lost: boolean; loss_count: number; avg_rtt: number }
const results = ref<JitterItem[]>([])
const sseUrl = computed(() => `/api/diagnostics/jitter/stream?target=${encodeURIComponent(target.value)}&packet_count=${packetCount.value}&interval_ms=${intervalMs.value}`)
const stream = useSseStream<JitterItem>(sseUrl)
const { isRunning, stop } = stream

const recentResults = computed(() => results.value.slice(-50))
const lossCount = computed(() => results.value.filter(r => r.lost).length)
const lossPct = computed(() => results.value.length ? lossCount.value / results.value.length * 100 : 0)
const jitterVal = computed(() => results.value.length ? results.value[results.value.length-1].jitter_ms : 0)
const avgRtt = computed(() => results.value.length ? results.value[results.value.length-1].avg_rtt : 0)
const maxRtt = computed(() => Math.max(...results.value.map(r => r.rtt_ms || 0), 1))

watch(results, async () => {
    await nextTick()
    if (!chartRef.value) return
    if (!chart) chart = echarts.init(chartRef.value)
    const seqs = results.value.map(r => r.seq)
    const rtts = results.value.map(r => r.lost ? null : r.rtt_ms)
    const jitters = results.value.map(r => r.jitter_ms)
    chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['RTT(ms)', 'Jitter(ms)'] },
        xAxis: { type: 'category', data: seqs, name: '序号' },
        yAxis: [
            { type: 'value', name: 'RTT(ms)' },
            { type: 'value', name: 'Jitter(ms)', axisLabel: { formatter: '{value}' } },
        ],
        series: [
            { name: 'RTT(ms)', type: 'line', data: rtts, smooth: true, symbol: 'none', lineStyle: { color: '#409eff' } },
            { name: 'Jitter(ms)', type: 'line', yAxisIndex: 1, data: jitters, smooth: true, symbol: 'none', lineStyle: { color: '#e6a23c' } },
        ],
        grid: { left: 50, right: 50, top: 40, bottom: 40 },
    }, true)
}, { deep: true })  // deep:true 确保 push 操作触发 watch 回调

function updateChartDirectly(d: JitterItem) {
    // 直接在回调里更新图表，不依赖 watch（更即时）
    if (!chartRef.value) return
    if (!chart) chart = echarts.init(chartRef.value)
    const seqs = results.value.map(r => r.seq)
    const rtts = results.value.map(r => r.lost ? null : r.rtt_ms)
    const jitters = results.value.map(r => r.jitter_ms)
    chart.setOption({
        series: [
            { data: rtts },
            { data: jitters },
        ],
        xAxis: { data: seqs },
    })
}

function startDiag() {
    const currentTarget = target.value.trim()
    results.value = []
    stream.onProgress = (d: JitterItem) => { results.value.push(d); updateChartDirectly(d) }
    stream.onError = (e: string) => { ElMessage.error('抖动分析失败: ' + e) }
    stream.onComplete = () => {
        const validRtts = results.value.filter(r => !r.lost && r.rtt_ms > 0).map(r => r.rtt_ms)
        const avgRtt = validRtts.length ? +(validRtts.reduce((a,b)=>a+b,0)/validRtts.length).toFixed(1) : 0
        const lost = results.value.filter(r => r.lost).length
        const lossPercent = results.value.length ? +((lost / results.value.length) * 100).toFixed(1) : 0
        const saveParams = new URLSearchParams({
            diagnostic_type: 'jitter', target: currentTarget,
            avg_rtt: String(avgRtt), loss_percent: String(lossPercent),
            status: 'ok',
        })
        fetch('/api/diagnostics/history/save?' + saveParams, { method: 'GET' }).catch(() => {})
    }
    stream.start()
}

onMounted(() => {
    if (chartRef.value) chart = echarts.init(chartRef.value)
})
</script>

<style scoped>
.diag-page { padding: 24px; max-width: 1100px; margin: 0 auto; }
.diag-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.diag-header h2 { margin: 0; font-size: 20px; }
.param-card { margin-bottom: 12px; }
.stats-row { display: flex; gap: 12px; margin: 12px 0; }
.stat-box { background: #f5f7fa; border-radius: 8px; padding: 8px 18px; text-align: center; }
.stat-box .lbl { font-size: 11px; color: #909399; }
.stat-box .val { font-size: 20px; font-weight: 700; }
.rtt-bar { height: 12px; background: #f0f0f0; border-radius: 3px; overflow: hidden; }
.rtt-bar div { height: 100%; border-radius: 3px; transition: width .3s; }
</style>

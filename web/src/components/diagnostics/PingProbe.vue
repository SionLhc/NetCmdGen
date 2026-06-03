<template>
  <div class="ping-probe" :class="{ running: isRunning }">
    <!-- 控制栏 -->
    <div class="probe-controls">
      <div class="control-row">
        <div class="target-input-wrap">
          <span class="input-label">目标地址</span>
          <el-input
            v-model="target"
            placeholder="8.8.8.8 或 baidu.com"
            size="default"
            :disabled="isRunning"
            class="target-input"
            @keyup.enter="startPing"
          >
            <template #prefix>
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="2" x2="12" y2="6"/>
                <line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
                <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/>
                <line x1="18" y1="12" x2="22" y2="12"/>
              </svg>
            </template>
          </el-input>
          <div class="param-group">
            <span class="param-label">发包</span>
            <el-input-number v-model="count" :min="1" :max="50" size="default" :disabled="isRunning" controls-position="right" />
          </div>
          <div class="param-group">
            <span class="param-label">超时</span>
            <el-input-number v-model="timeout" :min="0.5" :max="10" :step="0.5" size="default" :disabled="isRunning" />s
          </div>
        </div>
        <div class="action-btns">
          <el-button
            v-if="!isRunning"
            type="primary"
            size="default"
            @click="startPing"
            :loading="false"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            开始 Ping
          </el-button>
          <el-button
            v-else
            type="danger"
            size="default"
            @click="stopPing"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" class="btn-icon">
              <rect x="4" y="4" width="16" height="16" rx="2"/>
            </svg>
            停止
          </el-button>
        </div>
      </div>

      <!-- 实时汇总参数 -->
      <div v-if="isRunning || results.length > 0" class="ping-summary-bar">
        <span class="summary-target">{{ target }}</span>
        <div class="summary-stats">
          <span class="stat-item">
            <span class="stat-label">进度</span>
            <span class="stat-value" style="color:#6366f1">{{ results.length }}/{{ count }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">接收</span>
            <span class="stat-value" :style="{ color: receivedCount > 0 ? '#10b981' : '#94a3b8' }">{{ receivedCount }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">丢包</span>
            <span class="stat-value" :style="{ color: lossPercent > 0 ? '#ef4444' : '#10b981' }">{{ lossPercent }}%</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">最小</span>
            <span class="stat-value" style="color:#3b82f6">{{ minRtt != null ? minRtt + 'ms' : '--' }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">最大</span>
            <span class="stat-value" style="color:#f59e0b">{{ maxRtt != null ? maxRtt + 'ms' : '--' }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">平均</span>
            <span class="stat-value" style="color:#8b5cf6">{{ avgRtt != null ? avgRtt + 'ms' : '--' }}</span>
          </span>
        </div>
        <!-- 丢包率进度条 -->
        <div class="loss-bar-wrap">
          <div class="loss-bar">
            <div class="loss-received" :style="{ width: (100 - lossPercent) + '%' }"></div>
            <div class="loss-lost" :style="{ width: lossPercent + '%' }" v-if="lossPercent > 0"></div>
          </div>
          <span class="loss-label">{{ 100 - lossPercent }}% 可达</span>
        </div>
      </div>
    </div>

    <!-- 核心图表区域：双栏布局（图表 + 实时列表） -->
    <div v-if="results.length > 0" class="probe-body">
      <!-- 左侧：延迟波动图 -->
      <div class="chart-panel">
        <div class="panel-header">
          <span class="panel-title">延迟波动 (ms)</span>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background:#6366f1"></span> 延迟</span>
            <span class="legend-item"><span class="legend-dot" style="background:#ef4444"></span> 超时</span>
            <span class="legend-item" v-if="avgRtt != null"><span class="legend-dash"></span> 平均 {{ avgRtt }}ms</span>
          </div>
        </div>
        <div ref="chartRef" class="chart-container"></div>
      </div>

      <!-- 右侧：实时数据流列表 -->
      <div class="stream-panel">
        <div class="panel-header">
          <span class="panel-title">实时数据流</span>
          <span class="panel-badge">{{ results.length }} 包</span>
        </div>
        <div ref="streamListRef" class="stream-list">
          <transition-group name="packet-slide">
            <div
              v-for="r in results"
              :key="r.seq"
              class="packet-item"
              :class="{ timeout: r.status === 'timeout', latest: r.seq === results.length }"
            >
              <span class="packet-seq">#{{ r.seq }}</span>
              <div class="packet-bar-wrap">
                <div
                  class="packet-bar"
                  :style="{
                    width: r.rtt != null ? Math.min((r.rtt / maxBarRtt) * 100, 100) + '%' : '0%',
                    background: r.rtt == null
                      ? '#fca5a5'
                      : r.rtt < 30 ? 'linear-gradient(90deg, #10b981, #34d399)'
                      : r.rtt < 100 ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                      : 'linear-gradient(90deg, #ef4444, #f87171)'
                  }"
                ></div>
              </div>
              <span class="packet-val" :class="{
                'val-ok': r.rtt != null && r.rtt < 30,
                'val-warn': r.rtt != null && r.rtt >= 30 && r.rtt < 100,
                'val-bad': r.rtt != null && r.rtt >= 100,
                'val-timeout': r.rtt == null
              }">
                {{ r.rtt != null ? r.rtt + 'ms' : '超时' }}
              </span>
              <span class="packet-indicator" :class="{ 'ind-timeout': r.status === 'timeout', 'ind-ok': r.status === 'ok' }"></span>
            </div>
          </transition-group>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!isRunning" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/>
      </svg>
      <p>输入目标地址，点击"开始 Ping"进行网络连通性探测</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { doPingStream } from '@/api'
import * as echarts from 'echarts'

/* ── 参数 ── */
const target = ref('8.8.8.8')
const count = ref(10)
const timeout = ref(2.0)
const isRunning = ref(false)

/* ── 结果数据 ── */
interface PingItem { seq: number; rtt: number | null; status: string }
const results = ref<PingItem[]>([])

let streamController: AbortController | null = null
let chartInstance: echarts.ECharts | null = null
const chartRef = ref<HTMLElement | null>(null)
const streamListRef = ref<HTMLElement | null>(null)

/* ── 计算属性 ── */
const receivedCount = computed(() => results.value.filter(r => r.rtt !== null).length)
const lossPercent = computed(() => {
  if (results.value.length === 0) return 0
  const lost = results.value.filter(r => r.rtt === null).length
  return Math.round((lost / results.value.length) * 100)
})
const allRtts = computed(() => results.value.map(r => r.rtt).filter(v => v !== null) as number[])
const minRtt = computed(() => allRtts.value.length ? Math.min(...allRtts.value) : null)
const maxRtt = computed(() => allRtts.value.length ? Math.max(...allRtts.value) : null)
const avgRtt = computed(() => {
  if (allRtts.value.length === 0) return null
  return Math.round((allRtts.value.reduce((a, b) => a + b, 0) / allRtts.value.length) * 10) / 10
})
const maxBarRtt = computed(() => {
  const m = maxRtt.value
  return m ? Math.max(m * 1.2, 50) : 100
})

/* ── Ping 控制 ── */
function startPing() {
  if (!target.value.trim()) {
    ElMessage.warning('请输入目标地址')
    return
  }
  results.value = []
  isRunning.value = true

  streamController = doPingStream(
    target.value, count.value, timeout.value,
    // onProgress — 每收到新数据实时更新
    (data) => {
      results.value = [...data.results]
      nextTick(() => {
        updateChart()
        scrollToBottom()
      })
    },
    // onDone — 完成后最终更新
    (data) => {
      results.value = [...data.results]
      isRunning.value = false
      nextTick(() => {
        updateChart()
        scrollToBottom()
      })
      ElMessage.success(`Ping 完成: ${data.received}/${data.sent} 接收, ${data.loss_percent}% 丢包`)
    },
    // onError
    (err) => {
      isRunning.value = false
      ElMessage.error('Ping 失败: ' + (err?.message || '未知错误'))
    }
  )
}

function stopPing() {
  if (streamController) {
    streamController.abort()
    streamController = null
  }
  isRunning.value = false
  ElMessage.info('已停止')
}

/* ── ECharts 延迟波动图 ── */
function updateChart() {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value!)
  }

  const seqs = results.value.map(r => `#${r.seq}`)
  const rtts = results.value.map(r => r.rtt ?? null)
  const avg = avgRtt.value

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15,23,42,0.9)',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter: (params: any) => {
        const p = params[0]
        const val = p.data != null ? `${p.data}ms` : '超时'
        return `<b>${p.axisValue}</b><br/>延迟: ${val}`
      }
    },
    grid: { top: 12, right: 16, bottom: 28, left: 44 },
    xAxis: {
      type: 'category',
      data: seqs,
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisLabel: { color: '#64748b', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      name: 'ms',
      nameTextStyle: { color: '#94a3b8', fontSize: 10 },
      axisLabel: { color: '#94a3b8', fontSize: 10, formatter: '{value}' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    series: [{
      type: 'line',
      data: rtts,
      name: '延迟',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { color: '#6366f1', width: 2 },
      itemStyle: { color: '#6366f1' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(99,102,241,0.2)' },
          { offset: 1, color: 'rgba(99,102,241,0.02)' },
        ]),
      },
      markLine: avg != null ? {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#f59e0b', type: 'dashed', width: 1.5 },
        label: { formatter: `avg ${avg}ms`, color: '#f59e0b', fontSize: 10 },
        data: [{ yAxis: avg }],
      } : undefined,
      connectNulls: false,
    }],
  }, true)
}

/* 滚动到最新数据 */
function scrollToBottom() {
  if (streamListRef.value) {
    streamListRef.value.scrollTop = streamListRef.value.scrollHeight
  }
}

/* 窗口 resize 时重绘图表 */
function handleResize() {
  chartInstance?.resize()
}
watch(() => results.value.length, () => {
  nextTick(() => {
    chartInstance?.resize()
  })
})
import { onMounted, onUnmounted } from 'vue'
onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.ping-probe {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  transition: border-color 0.3s;
}
.ping-probe.running { border-color: #6366f1; box-shadow: 0 0 0 2px rgba(99,102,241,0.1); }

/* ── 控制栏 ── */
.probe-controls { padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
.control-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.target-input-wrap { flex: 1; min-width: 320px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.input-label { font-size: 13px; font-weight: 600; color: #475569; white-space: nowrap; }
.target-input { max-width: 240px; }
.param-group { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #64748b; }
.param-label { font-size: 12px; color: #94a3b8; }
.action-btns { display: flex; gap: 8px; flex-shrink: 0; }
.btn-icon { width: 16px; height: 16px; }
.input-icon { width: 16px; height: 16px; }

/* ── 汇总条 ── */
.ping-summary-bar {
  margin-top: 12px;
  padding: 10px 14px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
}
.summary-target { font-size: 13px; font-weight: 600; color: #1e293b; font-family: monospace; }
.summary-stats { display: flex; gap: 16px; margin-top: 6px; flex-wrap: wrap; }
.stat-item { display: flex; align-items: center; gap: 4px; }
.stat-label { font-size: 11px; color: #94a3b8; }
.stat-value { font-size: 14px; font-weight: 700; font-family: monospace; }

.loss-bar-wrap { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
.loss-bar { flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; display: flex; }
.loss-received { background: linear-gradient(90deg, #10b981, #34d399); transition: width 0.3s; }
.loss-lost { background: linear-gradient(90deg, #ef4444, #f87171); transition: width 0.3s; }
.loss-label { font-size: 11px; color: #64748b; white-space: nowrap; min-width: 56px; text-align: right; }

/* ── 核心展示区 ── */
.probe-body { display: grid; grid-template-columns: 1fr 260px; gap: 0; }
@media (max-width: 768px) {
  .probe-body { grid-template-columns: 1fr; }
}

.chart-panel {
  padding: 0;
  border-right: 1px solid #f1f5f9;
  display: flex; flex-direction: column;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f8fafc;
}
.panel-title { font-size: 13px; font-weight: 600; color: #334155; }
.panel-badge {
  font-size: 11px; color: #6366f1; background: rgba(99,102,241,0.08);
  padding: 2px 8px; border-radius: 10px;
}
.chart-legend { display: flex; gap: 12px; align-items: center; }
.legend-item { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #94a3b8; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; }
.legend-dash { width: 12px; height: 0; border-top: 1.5px dashed #f59e0b; }
.chart-container { height: 240px; }

/* ── 实时数据流 ── */
.stream-panel { display: flex; flex-direction: column; background: #fafbfc; }
.stream-list {
  flex: 1;
  overflow-y: auto;
  max-height: 280px;
  padding: 8px 12px;
  display: flex; flex-direction: column; gap: 2px;
}
.stream-list::-webkit-scrollbar { width: 4px; }
.stream-list::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 2px; }

.packet-item {
  display: flex; align-items: center; gap: 8px;
  padding: 5px 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}
.packet-item.latest { background: rgba(99,102,241,0.04); }
.packet-item.timeout { background: rgba(239,68,68,0.04); }
.packet-seq { font-size: 11px; color: #94a3b8; font-family: monospace; width: 24px; flex-shrink: 0; }
.packet-bar-wrap { flex: 1; height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden; }
.packet-bar { height: 100%; border-radius: 3px; transition: width 0.3s ease; min-width: 2px; }
.packet-val { font-size: 12px; font-weight: 600; font-family: monospace; width: 54px; text-align: right; }
.val-ok { color: #10b981; }
.val-warn { color: #f59e0b; }
.val-bad { color: #ef4444; }
.val-timeout { color: #ef4444; }
.packet-indicator { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.ind-ok { background: #10b981; }
.ind-timeout { background: #ef4444; }

/* 动画 */
.packet-slide-enter-active { transition: all 0.3s ease; }
.packet-slide-enter-from { opacity: 0; transform: translateX(-12px); }

/* 空状态 */
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 48px 20px; color: #94a3b8; gap: 12px;
}
.empty-icon { width: 40px; height: 40px; color: #cbd5e1; }
.empty-state p { font-size: 13px; }
</style>

<template>
  <div class="trace-map" :class="{ running: isRunning }">
    <!-- 控制栏 -->
    <div class="trace-controls">
      <div class="control-row">
        <div class="target-input-wrap">
          <span class="input-label">目标地址</span>
          <el-input
            v-model="target"
            placeholder="8.8.8.8 或 baidu.com"
            size="default"
            :disabled="isRunning"
            class="target-input"
            @keyup.enter="startTrace"
          >
            <template #prefix>
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
              </svg>
            </template>
          </el-input>
          <div class="param-group">
            <span class="param-label">最大跳</span>
            <el-input-number v-model="maxHops" :min="1" :max="30" size="default" :disabled="isRunning" />
          </div>
          <div class="param-group">
            <span class="param-label">超时</span>
            <el-input-number v-model="timeout" :min="0.5" :max="5" :step="0.5" size="default" :disabled="isRunning" />s
          </div>
        </div>
        <div class="action-btns">
          <el-button
            v-if="!isRunning"
            type="primary"
            size="default"
            @click="startTrace"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="btn-icon">
              <line x1="12" y1="2" x2="12" y2="22"/><polyline points="19 9 12 2 5 9"/>
            </svg>
            开始追踪
          </el-button>
          <el-button v-else type="danger" size="default" @click="stopTrace">
            <svg viewBox="0 0 24 24" fill="currentColor" class="btn-icon">
              <rect x="4" y="4" width="16" height="16" rx="2"/>
            </svg>
            停止
          </el-button>
        </div>
      </div>

      <!-- 汇总信息 -->
      <div v-if="hops.length > 0" class="trace-summary">
        <span class="summary-target">{{ target }}</span>
        <span class="summary-divider">→</span>
        <span class="summary-info">
          <span class="info-badge" :class="reachedTarget ? 'reached' : 'unreached'">
            {{ reachedTarget ? '已到达' : '追踪中' }}
          </span>
          <span class="info-hops">{{ hops.length }} 跳</span>
          <span v-if="finalAvgLatency" class="info-latency">
            全程 {{ finalAvgLatency }}ms
          </span>
        </span>
      </div>
    </div>

    <!-- 逐跳拓扑可视化：图表容器始终存在，防止 v-if 导致 Grid 布局延时 -->
    <div class="trace-body">
      <!-- 节点路径视图 -->
      <div class="hop-path" v-show="hops.length > 0">
        <div
          v-for="(hop, idx) in hops"
          :key="hop.hop"
          class="hop-node-group"
        >
          <!-- 连线 -->
          <div v-if="idx > 0" class="hop-edge" :class="{ 'edge-timeout': hop.ip === '超时' }">
            <div class="edge-line"></div>
            <div class="edge-rtt" v-if="hop.avg_rtt != null">{{ hop.avg_rtt }}ms</div>
          </div>

          <!-- 节点 -->
          <div
            class="hop-node"
            :class="{
              'node-ttl': hop.avg_rtt == null && hop.ip !== '超时',
              'node-timeout': hop.ip === '超时',
              'node-reached': hop.reached,
              'node-latest': idx === hops.length - 1 && isRunning,
            }"
          >
            <div class="node-circle">
              <!-- 到达目标 → 绿色对勾 -->
              <svg v-if="hop.reached" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="node-check"><polyline points="20 6 9 17 4 12"/></svg>
              <!-- TTL 过期但有 IP → 蓝色箭头 -->
              <span v-else-if="hop.avg_rtt == null && hop.ip !== '超时'" class="node-number" style="font-size:11px">→</span>
              <!-- 完全超时 → 红色 X -->
              <span v-else-if="hop.ip === '超时'" class="node-x">✕</span>
              <!-- 正常有 RTT → 跳数 -->
              <span v-else class="node-number">{{ hop.hop }}</span>
            </div>
            <div class="node-info">
              <div class="node-ip" :style="{
                color: hop.reached ? '#10b981' : hop.ip === '超时' ? '#ef4444' : '#475569',
                fontWeight: hop.reached ? 700 : hop.ip === '超时' ? 400 : 600,
              }">
                {{ hop.ip }}
              </div>
              <div class="node-meta">
                <!-- 有延迟 → 显示 ms -->
                <span v-if="hop.avg_rtt != null" class="meta-rtt" :class="{
                  'rtt-fast': hop.avg_rtt < 10,
                  'rtt-normal': hop.avg_rtt >= 10 && hop.avg_rtt < 50,
                  'rtt-slow': hop.avg_rtt >= 50
                }">{{ hop.avg_rtt }}ms</span>
                <!-- TTL 过期有 IP → 显示"转发"（成功收到路由器回复只是无延迟） -->
                <span v-else-if="hop.ip !== '超时'" class="meta-fwd">转发</span>
                <!-- 完全超时 -->
                <span v-else class="meta-loss">超时</span>
              </div>
            </div>
            <!-- 到达标记 -->
            <div v-if="hop.reached" class="node-badge">到达</div>
          </div>
        </div>

        <!-- 加载动画（追踪中） -->
        <div v-if="isRunning" class="hop-loading">
          <div class="edge-line loading-line"></div>
          <div class="loading-dot"></div>
          <span class="loading-text">探测中...</span>
        </div>
      </div>

      <!-- 空状态覆盖（grid 中跨两列） -->
      <div v-if="hops.length === 0 && !isRunning" class="empty-state" style="grid-column:1/-1">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><circle cx="5" cy="19" r="2"/>
          <line x1="12" y1="7" x2="7" y2="16"/><line x1="12" y1="7" x2="17" y2="16"/>
        </svg>
        <p>输入目标地址，点击"开始追踪"查看数据包经过的路由节点</p>
      </div>

      <!-- 侧边栏：ECharts 延迟柱状图，容器始终在 DOM 确保布局正确 -->
      <div class="trace-chart-panel" v-show="hops.length > 0">
        <div class="chart-header">
          <span>逐跳延迟对比 (ms)</span>
        </div>
        <div ref="traceChartRef" class="trace-chart"></div>
      </div>
    </div>

    <!-- 旧空状态（保留兼容） -->
    <div v-if="false" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><circle cx="5" cy="19" r="2"/>
        <line x1="12" y1="7" x2="7" y2="16"/><line x1="12" y1="7" x2="17" y2="16"/>
      </svg>
      <p>输入目标地址，点击"开始追踪"查看数据包经过的路由节点</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { doTraceStream } from '@/api'
import * as echarts from 'echarts'

/* ── 参数 ── */
const target = ref('8.8.8.8')
const maxHops = ref(15)
const timeout = ref(2.0)
const isRunning = ref(false)

/* ── 结果数据 ── */
interface HopItem {
  hop: number
  ip: string
  rtts: (number | null)[]
  avg_rtt: number | null
  reached: boolean
  loss: number
}
const hops = ref<HopItem[]>([])

let streamController: AbortController | null = null
let traceChart: echarts.ECharts | null = null
const traceChartRef = ref<HTMLElement | null>(null)

/* ── 计算属性 ── */
const reachedTarget = computed(() => {
  const last = hops.value[hops.value.length - 1]
  return last?.reached ?? false
})
const finalAvgLatency = computed(() => {
  const last = hops.value[hops.value.length - 1]
  return last?.avg_rtt ?? null
})

/* ── Traceroute 控制 ── */
function startTrace() {
  if (!target.value.trim()) {
    ElMessage.warning('请输入目标地址')
    return
  }
  const currentTarget = target.value.trim()  // 闭包捕获，防止回调时值被修改
  hops.value = []
  isRunning.value = true

  streamController = doTraceStream(
    target.value, maxHops.value, timeout.value, 3,
    // onProgress — 每完成一跳推送
    (data) => {
      hops.value = [...data.hops]
      nextTick(() => updateChart())
    },
    // onDone — 全部完成 + 保存历史
    (data) => {
      hops.value = [...data.hops]
      isRunning.value = false
      // 保存历史：取最后一跳的 avg_rtt（使用捕获的目标值）
      const lastHop = data.hops?.[data.hops.length - 1]
      const saveParams = new URLSearchParams({
        diagnostic_type: 'traceroute',
        target: currentTarget,
        avg_rtt: String(lastHop?.avg_rtt ?? 0),
        loss_percent: String(lastHop?.loss ?? 0),
        status: reachedTarget.value ? 'ok' : 'error',
      })
      fetch('/api/diagnostics/history/save?' + saveParams, { method: 'GET' }).catch(() => {})
      nextTick(() => updateChart())
      if (reachedTarget.value) {
        ElMessage.success(`路由追踪完成: ${data.total_hops} 跳到达目标`)
      } else {
        ElMessage.warning(`追踪结束: ${data.total_hops} 跳，未到达目标`)
      }
    },
    // onError
    (err) => {
      isRunning.value = false
      ElMessage.error('路由追踪失败: ' + (err?.message || '未知错误'))
    }
  )
}

function stopTrace() {
  if (streamController) {
    streamController.abort()
    streamController = null
  }
  isRunning.value = false
  ElMessage.info('已停止')
}

/* ── ECharts 逐跳延迟柱状图 ── */
function updateChart() {
  if (!traceChartRef.value) return
  if (!traceChart) {
    traceChart = echarts.init(traceChartRef.value!)
  }
  renderTraceChart()
}

/** 将 hops 数据渲染到 ECharts 柱状图，所有跳都有柱子 */
function renderTraceChart() {
  if (!traceChart) return
  const hopNums = hops.value.map(h => `#${h.hop}`)
  const ips = hops.value.map(h => h.ip)

  traceChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15,23,42,0.9)',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter: (params: any) => {
        const p = params[0]
        const idx = p.dataIndex
        const hop = hops.value[idx]
        const val = hop.avg_rtt
        const ip = ips[idx]
        if (val == null) {
          return `<b>#${hop.hop} ${ip}</b><br/>延迟: — (无响应)`
        }
        return `<b>#${hop.hop} ${ip}</b><br/>延迟: ${val}ms`
      }
    },
    grid: { top: 16, right: 18, bottom: 36, left: 44 },
    xAxis: {
      type: 'category',
      data: hopNums,
      axisLabel: {
        color: '#64748b', fontSize: 10,
      },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: {
      type: 'value',
      name: 'ms',
      nameTextStyle: { color: '#94a3b8', fontSize: 10 },
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      splitLine: { lineStyle: { color: '#f8fafc' } },
    },
    series: [{
      type: 'bar',
      barWidth: '50%',
      data: hops.value.map((h) => {
        const val = h.avg_rtt
        const hasRtt = val != null
        return {
          // 有延迟 → 实际值，无延迟 → 固定小高度占位
          value: val ?? 3,
          itemStyle: {
            // 有延迟 → 按数值着色，无延迟 → 灰色实心
            color: hasRtt
              ? (h.reached ? '#10b981' : val! < 10 ? '#6366f1' : val! < 50 ? '#f59e0b' : '#ef4444')
              : '#cbd5e1',
            borderRadius: [3, 3, 0, 0],
          },
        }
      }),
      label: {
        show: true,
        position: 'top',
        fontSize: 10,
        color: '#1e293b',
        formatter: (p: any) => {
          const val = hops.value[p.dataIndex]?.avg_rtt
          return val != null ? val + 'ms' : '—'
        },
      },
    }],
  }, true)
}

/* resize */
function handleResize() { traceChart?.resize() }
watch(() => hops.value.length, () => nextTick(() => traceChart?.resize()))
import { onMounted, onUnmounted } from 'vue'
onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  traceChart?.dispose()
})
</script>

<style scoped>
.trace-map {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  transition: border-color 0.3s;
}
.trace-map.running { border-color: #6366f1; box-shadow: 0 0 0 2px rgba(99,102,241,0.1); }

/* ── 控制栏 ── */
.trace-controls { padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
.control-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.target-input-wrap { flex: 1; min-width: 320px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.input-label { font-size: 13px; font-weight: 600; color: #475569; white-space: nowrap; }
.target-input { max-width: 240px; }
.param-group { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #64748b; }
.param-label { font-size: 12px; color: #94a3b8; }
.action-btns { display: flex; gap: 8px; flex-shrink: 0; }
.btn-icon { width: 16px; height: 16px; }
.input-icon { width: 16px; height: 16px; }

.trace-summary {
  margin-top: 12px; padding: 10px 14px;
  background: #f8fafc; border-radius: 8px; border: 1px solid #f1f5f9;
  display: flex; align-items: center; gap: 10px;
}
.summary-target { font-size: 13px; font-weight: 600; color: #1e293b; font-family: monospace; }
.summary-divider { color: #94a3b8; font-size: 14px; }
.summary-info { display: flex; align-items: center; gap: 8px; }
.info-badge {
  font-size: 11px; padding: 2px 8px; border-radius: 8px; font-weight: 600;
}
.info-badge.reached { background: rgba(16,185,129,0.1); color: #10b981; }
.info-badge.unreached { background: rgba(245,158,11,0.1); color: #f59e0b; }
.info-hops { font-size: 12px; color: #64748b; }
.info-latency { font-size: 12px; color: #8b5cf6; font-family: monospace; }

/* ── 节点路径 ── */
.trace-body { display: grid; grid-template-columns: 1fr 220px; }
@media (max-width: 768px) {
  .trace-body { grid-template-columns: 1fr; }
}

.hop-path {
  padding: 16px 20px;
  max-height: 400px; overflow-y: auto;
  border-right: 1px solid #f1f5f9;
}
.hop-path::-webkit-scrollbar { width: 5px; }
.hop-path::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }

.hop-node-group { position: relative; }

/* 连线 */
.hop-edge {
  display: flex; align-items: center;
  height: 28px; margin-left: 18px;
  position: relative;
}
.edge-line {
  width: 2px; height: 100%;
  background: linear-gradient(180deg, #6366f1, #a5b4fc);
  position: absolute; left: 9px;
}
.hop-edge.edge-timeout .edge-line {
  background: linear-gradient(180deg, #fca5a5, #fee2e2);
}
.edge-rtt {
  margin-left: 28px; font-size: 10px; color: #a5b4fc; font-family: monospace;
}

/* 节点 */
.hop-node {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 12px; border-radius: 8px;
  background: #fafbfc; border: 1px solid #f1f5f9;
  transition: all 0.3s ease;
}
.hop-node.node-ttl { background: #eff6ff; border-color: #bfdbfe; }
.hop-node.node-timeout { background: #fef2f2; border-color: #fecaca; }
.hop-node.node-reached { background: #f0fdf4; border-color: #bbf7d0; }
.hop-node.node-latest { border-color: #a5b4fc; box-shadow: 0 0 0 2px rgba(99,102,241,0.1); }

.node-circle {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: transform 0.3s;
}
.node-ttl .node-circle { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.node-timeout .node-circle { background: linear-gradient(135deg, #ef4444, #dc2626); }
.node-reached .node-circle { background: linear-gradient(135deg, #10b981, #059669); }
.node-number { color: #fff; font-size: 13px; font-weight: 700; }
.node-x { color: #fff; font-size: 14px; font-weight: 700; }
.node-check { width: 16px; height: 16px; color: #fff; }

.node-info { flex: 1; min-width: 0; }
.node-ip { font-size: 14px; font-weight: 600; font-family: monospace; }
.node-meta { display: flex; gap: 8px; align-items: center; margin-top: 2px; }
.meta-rtt { font-size: 11px; font-weight: 600; font-family: monospace; }
.rtt-fast { color: #10b981; }
.rtt-normal { color: #f59e0b; }
.rtt-slow { color: #ef4444; }
.meta-loss { font-size: 11px; color: #ef4444; }
.meta-fwd { font-size: 11px; color: #3b82f6; }
.node-detail { display: flex; gap: 3px; margin-top: 3px; }
.detail-dot { width: 5px; height: 5px; border-radius: 50%; }
.detail-dot.dot-ok { background: #6366f1; }
.detail-dot.dot-lost { background: #fca5a5; }
.node-badge { font-size: 11px; font-weight: 600; color: #10b981; margin-left: auto; padding: 2px 8px; background: rgba(16,185,129,0.1); border-radius: 4px; }

/* 加载动画 */
.hop-loading {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 0 12px 18px; position: relative;
}
.loading-line {
  width: 2px; height: 28px;
  background: linear-gradient(180deg, #a5b4fc, transparent);
  position: absolute; left: 18px; top: 0;
}
.loading-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: #6366f1; margin-left: 12px;
  animation: pulse 1.2s ease infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.4); }
}
.loading-text { font-size: 12px; color: #a5b4fc; }

/* ── 图表面板 ── */
.trace-chart-panel {
  padding: 0; display: flex; flex-direction: column;
  background: #fafbfc;
}
.chart-header {
  font-size: 13px; font-weight: 600; color: #334155;
  padding: 12px 16px; border-bottom: 1px solid #f1f5f9;
}
.trace-chart { height: 320px; }

/* 空状态 */
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 48px 20px; color: #94a3b8; gap: 12px;
}
.empty-icon { width: 40px; height: 40px; color: #cbd5e1; }
.empty-state p { font-size: 13px; }
</style>

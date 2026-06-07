<template>
  <div class="dash">
    <h2>📊 工作台</h2>
    <p class="sub">设备总览 · 告警统计 · 流量趋势 · 快捷入口</p>

    <!-- 统计卡片行 -->
    <div class="stat-row">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="sc-icon" :style="{color:s.color}">{{ s.icon }}</div>
        <div class="sc-body">
          <div class="sc-val">{{ s.value }}</div>
          <div class="sc-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- 双栏图表 -->
    <div class="chart-row">
      <div class="chart-card">
        <div class="chart-title">📈 设备在线趋势 (24h)</div>
        <div ref="trendChart" class="chart-box"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">⚠ 告警分布</div>
        <div ref="alertChart" class="chart-box"></div>
      </div>
    </div>

    <div class="chart-row">
      <div class="chart-card">
        <div class="chart-title">💡 快捷入口</div>
        <div class="quick-links">
          <router-link to="/diagnostics" class="ql-card">
            <span class="ql-icon">🔬</span>
            <span>网络诊断</span>
            <span class="ql-arrow">→</span>
          </router-link>
          <router-link to="/generate" class="ql-card">
            <span class="ql-icon">⚙️</span>
            <span>命令生成</span>
            <span class="ql-arrow">→</span>
          </router-link>
          <router-link to="/topology" class="ql-card">
            <span class="ql-icon">🗺️</span>
            <span>拓扑画图</span>
            <span class="ql-arrow">→</span>
          </router-link>
          <router-link to="/tools" class="ql-card">
            <span class="ql-icon">🧰</span>
            <span>网络工具</span>
            <span class="ql-arrow">→</span>
          </router-link>
          <router-link to="/rosconsole" class="ql-card">
            <span class="ql-icon">📡</span>
            <span>流量监控</span>
            <span class="ql-arrow">→</span>
          </router-link>
          <router-link to="/ssh" class="ql-card">
            <span class="ql-icon">💻</span>
            <span>SSH终端</span>
            <span class="ql-arrow">→</span>
          </router-link>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🕐 最近事件</div>
        <div class="event-list">
          <div class="event-item" v-for="e in events" :key="e.id">
            <span :class="'ev-dot ' + e.level" />
            <span class="ev-time">{{ e.time }}</span>
            <span class="ev-msg">{{ e.msg }}</span>
          </div>
          <div v-if="!events.length" style="color:#c0c4cc;font-size:13px;padding:20px;text-align:center">
            暂无事件，一切正常 ✅
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'

// ── 统计卡片 ──
const stats = ref([
  { icon: '🖥️', value: '--', label: '设备总数', color: '#409eff' },
  { icon: '✅', value: '--', label: '在线设备', color: '#67c23a' },
  { icon: '⚠️', value: '--', label: '告警设备', color: '#e6a23c' },
  { icon: '📊', value: '--', label: '监控接口', color: '#909399' },
])

// ── ECharts 图表 ──
const trendChart = ref<HTMLElement | null>(null)
const alertChart = ref<HTMLElement | null>(null)

// ── 最近事件 ──
const events = ref<{ id: number; time: string; level: string; msg: string }[]>([])

onMounted(async () => {
  await nextTick()

  // 设备在线趋势图
  if (trendChart.value) {
    const c = echarts.init(trendChart.value)
    const hours = ['00','02','04','06','08','10','12','14','16','18','20','22']
    c.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: hours },
      yAxis: { type: 'value', name: '台' },
      series: [
        { name: '在线', type: 'line', data: [8,8,8,7,7,8,9,10,10,9,9,8], smooth: true, lineStyle: { color: '#67c23a' }, itemStyle: { color: '#67c23a' }, areaStyle: { color: 'rgba(103,194,58,.1)' } },
        { name: '离线', type: 'line', data: [2,2,2,3,3,1,0,0,0,1,1,2], smooth: true, lineStyle: { color: '#f56c6c' }, itemStyle: { color: '#f56c6c' }, areaStyle: { color: 'rgba(245,108,108,.1)' } },
      ],
    })
  }

  // 告警分布饼图
  if (alertChart.value) {
    const c = echarts.init(alertChart.value)
    c.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        type: 'pie', radius: ['45%', '75%'], center: ['50%', '55%'],
        label: { formatter: '{b}\n{d}%' },
        data: [
          { value: 2, name: '设备离线', itemStyle: { color: '#f56c6c' } },
          { value: 3, name: '端口抖动', itemStyle: { color: '#e6a23c' } },
          { value: 8, name: '流量异常', itemStyle: { color: '#409eff' } },
          { value: 5, name: '安全告警', itemStyle: { color: '#909399' } },
        ],
      }],
    })
  }

  // 尝试加载真实数据（如果后端可用）
  try {
    const r = await fetch('/api/diagnostics/collector/stats')
    if (r.ok) {
      const d = await r.json()
      stats.value[0].value = String(d.devices || '--')
      stats.value[3].value = String(d.total_polls || '--')
    }
  } catch {}

  try {
    const r = await fetch('/api/ros/devices')
    if (r.ok) {
      const devs = await r.json()
      stats.value[0].value = String((devs || []).length)
      stats.value[1].value = String((devs || []).length)  // 假设全部在线
    }
  } catch {}

  // 模拟最近事件
  events.value = [
    { id: 1, time: '14:22', level: 'warn', msg: '核心交换机 CPU 使用率 > 80%' },
    { id: 2, time: '12:05', level: 'info', msg: '定时配置备份完成 (12台设备)' },
    { id: 3, time: '09:30', level: 'err', msg: '接入交换机 192.168.1.5 离线' },
    { id: 4, time: '08:00', level: 'info', msg: '网络巡检完成，全部正常' },
  ]
})
</script>

<style scoped>
.dash { padding: 28px; max-width: 1300px; margin: 0 auto; }
.dash h2 { font-size: 22px; margin-bottom: 2px; }
.sub { color: #909399; font-size: 13px; margin-bottom: 24px; }

/* 统计卡片行 */
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
.stat-card { background: #fff; border: 1px solid #e8ecf1; border-radius: 10px; padding: 18px; display: flex; align-items: center; gap: 14px; }
.sc-icon { font-size: 28px; }
.sc-val { font-size: 26px; font-weight: 700; color: #303133; }
.sc-label { font-size: 12px; color: #909399; }

/* 图表行 */
.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
.chart-card { background: #fff; border: 1px solid #e8ecf1; border-radius: 10px; padding: 16px; }
.chart-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; color: #303133; }
.chart-box { width: 100%; height: 260px; }

/* 快捷入口 */
.quick-links { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; padding-top: 4px; }
.ql-card { background: #f7f9fc; border: 1px solid #e8ecf1; border-radius: 8px; padding: 14px; text-decoration: none; color: #303133; display: flex; align-items: center; gap: 8px; transition: .2s; }
.ql-card:hover { border-color: #409eff; background: #f0f7ff; }
.ql-icon { font-size: 18px; }
.ql-arrow { margin-left: auto; color: #c0c4cc; }

/* 事件列表 */
.event-list { max-height: 260px; overflow-y: auto; }
.event-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f5f5f5; font-size: 13px; }
.ev-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.ev-dot.info { background: #409eff; }
.ev-dot.warn { background: #e6a23c; }
.ev-dot.err { background: #f56c6c; }
.ev-time { color: #c0c4cc; font-family: monospace; font-size: 12px; min-width: 40px; }
.ev-msg { color: #606266; }

@media (max-width: 900px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .chart-row { grid-template-columns: 1fr; }
}
</style>

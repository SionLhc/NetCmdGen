<template>
  <div class="diag-page">
    <div class="diag-header">
      <el-button text @click="$router.push('/diagnostics')">← 返回诊断中心</el-button>
      <h2>📈 历史趋势对比</h2>
    </div>

    <el-card class="param-card">
      <el-form :inline="true" size="default">
        <el-form-item label="诊断类型">
          <el-select v-model="diagType" style="width:140px">
            <el-option label="Ping" value="ping" />
            <el-option label="Traceroute" value="traceroute" />
            <el-option label="DNS" value="dns" />
            <el-option label="TCP端口" value="tcp-port" />
            <el-option label="HTTP" value="http" />
            <el-option label="Jitter" value="jitter" />
          </el-select>
        </el-form-item>
        <el-form-item label="对比目标">
          <el-select v-model="targets" multiple filterable allow-create placeholder="输入域名/IP" style="width:300px" />
        </el-form-item>
        <el-form-item label="天数">
          <el-select v-model="days" style="width:100px">
            <el-option label="1天" :value="1" />
            <el-option label="3天" :value="3" />
            <el-option label="7天" :value="7" />
            <el-option label="14天" :value="14" />
            <el-option label="30天" :value="30" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadHistory" :loading="loading">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ECharts 趋势图 -->
    <div ref="chartRef" style="width:100%;height:380px;margin-top:16px" v-show="records.length"></div>

    <!-- 异常事件 -->
    <el-card v-if="anomalies.length" style="margin-top:16px">
      <template #header>⚠ 异常事件</template>
      <div v-for="(a,i) in anomalies" :key="i" style="padding:4px 0;font-size:13px">
        <el-tag size="small" :type="a.severity==='high'?'danger':'warning'">{{ a.severity==='high'?'严重':'警告' }}</el-tag>
        &nbsp;{{ a.time }}&nbsp;{{ a.target }}&nbsp;{{ a.message }}
      </div>
    </el-card>

    <!-- 历史表格 -->
    <el-table :data="records" style="margin-top:12px" v-if="records.length" size="small" border max-height="400">
      <el-table-column prop="target" label="目标" width="160" />
      <el-table-column prop="diagnostic_type" label="类型" width="100" />
      <el-table-column label="摘要" min-width="200">
        <template #default="{row}">
          <template v-if="row.summary?.avg_rtt !== undefined">平均 RTT: {{ row.summary.avg_rtt }}ms · 丢包: {{ row.summary.loss_percent }}%</template>
          <template v-else-if="row.summary?.status">状态: {{ row.summary.status }}</template>
          <span v-else style="color:#909399">-</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{row}">
          <el-tag :type="row.status==='ok'?'success':'danger'" size="small">{{ row.status==='ok'?'正常':'异常' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="160" />
    </el-table>

    <el-empty v-if="!loading && !records.length" description="暂无历史数据，运行诊断后自动保存" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const diagType = ref('ping')
const targets = ref<string[]>(['baidu.com'])
const days = ref(7)
const loading = ref(false)
const records = ref<any[]>([])
const anomalies = ref<any[]>([])
const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

async function loadHistory() {
    loading.value = true
    const params = new URLSearchParams({ targets: targets.value.join(','), diagnostic_type: diagType.value, days: String(days.value) })
    const res = await fetch(`/api/v1/diagnostics/history?${params}`)
    const data = await res.json()
    records.value = data.records || []

    // 异常检测：延迟突增 > 2 倍平均
    const anoms: any[] = []
    const targetMap: Record<string, any[]> = {}
    for (const r of records.value) {
        if (!targetMap[r.target]) targetMap[r.target] = []
        targetMap[r.target].push(r)
    }
    for (const [tgt, recs] of Object.entries(targetMap)) {
        const avgRtts = recs.map((r: any) => r.summary?.avg_rtt || 0).filter((v: number) => v > 0)
        if (!avgRtts.length) continue
        const mean = avgRtts.reduce((a: number, b: number) => a + b, 0) / avgRtts.length
        for (const r of recs) {
            const rtt = r.summary?.avg_rtt || 0
            if (rtt > mean * 2 && rtt > 50) {
                anoms.push({
                    time: r.created_at, target: tgt,
                    message: `延迟突增至 ${rtt}ms（平均 ${mean.toFixed(0)}ms）`,
                    severity: rtt > mean * 3 ? 'high' : 'medium',
                })
            }
        }
    }
    anomalies.value = anoms.slice(0, 20)

    // 画 ECharts
    await nextTick()
    if (!chartRef.value) return
    if (!chart) chart = echarts.init(chartRef.value)

    // 按时间分组
    const series: any[] = []
    const timeSet = new Set<string>()
    const targetData: Record<string, Record<string, number>> = {}
    for (const r of records.value) {
        const time = r.created_at?.substring(0, 16) || ''
        timeSet.add(time)
        if (!targetData[r.target]) targetData[r.target] = {}
        targetData[r.target][time] = r.summary?.avg_rtt || 0
    }
    const times = [...timeSet].sort()

    const colors = ['#409eff','#67c23a','#e6a23c','#f56c6c','#909399']
    let ci = 0
    for (const [tgt, data] of Object.entries(targetData)) {
        series.push({
            name: tgt, type: 'line',
            data: times.map(t => data[t] || null),
            smooth: true, symbol: 'circle', symbolSize: 4,
            lineStyle: { color: colors[ci % colors.length] },
        })
        ci++
    }

    chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: Object.keys(targetData) },
        xAxis: { type: 'category', data: times, name: '时间' },
        yAxis: { type: 'value', name: '延迟(ms)' },
        series,
        grid: { left: 60, right: 30, top: 50, bottom: 50 },
    })

    loading.value = false
}

onMounted(() => {
    if (chartRef.value) chart = echarts.init(chartRef.value)
})
</script>

<style scoped>
.diag-page { padding: 24px; max-width: 1200px; margin: 0 auto; }
.diag-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.diag-header h2 { margin: 0; font-size: 20px; }
.param-card { margin-bottom: 12px; }
</style>

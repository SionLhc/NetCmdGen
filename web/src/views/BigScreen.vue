<template>
  <div class="screen">
    <div class="screen-header"><h1>📡 NetCmdGen 运维态势大屏</h1><span class="screen-time">{{ now }}</span></div>
    <div class="stat-row">
      <div class="stat-box" v-for="s in stats" :key="s.label"><div class="sb-val" :style="{color:s.color}">{{ s.value }}</div><div class="sb-label">{{ s.label }}</div></div>
    </div>
    <div class="screen-grid">
      <div class="s-panel"><div class="p-title">📈 24h 设备在线趋势</div><div ref="trendChart" class="p-chart"></div></div>
      <div class="s-panel"><div class="p-title">⚠ 告警分布</div><div ref="alertChart" class="p-chart"></div></div>
      <div class="s-panel"><div class="p-title">🖥️ Top5 流量设备</div><table class="top-table"><tr v-for="d in top" :key="d.name"><td>{{ d.name }}</td><td style="color:#67c23a">{{ d.traffic }}</td><td>{{ d.cpu }}</td><td><span :style="{color:d.alerts?'#f56c6c':'#909399'}">{{ d.alerts }} 告警</span></td></tr></table></div>
      <div class="s-panel"><div class="p-title">📋 实时事件</div><div class="event-list" v-if="events.length"><div v-for="e in events" :key="e.time" class="ev-item"><span class="ev-t">{{ e.time }}</span><span :class="'ev-b '+e.level"/><span>{{ e.msg }}</span></div></div></div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
const now=ref(''); const stats=ref<any[]>([]); const top=ref<any[]>([]); const events=ref<any[]>([])
const trendChart=ref<HTMLElement|null>(null); const alertChart=ref<HTMLElement|null>(null)
setInterval(()=>{now.value=new Date().toLocaleString()},1000)
onMounted(async()=>{
  const r=await fetch('/api/bigscreen/overview'); const d=await r.json()
  stats.value=[{label:'设备总数',value:d.summary.total_devices,color:'#409eff'},{label:'在线',value:d.summary.online_devices,color:'#67c23a'},{label:'离线',value:d.summary.offline_devices,color:'#f56c6c'},{label:'今日告警',value:d.summary.alerts_today,color:'#e6a23c'},{label:'带宽使用率',value:d.summary.bandwidth_used+'%',color:'#409eff'},{label:'备份完成',value:d.summary.backup_ok,color:'#67c23a'}]
  top.value=d.top_devices; events.value=d.recent_events
  await nextTick()
  if(trendChart.value){const c=echarts.init(trendChart.value)
    c.setOption({tooltip:{trigger:'axis'},grid:{left:40,right:20,top:10,bottom:30},xAxis:{type:'category',data:d.trend_24h.map((t:any)=>t.time)},yAxis:{type:'value'},series:[{name:'在线',type:'line',data:d.trend_24h.map((t:any)=>t.online),smooth:true,areaStyle:{color:'rgba(103,194,58,.15)'},lineStyle:{color:'#67c23a'},itemStyle:{color:'#67c23a'}},{name:'离线',type:'line',data:d.trend_24h.map((t:any)=>t.offline),smooth:true,areaStyle:{color:'rgba(245,108,108,.15)'},lineStyle:{color:'#f56c6c'},itemStyle:{color:'#f56c6c'}}]})}
  if(alertChart.value){const c=echarts.init(alertChart.value)
    c.setOption({tooltip:{trigger:'item'},series:[{type:'pie',radius:['40%','70%'],center:['50%','50%'],label:{formatter:'{b}\n{d}%'},data:d.alert_distribution}]})}
})
</script>
<style scoped>
.screen{background:linear-gradient(135deg,#0f172a,#1e293b);min-height:100vh;padding:20px;color:#e2e8f0}
.screen-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}h1{font-size:24px;margin:0}.screen-time{font-size:14px;color:#94a3b8}
.stat-row{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:20px}
.stat-box{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:16px;text-align:center}.sb-val{font-size:28px;font-weight:700}.sb-label{font-size:12px;color:#94a3b8;margin-top:4px}
.screen-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.s-panel{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:14px}.p-title{font-size:14px;font-weight:600;margin-bottom:8px}.p-chart{width:100%;height:240px}
.top-table{width:100%;border-collapse:collapse;font-size:13px}.top-table td{padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.08)}
.event-list{max-height:240px;overflow-y:auto;font-size:13px}.ev-item{display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.06)}.ev-t{color:#64748b;font-family:monospace;min-width:40px}.ev-b{width:6px;height:6px;border-radius:50%}.ev-b.err{background:#f56c6c}.ev-b.warn{background:#e6a23c}.ev-b.info{background:#409eff}
</style>

<template>
  <div class="topo-stats" v-if="visible">
    <div class="ts-header">📊 拓扑统计 <span class="ts-close" @click="visible=false">✕</span></div>
    <div class="ts-grid">
      <div class="ts-item"><span class="ts-val">{{ stats.nodes }}</span><span class="ts-lbl">节点数</span></div>
      <div class="ts-item"><span class="ts-val">{{ stats.edges }}</span><span class="ts-lbl">链路数</span></div>
      <div class="ts-item"><span class="ts-val" style="color:#67c23a">{{ stats.online }}</span><span class="ts-lbl">在线</span></div>
      <div class="ts-item"><span class="ts-val" style="color:#f56c6c">{{ stats.offline }}</span><span class="ts-lbl">离线</span></div>
    </div>
    <div ref="chartRef" style="width:100%;height:120px;margin-top:8px"></div>
  </div>
  <button v-else class="ts-toggle" @click="visible=true" title="统计面板">📊</button>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
const props=defineProps<{nodes:number;edges:number;online:number;offline:number}>()
const visible=ref(true); const chartRef=ref<HTMLElement|null>(null); let chart:echarts.ECharts|null=null
const stats=ref({nodes:0,edges:0,online:0,offline:0})
watch(()=>[props.nodes,props.edges,props.online,props.offline],()=>{
  stats.value={nodes:props.nodes,edges:props.edges,online:props.online,offline:props.offline}
  if(chart) chart.setOption({series:[{data:[{value:props.online,name:'在线',itemStyle:{color:'#67c23a'}},{value:props.offline,name:'离线',itemStyle:{color:'#f56c6c'}}]}]})
},{immediate:true})
onMounted(async()=>{await nextTick();if(chartRef.value){chart=echarts.init(chartRef.value);chart.setOption({tooltip:{trigger:'item'},series:[{type:'pie',radius:['50%','75%'],center:['50%','50%'],label:{show:false},data:[]}]})}})
</script>
<style scoped>
.topo-stats{position:fixed;right:16px;top:80px;background:#fff;border:1px solid #e8ecf1;border-radius:10px;padding:12px;width:200px;z-index:100;box-shadow:0 2px 12px rgba(0,0,0,.1)}.ts-header{font-size:13px;font-weight:600;margin-bottom:8px;display:flex;justify-content:space-between}.ts-close{cursor:pointer;color:#c0c4cc}.ts-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}.ts-item{background:#f5f7fa;border-radius:6px;padding:8px;text-align:center}.ts-val{font-size:18px;font-weight:700;display:block}.ts-lbl{font-size:10px;color:#909399}.ts-toggle{position:fixed;right:16px;top:80px;z-index:100;border:1px solid #e0e0e0;border-radius:8px;background:#fff;padding:6px 10px;cursor:pointer}
</style>

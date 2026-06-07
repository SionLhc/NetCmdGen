<template>
  <div class="page"><h2>🔍 网络巡检</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="设备"><el-input v-model="devId" placeholder="设备ID" style="width:160px"/></el-form-item>
      <el-form-item><el-checkbox v-for="t in templates" :key="t.id" v-model="selected[t.id]" :label="t.id">{{ t.name }}</el-checkbox></el-form-item>
      <el-form-item><el-button type="primary" @click="run">执行巡检</el-button></el-form-item>
    </el-form></el-card>
    <el-alert v-if="report" :title="`得分: ${report.score} · 通过 ${report.passed}/${report.passed+report.failed}`" :type="report.score>=90?'success':report.score>=60?'warning':'error'" :closable="false" show-icon style="margin-bottom:12px"/>
    <el-table :data="reports" size="small" border><el-table-column prop="device_name" label="设备" width="120"/>
      <el-table-column prop="score" label="得分" width="60" align="center"><template #default="{row}"><span :style="{color:row.score>=90?'#67c23a':'#e6a23c'}">{{ row.score }}</span></template></el-table-column>
      <el-table-column label="详情"><template #default="{row}"><template v-if="row.report&&typeof row.report==='object'"><span v-for="(v,k) in row.report" :key="k" style="margin-right:8px"><el-tag :type="v.status==='pass'?'success':'danger'" size="small">{{ v.name }}</el-tag></span></template></template></el-table-column>
      <el-table-column prop="created_at" label="时间" width="160"/></el-table>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
const templates=ref<any[]>([]); const devId=ref(''); const selected=reactive<Record<string,boolean>>({}); const report=ref<any>(null); const reports=ref<any[]>([])
async function load(){const[r1,r2]=await Promise.all([fetch('/api/health/templates'),fetch('/api/health/reports')]);templates.value=await r1.json();reports.value=await r2.json();templates.value.forEach((t:any)=>selected[t.id]=true)}
async function run(){const checks=Object.entries(selected).filter(([,v])=>v).map(([k])=>k).join(',');const r=await fetch(`/api/health/run?device_id=${devId.value}&device_name=${devId.value}&checks=${checks}`,{method:'POST'});report.value=await r.json();load()}
onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:1300px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

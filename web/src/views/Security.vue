<template>
  <div class="page"><h2>🛡️ 安全基线检查</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="设备ID"><el-input v-model="devId" placeholder="device-01" style="width:160px"/></el-form-item>
      <el-form-item><el-checkbox-group v-model="selected"><el-checkbox v-for="c in checks" :key="c.id" :label="c.id">{{ c.name }}</el-checkbox></el-checkbox-group></el-form-item>
      <el-form-item><el-button type="primary" @click="run">执行检查</el-button></el-form-item>
    </el-form></el-card>
    <el-alert v-if="report" :title="`安全评分: ${report.score} · 通过 ${report.passed}/10`" :type="report.score>=80?'success':report.score>=60?'warning':'error'" :closable="false" show-icon style="margin-bottom:12px"/>
    <el-table :data="reports" size="small" border><el-table-column prop="device_name" label="设备" width="120"/>
      <el-table-column prop="score" label="评分" width="60" align="center"><template #default="{row}"><span :style="{color:row.score>=80?'#67c23a':row.score>=60?'#e6a23c':'#f56c6c'}">{{ row.score }}</span></template></el-table-column>
      <el-table-column label="检查结果"><template #default="{row}"><template v-if="row.report&&typeof row.report==='object'"><span v-for="(v,k) in row.report" :key="k" style="margin-right:6px"><el-tooltip :content="v.detail"><el-tag :type="v.status==='pass'?'success':'danger'" size="small">{{ v.name }}</el-tag></el-tooltip></span></template></template></el-table-column>
      <el-table-column prop="created_at" label="时间" width="160"/></el-table>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
const checks=ref<any[]>([]); const selected=ref<string[]>([]); const devId=ref(''); const report=ref<any>(null); const reports=ref<any[]>([])
async function load(){const[r1,r2]=await Promise.all([fetch('/api/security/checks'),fetch('/api/security/reports')]);checks.value=await r1.json();reports.value=await r2.json();checks.value.forEach((c:any)=>selected.value.push(c.id))}
async function run(){const r=await fetch(`/api/security/run?device_id=${devId.value}&device_name=${devId.value}&checks=${selected.value.join(',')}`,{method:'POST'});report.value=await r.json();load()}
onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:1300px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

<template>
  <div class="page"><h2>🔌 交换机防护</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="设备"><el-input v-model="devId" placeholder="设备ID" style="width:160px"/></el-form-item>
      <el-form-item><el-checkbox-group v-model="selected"><el-checkbox v-for="i in items" :key="i.id" :label="i.id">{{ i.name }}</el-checkbox></el-checkbox-group></el-form-item>
      <el-form-item><el-button type="primary" @click="run">执行检查</el-button></el-form-item>
    </el-form></el-card>
    <el-alert v-if="report" title="检查完成" type="success" :closable="false" show-icon/>
    <el-table :data="results" size="small" border><el-table-column prop="device_name" label="设备" width="120"/>
      <el-table-column prop="score" label="评分" width="60" align="center"/><el-table-column label="检查项"><template #default="{row}"><template v-if="row.report"><span v-for="(v,k) in row.report" :key="k" style="margin-right:6px"><el-tooltip :content="v.cmd"><el-tag :type="v.status==='pass'?'success':'danger'" size="small">{{ v.name }}</el-tag></el-tooltip></span></template></template></el-table-column>
      <el-table-column prop="created_at" label="时间" width="160"/></el-table>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
const items=ref<any[]>([]);const selected=ref<string[]>([]);const devId=ref('');const report=ref<any>(null);const results=ref<any[]>([])
async function load(){const[r1,r2]=await Promise.all([fetch('/api/switch-protect/items'),fetch('/api/switch-protect/results')]);items.value=await r1.json();results.value=await r2.json();items.value.forEach((i:any)=>selected.value.push(i.id))}
async function run(){const r=await fetch(`/api/switch-protect/check?device_id=${devId.value}&device_name=${devId.value}&checks=${selected.value.join(',')}`,{method:'POST'});report.value=await r.json();load()}
onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:1300px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

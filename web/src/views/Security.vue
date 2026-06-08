<template>
  <div class="page"><h2>🛡️ 安全基线</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="设备ID"><el-input v-model="devId" placeholder="设备ID" style="width:160px"/></el-form-item>
      <el-form-item><el-checkbox v-for="t in checks" :key="t.id" v-model="sel[t.id]" :label="t.id">{{ t.name }}</el-checkbox></el-form-item>
      <el-form-item><el-button type="primary" @click="run" :loading="loading">执行检查</el-button></el-form-item>
    </el-form></el-card>
    <el-alert v-if="report" :title="`评分: ${report.score} · 通过 ${report.passed}/10`" :type="report.score>=90?'success':report.score>=60?'warning':'error'" :closable="false" show-icon style="margin-bottom:12px"/>
    <el-table :data="reports" size="small" border v-loading="loadingList">
      <el-table-column prop="device_name" label="设备"/>
      <el-table-column label="通过"><template #default="{row}"><el-tag :type="row.passed>='7'?'success':'warning'" size="small">{{ row.passed }}</el-tag></template></el-table-column>
      <el-table-column label="详情"><template #default="{row}"><span v-for="(v,k) in (row.checks||{})" :key="k" style="margin-right:6px"><el-tag :type="v==='pass'?'success':'danger'" size="small">{{ k }}</el-tag></span></template></el-table-column>
      <el-table-column prop="created_at" label="时间" width="160"/></el-table>
    <el-empty v-if="!loadingList && !reports.length" description="暂无安全检查报告"/>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRequest } from '@/composables/useRequest'
const { loading, get, post } = useRequest()
const loadingList = ref(false); const devId = ref(''); const checks = ref<any[]>([]); const sel = reactive<Record<string,boolean>>({}); const report = ref<any>(null); const reports = ref<any[]>([])
async function load() { loadingList.value = true; try { const c = await get<any[]>('/api/security/checks'); if (c) { checks.value = c; c.forEach((t: any) => sel[t.id] = true) } const list = await get<any[]>('/api/security/reports'); if (list) reports.value = list.reverse() } finally { loadingList.value = false } }
async function run() { if (!devId.value) { ElMessage.warning('请输入设备ID'); return } const ids = Object.entries(sel).filter(([,v])=>v).map(([k])=>k).join(','); if (!ids) { ElMessage.warning('请勾选检查项'); return } const data = await post<any>(`/api/security/run?devId=${devId.value}&checks=${ids}`, undefined, { successMsg: '检查完成', errorMsg: '检查失败', timeout: 30 }); if (data) { report.value = data; load() } }
onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:1300px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

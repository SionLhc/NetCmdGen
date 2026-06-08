<template>
  <div class="page"><h2>⏰ 计划任务</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="名称"><el-input v-model="form.name" placeholder="任务名称" style="width:150px"/></el-form-item>
      <el-form-item label="类型"><el-select v-model="form.type" style="width:120px"><el-option v-for="o in types" :key="o" :label="o" :value="o"/></el-select></el-form-item>
      <el-form-item label="Cron"><el-input v-model="form.cron" placeholder="0 2 * * *" style="width:140px"/></el-form-item>
      <el-form-item><el-button type="primary" @click="create" :loading="loading">创建任务</el-button></el-form-item>
    </el-form></el-card>
    <el-table :data="list" size="small" border v-loading="loadingList">
      <el-table-column prop="name" label="名称"/><el-table-column prop="type" label="类型" width="90"/>
      <el-table-column prop="cron" label="Cron" width="120"/><el-table-column prop="status" label="状态" width="80" align="center">
        <template #default="{row}"><el-tag :type="row.enabled?'success':'info'" size="small">{{ row.enabled?'启用':'停用' }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="140"><template #default="{row}">
        <el-button size="small" @click="toggle(row)">{{ row.enabled?'停用':'启用' }}</el-button>
        <el-button size="small" type="danger" @click="del(row)">删除</el-button></template></el-table-column></el-table>
    <el-empty v-if="!loadingList && !list.length" description="暂无计划任务"/>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRequest } from '@/composables/useRequest'
const { loading, get, post } = useRequest()
const loadingList = ref(false); const list = ref<any[]>([]); const form = reactive({ name: '', type: 'backup', cron: '0 2 * * *' })
const types = ['backup', 'health', 'report', 'custom']
async function load() { loadingList.value = true; try { const data = await get<any[]>('/api/scheduler/tasks'); if (data) list.value = data } finally { loadingList.value = false } }
async function create() { if (!form.name) { ElMessage.warning('请输入任务名称'); return }; await post('/api/scheduler/tasks', form, { successMsg: '已创建', errorMsg: '创建失败' }); list.value = []; load() }
async function toggle(row: any) { await post(`/api/scheduler/tasks/${row.id}/toggle`); load() }
async function del(row: any) {
  try { await ElMessageBox.confirm('确定删除此任务？', '确认', { type: 'warning' }); await post(`/api/scheduler/tasks/${row.id}/delete`); load() }
  catch { /* 取消 */ }
}
onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:1300px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

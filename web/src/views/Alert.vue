<template>
  <div class="page"><h2>🔔 告警配置</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="名称"><el-input v-model="form.name" placeholder="告警名称" style="width:150px"/></el-form-item>
      <el-form-item label="类型"><el-select v-model="form.type" style="width:140px"><el-option v-for="o in types" :key="o" :label="o" :value="o"/></el-select></el-form-item>
      <el-form-item label="Webhook"><el-input v-model="form.webhook" placeholder="https://..." style="width:280px"/></el-form-item>
      <el-form-item><el-button type="primary" @click="create" :loading="loading">创建规则</el-button></el-form-item>
    </el-form></el-card>
    <el-table :data="list" size="small" border v-loading="loadingList">
      <el-table-column prop="name" label="名称"/><el-table-column prop="type" label="类型" width="100"/>
      <el-table-column prop="webhook" label="Webhook URL" min-width="200"/><el-table-column label="操作" width="160" align="center">
        <template #default="{row}"><el-button size="small" @click="test(row)" :loading="testing===row.id">测试</el-button>
        <el-button size="small" type="danger" @click="del(row)">删除</el-button></template></el-table-column></el-table>
    <el-empty v-if="!loadingList && !list.length" description="暂无告警规则"/>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRequest } from '@/composables/useRequest'
const { loading, get, post } = useRequest()
const loadingList = ref(false); const list = ref<any[]>([]); const testing = ref(''); const form = reactive({ name: '', type: 'wechat', webhook: '' })
const types = ['wechat', 'dingtalk', 'email']
async function load() { loadingList.value = true; try { const data = await get<any[]>('/api/alert/rules'); if (data) list.value = data } finally { loadingList.value = false } }
async function create() { if (!form.name) { ElMessage.warning('请输入规则名称'); return }; if (!form.webhook) { ElMessage.warning('请输入 Webhook URL'); return }; await post('/api/alert/rules', form, { successMsg: '已创建', errorMsg: '创建失败' }); load() }
async function test(row: any) { testing.value = row.id; const r = await fetch(`/api/alert/test/${row.id}`, { method: 'POST' }); if (r.ok) { const d = await r.json(); ElMessage[d.ok ? 'success' : 'error'](d.ok ? '测试发送成功' : '测试失败') } else ElMessage.error(`测试失败: ${r.status}`); testing.value = '' }
async function del(row: any) { try { await ElMessageBox.confirm('确定删除？', '确认', { type: 'warning' }); await post(`/api/alert/rules/${row.id}/delete`); load() } catch { /* 取消 */ } }
onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:1300px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

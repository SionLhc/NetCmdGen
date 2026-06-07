<template>
  <div class="page"><h2>⏰ 计划任务</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="名称"><el-input v-model="form.name" placeholder="每日备份"/></el-form-item>
      <el-form-item label="类型"><el-select v-model="form.type"><el-option v-for="t in types" :key="t.id" :label="t.name" :value="t.id"/></el-select></el-form-item>
      <el-form-item label="Cron"><el-input v-model="form.cron" placeholder="0 3 * * *" style="width:140px"/></el-form-item>
      <el-form-item><el-button type="primary" @click="create">创建任务</el-button></el-form-item>
    </el-form></el-card>
    <el-table :data="tasks" size="small" border><el-table-column prop="name" label="名称" width="140"/><el-table-column prop="task_type" label="类型" width="80"/><el-table-column prop="cron_expr" label="Cron" width="120"/>
      <el-table-column label="状态" width="60"><template #default="{row}"><el-tag :type="row.enabled?'success':'info'" size="small">{{ row.enabled?'启用':'停用' }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="140"><template #default="{row}"><el-button text size="small" @click="toggle(row)">{{ row.enabled?'停用':'启用' }}</el-button><el-button text size="small" type="danger" @click="del(row.id)">删除</el-button></template></el-table-column></el-table>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
const tasks=ref<any[]>([]); const types=[{id:'backup',name:'配置备份'},{id:'health',name:'网络巡检'},{id:'report',name:'报告导出'},{id:'custom',name:'自定义'}]
const form=ref({name:'',type:'backup',cron:'0 3 * * *'})
async function load(){const r=await fetch('/api/scheduler/tasks');tasks.value=await r.json()}
async function create(){const p=new URLSearchParams({name:form.value.name,task_type:form.value.type,cron_expr:form.value.cron});await fetch('/api/scheduler/tasks?'+p,{method:'POST'});form.value.name='';load()}
async function toggle(row:any){await fetch(`/api/scheduler/tasks/${row.id}/toggle`,{method:'PUT'});load()}
async function del(id:number){await fetch(`/api/scheduler/tasks/${id}`,{method:'DELETE'});load()}
onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:900px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

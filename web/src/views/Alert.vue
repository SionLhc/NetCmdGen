<template>
  <div class="page"><h2>🔔 告警配置</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="名称"><el-input v-model="form.name" placeholder="核心交换机离线告警"/></el-form-item>
      <el-form-item label="类型"><el-select v-model="form.type"><el-option v-for="t in types" :key="t.id" :label="t.name" :value="t.id"/></el-select></el-form-item>
      <el-form-item label="Webhook"><el-input v-model="form.url" placeholder="企业微信Webhook URL" style="width:300px"/></el-form-item>
      <el-form-item><el-button type="primary" @click="create">创建规则</el-button></el-form-item>
    </el-form></el-card>
    <el-table :data="rules" size="small" border><el-table-column prop="name" label="名称" width="140"/><el-table-column prop="alert_type" label="类型" width="100"/>
      <el-table-column prop="webhook_url" label="Webhook" min-width="200"><template #default="{row}">{{ row.webhook_url?.substring(0,50) || '—' }}</template></el-table-column>
      <el-table-column label="操作" width="140"><template #default="{row}"><el-button text size="small" @click="test(row.webhook_url)">测试</el-button><el-button text size="small" type="danger" @click="del(row.id)">删除</el-button></template></el-table-column></el-table>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'; import { ElMessage } from 'element-plus'
const rules=ref<any[]>([]); const types=[{id:'device_offline',name:'设备离线'},{id:'port_flap',name:'端口抖动'},{id:'traffic_spike',name:'流量异常'},{id:'cpu_high',name:'CPU过载'},{id:'config_change',name:'配置变更'}]
const form=ref({name:'',type:'device_offline',url:''})
async function load(){const r=await fetch('/api/alert/rules');rules.value=await r.json()}
async function create(){const p=new URLSearchParams({name:form.value.name,alert_type:form.value.type,webhook_url:form.value.url});await fetch('/api/alert/rules?'+p,{method:'POST'});form.value.name='';load()}
async function del(id:number){await fetch(`/api/alert/rules/${id}`,{method:'DELETE'});load()}
async function test(url:string){const r=await fetch(`/api/alert/test?webhook_url=${encodeURIComponent(url)}`);const d=await r.json();ElMessage[d.ok?'success':'error'](d.ok?'推送成功':d.error)}
onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:900px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

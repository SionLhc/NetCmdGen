<template>
  <div class="page"><h2>📋 SNMP 采集模板</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="名称"><el-input v-model="f.name" placeholder="cpuLoad"/></el-form-item>
      <el-form-item label="OID"><el-input v-model="f.oid" placeholder="1.3.6.1..." style="width:260px"/></el-form-item>
      <el-form-item label="单位"><el-input v-model="f.unit" placeholder="%" style="width:80px"/></el-form-item>
      <el-form-item><el-button type="primary" @click="add">添加 OID</el-button></el-form-item>
    </el-form></el-card>
    <el-table :data="tpls" size="small" border><el-table-column prop="name" label="名称" width="120"/>
      <el-table-column prop="oid" label="OID" min-width="300"/><el-table-column prop="description" label="描述" width="160"/>
      <el-table-column prop="unit" label="单位" width="80" align="center"/><el-table-column label="操作" width="60"><template #default="{row}"><el-button text size="small" type="danger" @click="del(row.id)">删除</el-button></template></el-table-column></el-table>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
const tpls=ref<any[]>([]);const f=ref({name:'',oid:'',unit:''})
async function load(){const r=await fetch('/api/snmp-template/templates');tpls.value=await r.json()}
async function add(){await fetch(`/api/snmp-template/templates?name=${encodeURIComponent(f.value.name)}&oid=${encodeURIComponent(f.value.oid)}&unit=${f.value.unit}`,{method:'POST'});f.value={name:'',oid:'',unit:''};load()}
async function del(id:number){await fetch(`/api/snmp-template/templates/${id}`,{method:'DELETE'});load()}
onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:900px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

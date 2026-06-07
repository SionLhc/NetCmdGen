<template>
  <div class="page"><h2>💾 配置备份</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="设备"><el-input v-model="deviceId" placeholder="设备ID" style="width:200px"/></el-form-item>
      <el-form-item label="名称"><el-input v-model="deviceName" placeholder="设备名称"/></el-form-item>
      <el-form-item label="配置"><el-input v-model="config" type="textarea" :rows="3" placeholder="粘贴show run配置"/></el-form-item>
      <el-form-item><el-button type="primary" @click="save">保存备份</el-button></el-form-item>
    </el-form></el-card>
    <el-table :data="backups" size="small" border><el-table-column prop="device_name" label="设备" width="140"/>
      <el-table-column prop="config_size" label="大小" width="80" align="right"><template #default="{row}">{{ (row.config_size/1024).toFixed(1) }}KB</template></el-table-column>
      <el-table-column prop="created_at" label="时间" width="160"/><el-table-column label="操作" width="100">
        <template #default="{row}"><el-button text size="small" @click="viewBackup(row.id)">查看</el-button></template></el-table-column></el-table>
    <el-dialog v-model="showDiff" title="配置差异" width="800px"><pre style="font-size:12px;max-height:500px;overflow:auto;background:#1e1e1e;color:#ccc;padding:12px;border-radius:6px">{{ diffText }}</pre></el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'; import { ElMessage } from 'element-plus'
const backups=ref<any[]>([]); const deviceId=ref(''); const deviceName=ref(''); const config=ref('')
const showDiff=ref(false); const diffText=ref('')
async function load(){const r=await fetch('/api/backup');backups.value=await r.json()}
async function save(){const p=new URLSearchParams({device_id:deviceId.value,device_name:deviceName.value,config:config.value});await fetch('/api/backup?'+p,{method:'POST'});config.value='';load();ElMessage.success('已保存')}
async function viewBackup(id:number){const r=await fetch('/api/backup/'+id);const d=await r.json();diffText.value=d.config||'(空)';showDiff.value=true}
onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:1300px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

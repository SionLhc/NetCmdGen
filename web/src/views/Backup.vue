<template>
  <div class="page"><h2>💾 配置备份</h2>
    <el-card style="margin-bottom:14px"><el-form :inline="true" size="default">
      <el-form-item label="设备IP"><el-input v-model="ip" placeholder="192.168.1.1" style="width:160px"/></el-form-item>
      <el-form-item label="设备名"><el-input v-model="name" placeholder="Core-R1" style="width:160px"/></el-form-item>
      <el-form-item><el-button type="primary" @click="save" :loading="loading">保存配置</el-button></el-form-item>
    </el-form></el-card>
    <el-table :data="list" size="small" border v-loading="loadingList">
      <el-table-column prop="device_name" label="设备" width="120"/>
      <el-table-column label="配置预览"><template #default="{row}"><code style="font-size:11px;max-width:720px;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ row.content?.slice(0,80) || '(空)' }}</code></template></el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{row}"><el-button size="small" @click="view(row)">查看</el-button></template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="160"/></el-table>
    <el-empty v-if="!loadingList && !list.length" description="暂无备份记录"/>
    <el-dialog v-model="showView" title="配置内容" width="700px"><pre style="max-height:500px;overflow:auto;font-size:12px;background:#f5f7fa;padding:14px;border-radius:8px;white-space:pre-wrap">{{ viewing?.content }}</pre></el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRequest } from '@/composables/useRequest'
const { loading, get, post } = useRequest()
const loadingList = ref(false); const ip = ref(''); const name = ref(''); const list = ref<any[]>([]); const viewing = ref<any>(null); const showView = ref(false)
async function load() { loadingList.value = true; try { const data = await get<any[]>('/api/backup'); if (data) list.value = data.reverse() } finally { loadingList.value = false } }
async function save() { if (!ip.value) { ElMessage.warning('请输入设备 IP'); return }; await post('/api/backup', { device_id: ip.value, device_name: name.value || ip.value, content: '' }, { successMsg: '已保存', errorMsg: '保存失败' }); load() }
function view(row: any) { viewing.value = row; showView.value = true }
onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:1300px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

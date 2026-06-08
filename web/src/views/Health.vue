<template>
  <div class="page">
    <h2>🔍 网络巡检</h2>

    <!-- 巡检表单 -->
    <el-card style="margin-bottom:14px">
      <el-form :inline="true" size="default">
        <el-form-item label="设备IP">
          <el-input v-model="devIp" placeholder="192.168.1.1" style="width:160px"/>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="username" placeholder="admin" style="width:120px"/>
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" placeholder="密码" style="width:120px"/>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-for="t in templates" :key="t.id" v-model="selected[t.id]" :label="t.id">{{ t.name }}</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="run" :loading="loading">执行巡检</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 巡检结果 -->
    <el-alert v-if="result" :title="resultMsg" :type="resultLevel" :closable="false" show-icon style="margin-bottom:12px"/>

    <!-- 历史报告 -->
    <el-table :data="reports" size="small" border v-loading="loadingList">
      <el-table-column prop="device_name" label="设备" width="130"/>
      <el-table-column prop="score" label="得分" width="60" align="center">
        <template #default="{row}">
          <el-tag :type="row.score>=90?'success':row.score>=60?'warning':'danger'" size="small">{{ row.score }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="巡检项">
        <template #default="{row}">
          <span v-for="(v,k) in getCheckItems(row)" :key="k" style="margin-right:6px">
            <el-tag :type="v.level==='normal'?'success':v.level==='warning'?'warning':'danger'" size="small">
              {{ v.item_name }}
            </el-tag>
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="160"/>
    </el-table>
    <el-empty v-if="!loadingList && !reports.length" description="暂无巡检报告，请执行一次巡检"/>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRequest } from '@/composables/useRequest'

const { loading, get, post } = useRequest()
const loadingList = ref(false)
const templates = ref<any[]>([])
const selected = reactive<Record<string, boolean>>({})
const reports = ref<any[]>([])
const devIp = ref('')
const username = ref('admin')
const password = ref('')
const result = ref<any>(null)

async function load() {
  loadingList.value = true
  try {
    const data = await get<any[]>(`/api/health/templates?t=${Date.now()}`)
    if (data) {
      templates.value = data
      // 默认勾选常用项
      data.forEach((t: any) => { selected[t.id] = true })
    }
    const list = await get<any[]>(`/api/health/reports?t=${Date.now()}`)
    if (list) reports.value = list.reverse()
  } finally { loadingList.value = false }
}

async function run() {
  if (!devIp.value) { ElMessage.warning('请输入设备 IP'); return }
  if (!username.value) { ElMessage.warning('请输入用户名'); return }
  const checks = Object.entries(selected).filter(([, v]) => v).map(([k]) => k).join(',')
  if (!checks) { ElMessage.warning('请勾选至少一个巡检项'); return }

  const data = await post<any>(
    `/api/health/run?device_id=manual&device_name=${devIp.value}&device_ip=${devIp.value}&username=${username.value}&password=${password.value}&checks=${checks}`,
    undefined, { successMsg: '巡检完成', errorMsg: '巡检失败', timeout: 60 }
  )
  if (data) {
    result.value = data
    resultMsg.value = `得分 ${data.score} · 通过 ${data.passed || 0} · 警告 ${data.warning || 0} · 失败 ${data.failed || 0}`
    resultLevel.value = data.score >= 90 ? 'success' : data.score >= 60 ? 'warning' : 'error'
    load()
  }
}

const resultMsg = ref('')
const resultLevel = ref<'success' | 'warning' | 'error'>('success')

function getCheckItems(row: any): any[] {
  if (!row.report) return []
  // report.checks 是巡检结果数组 {item_name, level, message, source, ...}
  if (row.report.checks) return row.report.checks
  if (typeof row.report === 'object') {
    return Object.values(row.report).filter((v: any) => v?.item_name || v?.name)
  }
  return []
}

onMounted(load)
</script>
<style scoped>.page{padding:24px;max-width:1300px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}</style>

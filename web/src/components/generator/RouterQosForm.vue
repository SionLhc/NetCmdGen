<template>
  <el-form label-width="120px" size="default">
    <el-form-item label="启用流控">
      <el-switch v-model="form.enable_qos" active-text="开启" inactive-text="关闭" />
      <span style="font-size:12px;color:#909399;margin-left:8px">限制每台设备带宽，防止个别用户占满</span>
    </el-form-item>

    <template v-if="form.enable_qos">
      <el-divider content-position="left">总带宽设置</el-divider>
      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="上行带宽">
            <el-input-number v-model="form.total_upload" :min="1" :max="10000" size="default" style="width:140px" />
            <span style="margin-left:4px">Mbps</span>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="下行带宽">
            <el-input-number v-model="form.total_download" :min="1" :max="10000" size="default" style="width:140px" />
            <span style="margin-left:4px">Mbps</span>
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">每IP限速</el-divider>
      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="每IP上行">
            <el-input-number v-model="form.per_ip_upload" :min="1" :max="1000" size="default" style="width:140px" />
            <span style="margin-left:4px">Mbps</span>
            <span style="font-size:12px;color:#909399;margin-left:8px">建议 10-50</span>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="每IP下行">
            <el-input-number v-model="form.per_ip_download" :min="1" :max="1000" size="default" style="width:140px" />
            <span style="margin-left:4px">Mbps</span>
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">应用优先级（保证关键业务不卡顿）</el-divider>
      <div v-for="(p,i) in form.priorities" :key="i" style="display:flex;gap:8px;align-items:center;margin-bottom:6px">
        <el-select v-model="p.level" size="default" style="width:130px">
          <el-option label="🔴 高优先级" value="high" />
          <el-option label="🟡 中优先级" value="medium" />
          <el-option label="🟢 低优先级" value="low" />
        </el-select>
        <el-input v-model="p.name" placeholder="应用名（如 视频会议）" size="default" style="width:200px" />
        <el-button link type="danger" size="small" @click="form.priorities.splice(i,1)" v-if="form.priorities.length>1">✕</el-button>
      </div>
      <el-button size="small" @click="form.priorities.push({level:'medium',name:''})">+ 添加优先级</el-button>
    </template>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string,any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string,any>] }>()

const form = reactive({
  enable_qos: props.modelValue?.enable_qos ?? false,
  total_upload: props.modelValue?.total_upload ?? 100,
  total_download: props.modelValue?.total_download ?? 200,
  per_ip_upload: props.modelValue?.per_ip_upload ?? 10,
  per_ip_download: props.modelValue?.per_ip_download ?? 20,
  priorities: props.modelValue?.priorities || [
    { level: 'high', name: '视频会议/Zoom' },
    { level: 'medium', name: '网页浏览' },
    { level: 'low', name: 'P2P下载' },
  ],
})

watch(() => form, () => emit('update:modelValue', { ...form }), { deep: true })
</script>

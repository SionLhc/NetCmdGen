<template>
  <div class="router-form-panel">
    <div class="panel-switch">
      <el-switch v-model="form.enable_qos" active-text="启用流控限速" size="default" />
      <span class="panel-switch-hint">限制每台设备带宽，防止个别人占满全部带宽</span>
    </div>

    <template v-if="form.enable_qos">
      <!-- 总带宽 -->
      <div class="panel-section">
        <div class="section-title">📊 总带宽上限</div>
        <div class="section-hint">设置整条线路的总带宽（一般填入运营商套餐值）</div>
        <div class="config-card">
          <div class="card-grid card-grid-2">
            <div class="field-group">
              <label class="field-label">上行带宽（上传）</label>
              <div class="field-input-row">
                <el-input-number v-model="form.total_upload" :min="1" :max="10000" size="default" style="flex:1" />
                <span class="field-unit">Mbps</span>
              </div>
              <span class="field-extra">运营商上行通常较小，如 100Mbps</span>
            </div>
            <div class="field-group">
              <label class="field-label">下行带宽（下载）</label>
              <div class="field-input-row">
                <el-input-number v-model="form.total_download" :min="1" :max="10000" size="default" style="flex:1" />
                <span class="field-unit">Mbps</span>
              </div>
              <span class="field-extra">运营商下行通常较大，如 500Mbps</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 每IP限速 -->
      <div class="panel-section">
        <div class="section-title">👤 每台设备限速</div>
        <div class="section-hint">单台设备最多占用多少带宽，保证大家公平使用</div>
        <div class="config-card">
          <div class="card-grid card-grid-2">
            <div class="field-group">
              <label class="field-label">每 IP 上行（上传）</label>
              <div class="field-input-row">
                <el-input-number v-model="form.per_ip_upload" :min="1" :max="1000" size="default" style="flex:1" />
                <span class="field-unit">Mbps</span>
              </div>
              <span class="field-extra">建议 10-30 Mbps，防止 P2P 上传占满</span>
            </div>
            <div class="field-group">
              <label class="field-label">每 IP 下行（下载）</label>
              <div class="field-input-row">
                <el-input-number v-model="form.per_ip_download" :min="1" :max="1000" size="default" style="flex:1" />
                <span class="field-unit">Mbps</span>
              </div>
              <span class="field-extra">建议 20-50 Mbps，保证流畅上网</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 应用优先级 -->
      <div class="panel-section">
        <div class="section-title">🎯 应用优先级</div>
        <div class="section-hint">高优先级应用优先保证带宽，网络拥塞时关键业务不卡顿</div>

        <div class="priority-list">
          <div v-for="(p, i) in form.priorities" :key="'pri'+i" class="priority-row">
            <div class="priority-indicator" :class="p.level === 'high' ? 'pri-high' : p.level === 'medium' ? 'pri-medium' : 'pri-low'"></div>
            <el-select v-model="p.level" size="default" class="priority-level">
              <el-option label="🔴 高 — 保证带宽优先" value="high" />
              <el-option label="🟡 中 — 尽力转发" value="medium" />
              <el-option label="🟢 低 — 网络空闲时使用" value="low" />
            </el-select>
            <el-input v-model="p.name" size="default" placeholder="应用名称（如 视频会议/Zoom）" class="priority-name" />
            <el-button link type="danger" size="small" @click="form.priorities.splice(i, 1)" v-if="form.priorities.length > 1" class="priority-del">删除</el-button>
          </div>
        </div>
        <el-button size="default" type="primary" plain class="add-btn" @click="form.priorities.push({ level: 'medium', name: '' })">+ 添加优先级</el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

const form = reactive({
  enable_qos: props.modelValue?.enable_qos ?? false,
  total_upload: props.modelValue?.total_upload ?? 100,
  total_download: props.modelValue?.total_download ?? 500,
  per_ip_upload: props.modelValue?.per_ip_upload ?? 20,
  per_ip_download: props.modelValue?.per_ip_download ?? 50,
  priorities: (props.modelValue?.priorities?.length ? props.modelValue.priorities : [
    { level: 'high', name: '视频会议 / VoIP' },
    { level: 'medium', name: '网页浏览' },
    { level: 'low', name: 'P2P 下载 / 更新' },
  ]) as { level: string; name: string }[],
})

watch(() => form, () => emit('update:modelValue', { ...form }), { deep: true })
</script>

<style scoped>
.router-form-panel { max-width: 840px; }
.panel-switch { display: flex; align-items: center; padding: 10px 14px; background: #f5f7fa; border-radius: 8px; margin-bottom: 14px; }
.panel-switch-hint { font-size: 12px; color: #909399; margin-left: 12px; }
.panel-section { margin-bottom: 18px; }
.section-title { font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.section-hint { font-size: 11px; color: #909399; margin-bottom: 12px; }

.config-card { border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; background: #fff; }
.card-grid { display: grid; gap: 14px; }
.card-grid-2 { grid-template-columns: 1fr 1fr; }
.field-group { display: flex; flex-direction: column; }
.field-label { font-size: 11px; color: #606266; margin-bottom: 4px; font-weight: 500; }
.field-input-row { display: flex; align-items: center; gap: 6px; }
.field-unit { font-size: 12px; color: #909399; flex-shrink: 0; min-width: 36px; }
.field-extra { font-size: 10px; color: #c0c4cc; margin-top: 4px; }

/* 优先级列表 */
.priority-list { margin-bottom: 10px; }
.priority-row { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border: 1px solid #e4e7ed; border-radius: 6px; margin-bottom: 8px; background: #fff; }
.priority-row:hover { border-color: #c0c4cc; }
.priority-indicator { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.pri-high { background: #f56c6c; box-shadow: 0 0 4px rgba(245, 108, 108, 0.5); }
.pri-medium { background: #e6a23c; box-shadow: 0 0 4px rgba(230, 162, 60, 0.5); }
.pri-low { background: #67c23a; box-shadow: 0 0 4px rgba(103, 194, 58, 0.5); }
.priority-level { width: 180px; flex-shrink: 0; }
.priority-name { flex: 1; }
.priority-del { flex-shrink: 0; }

.add-btn { width: 100%; margin-top: 4px; }
</style>

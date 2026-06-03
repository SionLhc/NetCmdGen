<template>
  <div class="router-form-panel">
    <div class="panel-switch">
      <el-switch v-model="form.enable_dhcp" active-text="启用 DHCP 服务" size="default" />
      <span class="panel-switch-hint">自动给内网设备分配IP地址</span>
    </div>

    <template v-if="form.enable_dhcp">
      <!-- 地址池 -->
      <div class="panel-section">
        <div class="section-title">📦 地址池配置</div>
        <div class="section-hint">定义分配给内网设备的 IP 范围</div>

        <div class="config-card">
          <div class="card-grid card-grid-3">
            <div class="field-group">
              <label class="field-label">网络地址</label>
              <el-input v-model="form.network" size="default" placeholder="192.168.1.0" />
            </div>
            <div class="field-group">
              <label class="field-label">掩码位数</label>
              <el-input-number v-model="form.mask_len" :min="8" :max="30" size="default" style="width:100%" />
              <span class="field-extra">常用 24 = 255.255.255.0</span>
            </div>
            <div class="field-group">
              <label class="field-label">网关地址</label>
              <el-input v-model="form.gateway" size="default" placeholder="192.168.1.1" />
              <span class="field-extra">通常是路由器 LAN 口 IP</span>
            </div>
          </div>

          <div class="card-grid card-grid-3">
            <div class="field-group">
              <label class="field-label">首选 DNS</label>
              <el-input v-model="form.dns1" size="default" placeholder="223.5.5.5（阿里）" />
            </div>
            <div class="field-group">
              <label class="field-label">备用 DNS</label>
              <el-input v-model="form.dns2" size="default" placeholder="114.114.114.114" />
            </div>
            <div class="field-group">
              <label class="field-label">租约时间</label>
              <el-select v-model="form.lease" size="default" style="width:100%">
                <el-option label="1 天" value="day 0 hour 1" />
                <el-option label="3 天" value="day 3 hour 0" />
                <el-option label="7 天" value="day 7 hour 0" />
                <el-option label="30 天" value="day 30 hour 0" />
              </el-select>
            </div>
          </div>
        </div>
      </div>

      <!-- 排除地址 -->
      <div class="panel-section">
        <div class="section-title">🚫 排除地址（保留给服务器/打印机等固定IP设备）</div>
        <div class="section-hint">这些 IP 不会分配给普通客户端，避免 IP 冲突</div>

        <div class="exclude-list">
          <div v-for="(item, i) in form.excluded" :key="'ex'+i" class="exclude-row">
            <el-input v-model="item.start" size="default" placeholder="起始 IP" class="exclude-ip" />
            <span class="exclude-arrow">→</span>
            <el-input v-model="item.end" size="default" placeholder="结束 IP（单IP可相同）" class="exclude-ip" />
            <el-button link type="danger" @click="form.excluded.splice(i, 1)" :disabled="form.excluded.length <= 1" class="exclude-del">删除</el-button>
          </div>
        </div>
        <el-button size="default" type="primary" plain class="add-btn" @click="form.excluded.push({ start: '', end: '' })">+ 添加排除范围</el-button>
      </div>

      <!-- 高级选项 -->
      <div class="panel-section">
        <div class="section-title">⚙ 高级选项</div>
        <div class="config-card">
          <div class="card-grid card-grid-2">
            <div class="field-group">
              <label class="field-label">本地域名（可选）</label>
              <el-input v-model="form.domain" size="default" placeholder="company.local" />
              <span class="field-extra">内网设备可通过域名访问，如 nas.company.local</span>
            </div>
            <div class="field-group">
              <label class="field-label">NTP 时间服务器（可选）</label>
              <el-input v-model="form.ntp_server" size="default" placeholder="192.168.1.1" />
              <span class="field-extra">使用路由器做 NTP，保证设备时间同步</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

const form = reactive({
  enable_dhcp: props.modelValue?.enable_dhcp ?? true,
  network: props.modelValue?.network || '192.168.1.0',
  mask_len: props.modelValue?.mask_len ?? 24,
  gateway: props.modelValue?.gateway || '192.168.1.1',
  dns1: props.modelValue?.dns1 || '223.5.5.5',
  dns2: props.modelValue?.dns2 || '114.114.114.114',
  lease: props.modelValue?.lease || 'day 0 hour 1',
  domain: props.modelValue?.domain || '',
  ntp_server: props.modelValue?.ntp_server || '',
  excluded: (props.modelValue?.excluded?.length ? props.modelValue.excluded : [{ start: '192.168.1.10', end: '192.168.1.50' }]) as { start: string; end: string }[],
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
.card-grid { display: grid; gap: 14px; margin-bottom: 0; }
.card-grid-2 { grid-template-columns: 1fr 1fr; }
.card-grid-3 { grid-template-columns: 1fr 1fr 1fr; }
.card-grid + .card-grid { margin-top: 14px; padding-top: 14px; border-top: 1px dashed #ebeef5; }
.field-group { display: flex; flex-direction: column; }
.field-label { font-size: 11px; color: #606266; margin-bottom: 4px; font-weight: 500; }
.field-extra { font-size: 10px; color: #c0c4cc; margin-top: 2px; }

.exclude-list { margin-bottom: 10px; }
.exclude-row { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border: 1px solid #e4e7ed; border-radius: 6px; margin-bottom: 8px; background: #fff; }
.exclude-row:hover { border-color: #c0c4cc; }
.exclude-ip { flex: 1; }
.exclude-arrow { font-size: 14px; color: #909399; font-weight: 700; flex-shrink: 0; }
.exclude-del { flex-shrink: 0; }

.add-btn { width: 100%; margin-top: 4px; }
</style>

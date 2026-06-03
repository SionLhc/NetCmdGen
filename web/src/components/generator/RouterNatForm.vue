<template>
  <div class="router-form-panel">
    <!-- 开关行 -->
    <div class="panel-switch">
      <el-switch v-model="form.enable_nat" active-text="启用 NAT" size="default" />
      <span class="panel-switch-hint">让内网设备访问互联网（源NAT自动开启）</span>
    </div>

    <template v-if="form.enable_nat">
      <div class="panel-section">
        <div class="section-title">🔗 端口映射（DNAT — 把内网服务暴露到公网）</div>
        <div class="section-hint">多公网IP时必须指定IP；单公网IP留空即可</div>

        <div v-for="(m, i) in form.mappings" :key="'nat'+i" class="mapping-card">
          <div class="card-header">
            <div class="card-header-left">
              <span class="card-tag" :class="m.protocol==='tcp'?'tag-tcp':m.protocol==='udp'?'tag-udp':'tag-both'">
                {{ m.protocol === 'tcp' ? 'TCP' : m.protocol === 'udp' ? 'UDP' : 'TCP+UDP' }}
              </span>
              <span class="card-index">映射 #{{ i + 1 }}</span>
              <span v-if="m.desc" class="card-desc">— {{ m.desc }}</span>
            </div>
            <el-button link type="danger" size="small" @click="removeMapping(i)" v-if="form.mappings.length > 1">删除</el-button>
          </div>

          <!-- 第一行：描述 + 协议 -->
          <div class="card-grid card-grid-2">
            <div class="field-group">
              <label class="field-label">描述</label>
              <el-input v-model="m.desc" size="default" placeholder="如：公司官网 HTTPS" />
            </div>
            <div class="field-group">
              <label class="field-label">协议</label>
              <el-select v-model="m.protocol" size="default" style="width:100%">
                <el-option label="TCP（网页/SSH/邮件等）" value="tcp" />
                <el-option label="UDP（DNS/VPN/游戏等）" value="udp" />
                <el-option label="TCP + UDP" value="both" />
              </el-select>
            </div>
          </div>

          <!-- 第二行：公网IP + 公网端口 + 内网IP -->
          <div class="card-grid card-grid-3">
            <div class="field-group">
              <label class="field-label">公网 IP</label>
              <el-input v-model="m.public_ip" size="default" placeholder="留空 = 接口 IP" />
            </div>
            <div class="field-group">
              <label class="field-label">公网端口</label>
              <el-input-number v-model="m.external_port" :min="1" :max="65535" size="default" style="width:100%" />
            </div>
            <div class="field-group">
              <label class="field-label">映射到内网地址</label>
              <el-input v-model="m.internal_ip" size="default" placeholder="192.168.1.100" />
            </div>
          </div>

          <!-- 第三行：内网端口 -->
          <div class="card-grid card-grid-3">
            <div class="field-group">
              <label class="field-label">内网端口</label>
              <el-input-number v-model="m.internal_port" :min="1" :max="65535" size="default" style="width:100%" />
              <span class="field-extra">不填=与公网端口相同</span>
            </div>
            <div class="field-placeholder"></div>
            <div class="field-placeholder"></div>
          </div>

          <!-- 实时命令预览 -->
          <div class="cmd-preview">{{ dnatPreview(i) }}</div>
        </div>

        <el-button size="default" type="primary" plain class="add-btn" @click="addMapping">+ 添加端口映射</el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

const form = reactive({
  enable_nat: props.modelValue?.enable_nat ?? true,
  mappings: (props.modelValue?.mappings?.length ? props.modelValue.mappings : [
    { desc: '', protocol: 'tcp', public_ip: '', external_port: 443, internal_ip: '192.168.1.10', internal_port: 443 },
  ]) as { desc: string; protocol: string; public_ip: string; external_port: number; internal_ip: string; internal_port: number }[],
})

function dnatPreview(i: number) {
  const m = form.mappings[i]; if (!m) return ''
  const ip = m.public_ip || '{公网IP}'
  const proto = m.protocol === 'both' ? 'tcp' : m.protocol
  return `→ /ip firewall nat add chain=dstnat dst-address=${ip}  protocol=${proto}  dst-port=${m.external_port}  action=dst-nat  to-addresses=${m.internal_ip || '{内网IP}'}  to-ports=${m.internal_port || m.external_port}`
}

function addMapping() {
  form.mappings.push({ desc: '', protocol: 'tcp', public_ip: '', external_port: 80, internal_ip: '', internal_port: 80 })
}
function removeMapping(i: number) { form.mappings.splice(i, 1) }

watch(() => form, () => emit('update:modelValue', { ...form }), { deep: true })
</script>

<style scoped>
.router-form-panel { max-width: 840px; }
.panel-switch { display: flex; align-items: center; padding: 10px 14px; background: #f5f7fa; border-radius: 8px; margin-bottom: 14px; }
.panel-switch-hint { font-size: 12px; color: #909399; margin-left: 12px; }
.panel-section { margin-bottom: 8px; }
.section-title { font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.section-hint { font-size: 11px; color: #909399; margin-bottom: 14px; }

.mapping-card { border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; margin-bottom: 14px; background: #fff; }
.mapping-card:hover { border-color: #c0c4cc; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px dashed #ebeef5; }
.card-header-left { display: flex; align-items: center; gap: 8px; }
.card-tag { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 600; color: #fff; }
.tag-tcp { background: #409eff; }
.tag-udp { background: #e6a23c; }
.tag-both { background: #67c23a; }
.card-index { font-weight: 600; font-size: 13px; color: #303133; }
.card-desc { font-size: 12px; color: #909399; }

.card-grid { display: grid; gap: 14px; margin-bottom: 14px; }
.card-grid-2 { grid-template-columns: 1fr 1fr; }
.card-grid-3 { grid-template-columns: 1fr 1fr 1fr; }
.field-group { display: flex; flex-direction: column; }
.field-label { font-size: 11px; color: #606266; margin-bottom: 4px; font-weight: 500; }
.field-extra { font-size: 10px; color: #c0c4cc; margin-top: 2px; }
.field-placeholder { min-height: 0; }

.cmd-preview { margin-top: 10px; padding: 8px 12px; background: #1e1e1e; color: #a6e22e; font-family: Consolas, monospace; font-size: 11px; border-radius: 4px; white-space: pre-wrap; word-break: break-all; }
.add-btn { width: 100%; margin-top: 4px; }
</style>

<template>
  <div class="router-form-panel">
    <div class="panel-switch">
      <span class="section-title" style="margin:0">🛡 访问控制列表（ACL）</span>
      <span class="panel-switch-hint">定义哪些设备/网段可以或不可以上网，规则从上到下匹配</span>
    </div>

    <div v-for="(r, i) in form.rules" :key="'acl'+i" class="rule-card">
      <!-- 规则头部 -->
      <div class="card-header">
        <div class="card-header-left">
          <span class="card-tag" :class="r.action === 'deny' ? 'tag-deny' : 'tag-permit'">
            {{ r.action === 'deny' ? '🚫 禁止' : '✅ 允许' }}
          </span>
          <span class="card-index">规则 #{{ i + 1 }}</span>
          <span v-if="r.desc" class="card-desc">— {{ r.desc }}</span>
        </div>
        <el-button link type="danger" size="small" @click="form.rules.splice(i, 1)" v-if="form.rules.length > 1">删除</el-button>
      </div>

      <!-- 第一行：动作 + 协议 + 端口 -->
      <div class="card-grid card-grid-3">
        <div class="field-group">
          <label class="field-label">动作</label>
          <el-select v-model="r.action" size="default" style="width:100%">
            <el-option label="✅ 允许 (permit)" value="permit" />
            <el-option label="🚫 禁止 (deny)" value="deny" />
          </el-select>
        </div>
        <div class="field-group">
          <label class="field-label">协议</label>
          <el-select v-model="r.protocol" size="default" style="width:100%">
            <el-option label="所有协议" value="ip" />
            <el-option label="TCP（网页/SSH等）" value="tcp" />
            <el-option label="UDP（DNS/游戏等）" value="udp" />
            <el-option label="ICMP（Ping）" value="icmp" />
          </el-select>
        </div>
        <div class="field-group">
          <label class="field-label">目的端口</label>
          <el-input v-model="r.dst_port" size="default" placeholder="留空 = 所有端口" />
          <span class="field-extra">多个用逗号分隔，如 80,443</span>
        </div>
      </div>

      <!-- 第二行：源地址 + 目的地址 -->
      <div class="card-grid card-grid-2">
        <div class="field-group">
          <label class="field-label">源地址（谁发起的）</label>
          <el-input v-model="r.src_ip" size="default" placeholder="192.168.1.0/24" />
          <span class="field-extra">单个IP、网段或留空=所有源</span>
        </div>
        <div class="field-group">
          <label class="field-label">目的地址（访问谁）</label>
          <el-input v-model="r.dst_ip" size="default" placeholder="留空 = 任意地址" />
          <span class="field-extra">限制访问特定目标，如 8.8.8.8</span>
        </div>
      </div>

      <!-- 第三行：描述 -->
      <div class="field-group" style="margin-top:2px">
        <label class="field-label">备注描述</label>
        <el-input v-model="r.desc" size="default" placeholder="如：禁止财务部访问外网" />
      </div>

      <!-- 实时命令预览 -->
      <div class="cmd-preview">{{ aclPreview(i) }}</div>
    </div>

    <el-button size="default" type="primary" plain class="add-btn" @click="form.rules.push({ action: 'deny', protocol: 'ip', src_ip: '', dst_ip: '', dst_port: '', desc: '' })">+ 添加规则</el-button>
    <div v-if="form.rules.length > 0" class="footer-hint">ℹ 规则从上到下匹配，末尾自动隐含<strong> 禁止所有 </strong>（deny all）</div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

const form = reactive({
  rules: (props.modelValue?.rules?.length ? props.modelValue.rules : [
    { action: 'permit', protocol: 'tcp', src_ip: '192.168.1.0/24', dst_ip: '', dst_port: '80,443', desc: '允许内网浏览网页' },
  ]) as { action: string; protocol: string; src_ip: string; dst_ip: string; dst_port: string; desc: string }[],
})

function aclPreview(i: number) {
  const r = form.rules[i]; if (!r) return ''
  const action = r.action === 'permit' ? 'accept' : 'drop'
  const src = r.src_ip || '0.0.0.0/0'
  let line = `→ /ip firewall filter add chain=forward  src-address=${src}`
  if (r.dst_ip) line += `  dst-address=${r.dst_ip}`
  if (r.protocol !== 'ip') line += `  protocol=${r.protocol}`
  if (r.dst_port && r.protocol !== 'ip') line += `  dst-port=${r.dst_port}`
  line += `  action=${action}`
  if (r.desc) line += `  comment="${r.desc}"`
  return line
}

watch(() => form, () => emit('update:modelValue', { ...form }), { deep: true })
</script>

<style scoped>
.router-form-panel { max-width: 840px; }
.panel-switch { display: flex; align-items: center; padding: 10px 14px; background: #f5f7fa; border-radius: 8px; margin-bottom: 14px; }
.panel-switch-hint { font-size: 12px; color: #909399; margin-left: 12px; }
.section-title { font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 4px; }

.rule-card { border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; margin-bottom: 14px; background: #fff; }
.rule-card:hover { border-color: #c0c4cc; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px dashed #ebeef5; }
.card-header-left { display: flex; align-items: center; gap: 8px; }
.card-tag { display: inline-block; padding: 2px 10px; border-radius: 3px; font-size: 11px; font-weight: 600; color: #fff; }
.tag-permit { background: #67c23a; }
.tag-deny { background: #f56c6c; }
.card-index { font-weight: 600; font-size: 13px; color: #303133; }
.card-desc { font-size: 12px; color: #909399; }

.card-grid { display: grid; gap: 14px; margin-bottom: 14px; }
.card-grid-2 { grid-template-columns: 1fr 1fr; }
.card-grid-3 { grid-template-columns: 1fr 1fr 1fr; }
.field-group { display: flex; flex-direction: column; }
.field-label { font-size: 11px; color: #606266; margin-bottom: 4px; font-weight: 500; }
.field-extra { font-size: 10px; color: #c0c4cc; margin-top: 2px; }

.cmd-preview { margin-top: 12px; padding: 8px 12px; background: #1e1e1e; color: #a6e22e; font-family: Consolas, monospace; font-size: 11px; border-radius: 4px; white-space: pre-wrap; word-break: break-all; }
.add-btn { width: 100%; margin-top: 4px; }
.footer-hint { font-size: 11px; color: #909399; margin-top: 10px; text-align: center; }
</style>

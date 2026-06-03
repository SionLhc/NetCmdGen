<template>
  <el-form label-width="130px" size="small">
    <!-- 总带宽 -->
    <el-divider content-position="left">
      <span style="color:#303133;font-weight:600">📊 总带宽</span>
      <span style="font-size:11px;color:#909399">&nbsp;请如实填写运营商给的带宽</span>
    </el-divider>
    <el-form-item label="下载带宽">
      <el-input v-model="form.total_bandwidth_down" style="width:180px" placeholder="100M">
        <template #append>Mbps</template>
      </el-input>
      <span style="font-size:11px;color:#909399;margin-left:8px">运营商套餐的下行速率</span>
    </el-form-item>
    <el-form-item label="上传带宽">
      <el-input v-model="form.total_bandwidth_up" style="width:180px" placeholder="20M">
        <template #append>Mbps</template>
      </el-input>
      <span style="font-size:11px;color:#909399;margin-left:8px">一般下行1/5~1/10</span>
    </el-form-item>

    <!-- 应用优先级 -->
    <el-divider content-position="left">
      <span style="color:#303133;font-weight:600">🎯 应用优先级</span>
      <span style="font-size:11px;color:#909399">&nbsp;勾选需要优先保障的应用（数字越小越优先）</span>
    </el-divider>

    <el-form-item label="VOIP语音电话" style="margin-bottom:6px">
      <el-switch v-model="form.app_priorities.voip" active-text="优先（级别1）保障通话质量" />
      <span style="font-size:11px;color:#909399;margin-left:10px">SIP/RTP，默认开启</span>
    </el-form-item>

    <el-form-item label="网页浏览" style="margin-bottom:6px">
      <el-switch v-model="form.app_priorities.http" active-text="优先（级别4）办公必需" inactive-text="不区分" />
      <span style="font-size:11px;color:#909399;margin-left:10px">HTTP/HTTPS，保障网页不卡</span>
    </el-form-item>

    <el-form-item label="视频会议" style="margin-bottom:6px">
      <el-switch v-model="form.app_priorities.video" active-text="优先（级别3）不卡顿" inactive-text="不区分" />
      <span style="font-size:11px;color:#909399;margin-left:10px">Zoom/腾讯会议等流媒体</span>
    </el-form-item>

    <el-form-item label="在线游戏" style="margin-bottom:6px">
      <el-switch v-model="form.app_priorities.gaming" active-text="优先（级别2）低延迟" inactive-text="不区分" />
      <span style="font-size:11px;color:#909399;margin-left:10px">CS/英雄联盟等，保障延迟</span>
    </el-form-item>

    <el-form-item label="P2P下载限速">
      <el-switch v-model="form.app_priorities.p2p" active-text="限制（级别8）" inactive-text="不限制" />
      <el-input v-if="form.app_priorities.p2p" v-model="form.app_priorities.p2p_limit" style="width:100px;margin-left:10px" placeholder="5M">
        <template #append>Mbps</template>
      </el-input>
      <span style="font-size:11px;color:#909399;margin-left:8px">BT/迅雷/电驴等下载工具</span>
    </el-form-item>

    <!-- 每IP限速 -->
    <el-divider content-position="left">
      <span style="color:#303133;font-weight:600">👤 每IP限速</span>
      <span style="font-size:11px;color:#909399">&nbsp;限制每个用户的带宽（防单机占用全部带宽）</span>
    </el-divider>
    <el-form-item label="每IP限速">
      <el-switch v-model="form.per_ip_enabled" active-text="开启" />
    </el-form-item>
    <el-form-item v-if="form.per_ip_enabled" label="每IP速率">
      <el-input v-model="form.per_ip_limit" style="width:140px" placeholder="10M">
        <template #append>Mbps</template>
      </el-input>
      <span style="font-size:11px;color:#909399;margin-left:8px">建议: 总带宽÷用户数，如50人 → 10M/人</span>
    </el-form-item>

    <!-- 预览 -->
    <el-divider />
    <div style="padding:10px 16px;background:#f0fdf4;border-radius:6px;font-size:12px;line-height:1.8;color:#166534">
      <div style="font-weight:600;margin-bottom:4px">📋 将生成的配置</div>
      <div>1. Mangle 标记: 自动为 {{ enabledApps.join('、') || '上网' }} 创建防火墙标记规则</div>
      <div>2. Queue Tree: 创建分层限速树，总带宽 ↓{{ form.total_bandwidth_down }} ↑{{ form.total_bandwidth_up }}</div>
      <div v-if="form.app_priorities.voip">3. VOIP电话始终优先（级别1），打满带宽才排队</div>
      <div v-if="form.app_priorities.p2p">4. P2P下载最低优先级（级别8），空闲时全速、忙时限速{{ form.app_priorities.p2p_limit }}</div>
      <div v-if="form.per_ip_enabled">5. 每IP限速 {{ form.per_ip_limit }}，防单机抢占</div>
    </div>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, computed, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const form = reactive({
  total_bandwidth_down: props.modelValue?.total_bandwidth_down || '100M',
  total_bandwidth_up: props.modelValue?.total_bandwidth_up || '20M',
  app_priorities: {
    voip: props.modelValue?.app_priorities?.voip ?? true,
    video: props.modelValue?.app_priorities?.video ?? false,
    http: props.modelValue?.app_priorities?.http ?? true,
    gaming: props.modelValue?.app_priorities?.gaming ?? false,
    p2p: props.modelValue?.app_priorities?.p2p ?? false,
    p2p_limit: props.modelValue?.app_priorities?.p2p_limit || '5M',
  },
  per_ip_enabled: props.modelValue?.per_ip_enabled ?? false,
  per_ip_limit: props.modelValue?.per_ip_limit || '10M',
})

/** 当前启用的应用名称列表 */
const enabledApps = computed(() => {
  const map: Record<string, string> = { voip: 'VOIP', video: '视频', http: '网页', gaming: '游戏', p2p: 'P2P' }
  return Object.entries(form.app_priorities)
    .filter(([k, v]) => k !== 'p2p_limit' && v)
    .map(([k]) => map[k] || k)
})

// 防抖 emit
let _qr: ReturnType<typeof setTimeout> | null = null
function _emit() {
  if (_qr) clearTimeout(_qr)
  _qr = setTimeout(() => emit('update:modelValue', { ...form }), 200)
}

// 只监听关键字段（避免完整 deep watch 性能问题）
watch([
  () => form.total_bandwidth_down,
  () => form.total_bandwidth_up,
  () => form.per_ip_enabled,
  () => form.per_ip_limit,
  () => form.app_priorities,
], () => _emit(), { deep: true })
</script>

<template>
  <div class="ros-policy">
    <!-- ─── 场景1：国内外智能分流 ─────────────────── -->
    <el-divider content-position="left">
      <span style="font-weight:600">🌏 国内外智能分流</span>
      <span style="font-size:11px;color:#909399">&nbsp;国内站走国内线、国外站走海外线（常用场景）</span>
    </el-divider>

    <el-form-item label="启用分流">
      <el-switch v-model="form.cnRoute.enabled" active-text="开启" @change="emitUpdate" />
    </el-form-item>

    <template v-if="form.cnRoute.enabled">
      <div class="scenario-card">
        <div class="scenario-desc">
          💡 <b>工作原理</b>（全自动，你只需告诉系统哪条线走什么）：<br/>
          1. 系统内置中国 IP 地址列表 → 2. 匹配国内流量打标签"走国内线" → 3. 剩余流量走默认 WAN（海外线）
        </div>

        <el-row :gutter="8" style="margin-bottom:8px">
          <el-col :span="12">
            <div class="wan-select-label">🇨🇳 国内流量走</div>
            <el-select v-model="form.cnRoute.cnWan" size="small" style="width:100%" filterable allow-create default-first-option>
              <el-option v-for="w in wanList" :key="w" :label="w + '（国内线）'" :value="w" />
            </el-select>
          </el-col>
          <el-col :span="12">
            <div class="wan-select-label">🌐 国外/海外流量走</div>
            <el-select v-model="form.cnRoute.intlWan" size="small" style="width:100%" filterable allow-create default-first-option>
              <el-option v-for="w in wanList" :key="w" :label="w + '（海外线）'" :value="w" />
            </el-select>
          </el-col>
        </el-row>

        <div class="ros-hint-box">
          <span v-if="form.cnRoute.cnWan === form.cnRoute.intlWan" style="color:#e6a23c">⚠ 两条线选了同一个口，分流不生效</span>
          <span v-else style="color:#67c23a">✅ 国内 → {{ form.cnRoute.cnWan }} · 国外 → {{ form.cnRoute.intlWan }}</span>
        </div>
      </div>
    </template>

    <!-- ─── 场景2：指定设备/网段走指定WAN ─────────────────── -->
    <el-divider content-position="left">
      <span style="font-weight:600">👤 指定设备走指定线路</span>
      <span style="font-size:11px;color:#909399">&nbsp;财务部走专线、监控走独立线、会议室走宽带</span>
    </el-divider>

    <div v-for="(pr, i) in form.deviceRoutes" :key="'dr'+i" class="scenario-card" :class="pr._expired ? 'dimmed' : ''">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span style="font-size:13px;font-weight:600">规则 {{ i + 1 }}</span>
        <el-button text type="danger" size="small" @click="form.deviceRoutes.splice(i,1);emitUpdate()">× 删除</el-button>
      </div>
      <el-row :gutter="8">
        <el-col :span="6">
          <div class="field-label">设备/网段</div>
          <el-input v-model="pr.srcAddr" size="small" placeholder="192.168.10.0/24" />
          <span class="field-hint">财务部/监控/会议室IP</span>
        </el-col>
        <el-col :span="6">
          <div class="field-label">走哪条线路？</div>
          <el-select v-model="pr.wanInterface" size="small" style="width:100%" filterable allow-create default-first-option>
            <el-option v-for="w in wanList" :key="w" :label="w" :value="w" />
          </el-select>
          <span class="field-hint">可自定义名称，如 HK/CN2</span>
        </el-col>
        <el-col :span="6">
          <div class="field-label">出口公网 IP</div>
          <el-input v-model="pr.srcNatIp" size="small" placeholder="留空 = masquerade" />
          <span class="field-hint">多公网IP时指定，如 203.0.113.5</span>
        </el-col>
        <el-col :span="6">
          <div class="field-label">备注说明</div>
          <el-input v-model="pr.comment" size="small" placeholder="如：财务专线" />
        </el-col>
      </el-row>
      <div class="ros-hint-box" style="margin-top:8px">
        {{ pr.srcAddr ? '✅ ' + pr.srcAddr + ' → ' + (pr.wanInterface || '未选') + (pr.srcNatIp ? '（SNAT: ' + pr.srcNatIp + '）' : '（自动masquerade）') : '⚠ 请填写设备IP或网段' }}
        <span v-if="pr._expired" style="color:#e6a23c">（已失效，请更新）</span>
      </div>
    </div>
    <el-button size="small" type="primary" plain @click="addDeviceRoute()" style="width:100%">+ 添加设备/网段</el-button>

    <!-- ─── 场景3：应用分流 ─────────────────── -->
    <el-divider content-position="left">
      <span style="font-weight:600">📱 按应用/端口分流</span>
      <span style="font-size:11px;color:#909399">&nbsp;HTTP走宽带、游戏走专线等</span>
    </el-divider>

    <div v-for="(ar, i) in form.appRoutes" :key="'ar'+i" class="scenario-card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span style="font-size:13px;font-weight:600">应用规则 {{ i + 1 }}</span>
        <el-button text type="danger" size="small" @click="form.appRoutes.splice(i,1);emitUpdate()">× 删除</el-button>
      </div>
      <el-row :gutter="6">
        <el-col :span="6">
          <div class="field-label">应用类型</div>
          <el-select v-model="ar.appType" size="small" style="width:100%" @change="onAppTypeChange(ar)">
            <el-option label="🌐 网页 (80/443)" value="web" />
            <el-option label="🎮 游戏 (UDP)" value="game" />
            <el-option label="📹 视频会议" value="voip" />
            <el-option label="📧 邮件 (SMTP)" value="mail" />
            <el-option label="⚡ 自定义端口" value="custom" />
          </el-select>
        </el-col>
        <el-col v-if="ar.appType === 'custom'" :span="6">
          <div class="field-label">自定义端口</div>
          <el-input v-model="ar.customPorts" size="small" placeholder="80,443 或 10000-20000" />
        </el-col>
        <el-col :span="6">
          <div class="field-label">走哪条线路</div>
          <el-select v-model="ar.wanInterface" size="small" style="width:100%" filterable allow-create default-first-option>
            <el-option v-for="w in wanList" :key="w" :label="w" :value="w" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <div class="field-label">备注</div>
          <el-input v-model="ar.comment" size="small" placeholder="如：视频专线" />
        </el-col>
      </el-row>
    </div>
    <el-button size="small" type="primary" plain @click="form.appRoutes.push({appType:'web',customPorts:'',wanInterface:wanList[0],comment:''});emitUpdate()" style="width:100%">+ 添加应用策略</el-button>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch, computed, nextTick } from 'vue'

const props = defineProps<{ modelValue: Record<string, any>; wanInterfaces?: string[] }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

// 可用的 WAN 口列表（从接口表单或默认）
const wanList = computed(() => {
  if (props.wanInterfaces && props.wanInterfaces.length > 0) return props.wanInterfaces
  return ['ether1', 'ether2', 'ether3']
})

const form = reactive({
  cnRoute: {
    enabled: props.modelValue?.cnRoute?.enabled ?? false,
    cnWan: props.modelValue?.cnRoute?.cnWan || wanList.value[0],
    intlWan: props.modelValue?.cnRoute?.intlWan || (wanList.value[1] || wanList.value[0]),
  },
  deviceRoutes: props.modelValue?.deviceRoutes?.length ? props.modelValue.deviceRoutes : [
    { srcAddr: '', wanInterface: wanList.value[0], srcNatIp: '', comment: '', _expired: false },
  ] as any[],
  appRoutes: props.modelValue?.appRoutes?.length ? props.modelValue.appRoutes : [
    { appType: 'web', customPorts: '', wanInterface: wanList.value[0], comment: '' },
  ] as any[],
})

function addDeviceRoute() {
  form.deviceRoutes.push({ srcAddr: '', wanInterface: wanList.value[0], srcNatIp: '', comment: '', _expired: false })
  emitUpdate()
}

function onAppTypeChange(ar: any) {
  const ports: Record<string, string> = { web: '80,443', game: '3074,27015-27030', voip: '5060,10000-20000', mail: '25,465,587,993' }
  ar.customPorts = ports[ar.appType] || ''
  emitUpdate()
}

let _pt: ReturnType<typeof setTimeout> | null = null
function emitUpdate() {
  if (_pt) clearTimeout(_pt)
  _pt = setTimeout(() => emit('update:modelValue', { ...form }), 200)
}

// 轻量 watch（只监听关键结构变化）
watch(() => form.deviceRoutes.length, () => emitUpdate())
watch(() => form.appRoutes.length, () => emitUpdate())
watch(() => form.cnRoute.enabled, () => emitUpdate())
watch(() => form.cnRoute.cnWan, () => emitUpdate())
watch(() => form.cnRoute.intlWan, () => emitUpdate())

// 父组件 props 更新时同步到内部 form（模板加载/切换场景时可能用到）
let _psyncing = false
watch(() => props.modelValue, (v) => {
  if (_psyncing || !v || Object.keys(v).length === 0) return
  _psyncing = true
  if (v.cnRoute) {
    if (typeof v.cnRoute.enabled === 'boolean') form.cnRoute.enabled = v.cnRoute.enabled
    if (v.cnRoute.cnWan) form.cnRoute.cnWan = v.cnRoute.cnWan
    if (v.cnRoute.intlWan) form.cnRoute.intlWan = v.cnRoute.intlWan
  }
  if (Array.isArray(v.deviceRoutes) && v.deviceRoutes.length > 0) {
    form.deviceRoutes.length = 0; form.deviceRoutes.push(...v.deviceRoutes)
  }
  if (Array.isArray(v.appRoutes) && v.appRoutes.length > 0) {
    form.appRoutes.length = 0; form.appRoutes.push(...v.appRoutes)
  }
  nextTick(() => { _psyncing = false })
}, { immediate: true })
</script>

<style scoped>
.scenario-card {
  background: #f9fafb;
  border: 1px solid #e8ecf1;
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 10px;
}
.scenario-desc {
  font-size: 12px;
  color: #606266;
  background: #ecf5ff;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 10px;
  line-height: 1.6;
}
.wan-select-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 2px;
  font-weight: 500;
}
.field-label {
  font-size: 11px;
  color: #606266;
  margin-bottom: 2px;
}
.field-hint {
  font-size: 10px;
  color: #c0c4cc;
  display: block;
  margin-top: 2px;
}
.ros-hint-box {
  font-size: 12px;
  padding: 6px 10px;
  background: #f0fdf4;
  border-radius: 4px;
  color: #166534;
  margin-top: 4px;
}
.dimmed {
  opacity: 0.5;
}
</style>

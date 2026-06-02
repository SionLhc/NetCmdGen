<template>
  <div class="router-wan">
    <!-- 设备型号选择（醒目放在第一行） -->
    <div v-if="props.vendor" style="background:#f0f7ff;border:1px solid #b3d8ff;border-radius:8px;padding:12px 16px;margin-bottom:12px">
      <div style="font-size:12px;color:#337ecc;margin-bottom:4px">📋 选择你的设备型号（确保命令100%兼容）</div>
      <el-select
        :model-value="deviceModel"
        @update:model-value="onModelChange"
        filterable
        placeholder="选设备型号（可搜索）"
        size="default"
        style="width:300px"
      >
        <el-option-group v-for="g in deviceModelOptions" :key="g.label" :label="g.label">
          <el-option v-for="m in g.options" :key="m.value" :label="m.label" :value="m.value" />
        </el-option-group>
      </el-select>
      <span v-if="!deviceModel" style="color:#e6a23c;font-size:12px;margin-left:12px">⚠ 未选择型号 — 生成命令为通用版本</span>
      <span v-else style="color:#67c23a;font-size:12px;margin-left:12px">✅ {{ deviceModel }}</span>
    </div>

    <!-- Web 配置引导（针对不支持命令行的低端设备） -->
    <el-alert v-if="isWebOnly" type="warning" :closable="false" show-icon style="margin-bottom:12px">
      <template #title>⚠ 该型号不支持命令行配置</template>
      <div style="font-size:12px;line-height:1.6">
        <strong>{{ deviceModel }}</strong> 为入门级设备，仅支持 Web 管理界面配置。
        请参考以下步骤：
        <ol style="margin:4px 0;padding-left:20px">
          <li>电脑连接设备 LAN 口，获取自动 IP（默认 192.168.1.x）</li>
          <li>浏览器打开 <code>https://192.168.1.1</code>（华为/H3C 默认管理 IP）</li>
          <li>默认用户名 <b>admin</b>，默认密码见设备底部贴纸</li>
          <li>进入「网络设置 → WAN口」选择上网方式填入账号</li>
        </ol>
        <span style="color:#e6a23c">建议升级为 AR2200 或更高型号以获得命令行支持</span>
      </div>
    </el-alert>

    <!-- 顶部引导 -->
    <el-alert type="success" :closable="false" show-icon style="margin-bottom:16px">
      <template #title>📖 每条宽带线路独立配置</template>
      单线只填第 1 行。多线时每行单独选上网方式、填对应参数。配置完下方实时预览命令。
    </el-alert>

    <div class="wan-lines">
      <div v-for="(line, li) in wanLines" :key="li" class="wan-line-card">
        <!-- 线路头部 -->
        <div class="wan-line-header">
          <div class="wan-line-title">
            <span class="wan-line-num">线路 {{ li + 1 }}</span>
            <span v-if="li === 0" class="wan-line-tag">主线路</span>
            <span v-else class="wan-line-tag backup">备用线路</span>
          </div>
          <div class="wan-line-desc">
            <el-input v-model="line.description" placeholder="备注（如：电信100M）" size="small" style="width:160px" />
            <span v-if="wanLines.length > 1" style="margin-left:8px">权重</span>
            <el-input-number v-if="wanLines.length > 1" v-model="line.weight" :min="1" :max="100" size="small" style="width:80px;margin-left:4px" />
          </div>
        </div>

        <!-- 上网方式 -->
        <div class="wan-line-type">
          <label class="wan-label">上网方式</label>
          <el-radio-group v-model="line.connectionType" size="small">
            <el-radio-button value="pppoe">PPPoE 拨号</el-radio-button>
            <el-radio-button value="static">静态 IP</el-radio-button>
            <el-radio-button value="dhcp">DHCP 获取</el-radio-button>
          </el-radio-group>
        </div>

        <!-- PPPoE 参数 -->
        <template v-if="line.connectionType === 'pppoe'">
          <div class="wan-line-fields">
            <div class="wan-field">
              <label>物理接口 <el-tooltip content="插光猫网线的接口" placement="top"><span class="help-icon">?</span></el-tooltip></label>
              <el-input v-model="line.pppoePhysical" :placeholder="li===0 ? 'GigabitEthernet0/0/0' : 'GigabitEthernet0/0/1'" size="small" />
            </div>
            <div class="wan-field">
              <label>宽带账号 <el-tooltip content="运营商提供的上网账号" placement="top"><span class="help-icon">?</span></el-tooltip></label>
              <el-input v-model="line.pppoeUser" placeholder="如 075512345678@adsl.gd" size="small" />
            </div>
            <div class="wan-field">
              <label>宽带密码 <el-tooltip content="和账号一起的密码" placement="top"><span class="help-icon">?</span></el-tooltip></label>
              <el-input v-model="line.pppoePass" type="password" show-password placeholder="运营商给的密码" size="small" />
            </div>
            <div class="wan-field">
              <label>MTU</label>
              <el-input-number v-model="line.pppoeMtu" :min="576" :max="1500" size="small" style="width:100%" />
            </div>
          </div>
          <div class="cmd-preview-single">{{ pppoePreview(li) }}</div>
        </template>

        <!-- 静态 IP 参数 -->
        <template v-if="line.connectionType === 'static'">
          <div class="wan-line-fields">
            <div class="wan-field">
              <label>物理接口</label>
              <el-input v-model="line.staticPhysical" :placeholder="li===0?'GigabitEthernet0/0/0':'GigabitEthernet0/0/1'" size="small" />
            </div>
            <div class="wan-field">
              <label>IP 地址</label>
              <el-input v-model="line.staticIp" placeholder="203.0.113.10" size="small" />
            </div>
            <div class="wan-field">
              <label>子网掩码</label>
              <el-input v-model="line.staticMask" placeholder="255.255.255.0" size="small" />
            </div>
            <div class="wan-field">
              <label>网关</label>
              <el-input v-model="line.staticGateway" placeholder="203.0.113.1" size="small" />
            </div>
          </div>
          <div class="cmd-preview-single">{{ staticPreview(li) }}</div>
        </template>

        <!-- DHCP 参数 -->
        <template v-if="line.connectionType === 'dhcp'">
          <div class="wan-line-fields">
            <div class="wan-field">
              <label>物理接口</label>
              <el-input v-model="line.dhcpPhysical" :placeholder="li===0?'GigabitEthernet0/0/0':'GigabitEthernet0/0/1'" size="small" />
            </div>
          </div>
          <div class="cmd-preview-single">{{ dhcpPreview(li) }}</div>
        </template>
      </div>
    </div>

    <!-- 增减线路 -->
    <div style="display:flex;gap:8px;margin-bottom:16px">
      <el-button v-if="wanLines.length < 3" size="small" type="primary" plain @click="addLine">+ 添加线路</el-button>
      <el-button v-if="wanLines.length > 1" size="small" type="danger" plain @click="removeLine">− 移除最后一条</el-button>
      <span style="font-size:12px;color:#909399;margin-left:8px;align-self:center">最多支持 3 条宽带线路</span>
    </div>

    <!-- NAT + 端口映射 -->
    <div class="wan-section">
      <h4>NAT 地址转换</h4>
      <p class="wan-desc">NAT 让内网多台设备共享公网 IP 上网。必须开启！</p>
      <el-switch v-model="natEnabled" active-text="开启（让内网上网）" size="large" />
    </div>

    <!-- 命令汇总预览 -->
    <div class="wan-section" style="background:#1a1b2e;border-color:#2d2d3d">
      <h4 style="color:#818cf8;margin-top:0">📋 命令汇总预览（将复制到 {{ vendorName }} 路由器 CLI 执行）</h4>
      <pre class="cmd-preview-full">{{ fullPreview }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch, ref } from 'vue'

const props = defineProps<{ modelValue: Record<string, any>; vendor?: string }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

const vendor = computed(() => props.vendor || 'huawei')
const vendorName = computed(() => {
  const m: Record<string,string> = { huawei:'华为 AR', h3c:'H3C MSR', ruijie:'锐捷 RSR', maipu:'迈普 MP' }
  return m[vendor.value] || vendor.value
})

// ─── 设备型号选择 ─────────────────────────────────
const deviceModel = ref(props.modelValue?.device_model || '')

const deviceModelOptions = computed(() => {
  const m: Record<string, {label:string, options:{label:string;value:string}[]}[]> = {
    huawei: [
      { label:'AR 企业路由器', options:[
        {label:'AR1200 系列（中小分支）',value:'AR1200'},{label:'AR2200/AR3200 系列（方案推荐★）',value:'AR2200'},
        {label:'AR6300 系列（高性能）',value:'AR6300'},{label:'NE 系列（运营商级）',value:'NE'}]},
    ],
    h3c: [
      { label:'MSR 路由器', options:[
        {label:'MSR 2600/3600 系列',value:'MSR2600'},{label:'MSR 5600 系列（方案推荐★）',value:'MSR5600'}]},
    ],
    ruijie: [
      { label:'RSR 路由器', options:[
        {label:'RSR10/20 系列',value:'RSR10'},{label:'RSR30/50 系列（方案推荐★）',value:'RSR30'},{label:'RSR77 系列',value:'RSR77'}]},
    ],
    maipu: [
      { label:'MP 路由器', options:[
        {label:'MP1800/2800 系列',value:'MP1800'},{label:'MP3800/4800 系列（方案推荐★）',value:'MP3800'}]},
    ],
  }
  return m[props.vendor || ''] || []
})

function onModelChange(val: string) {
  deviceModel.value = val
  emitUpdate()
}

// 不带配置命令的设备型号（如低端家用路由器）
const isWebOnly = computed(() => {
  const webOnlyModels = ['AR1200','RSR10','MP1800']
  return webOnlyModels.includes(deviceModel.value)
})

// ─── 每条线路独立结构 ────────────────────────────
interface WanLine {
  connectionType: 'pppoe' | 'static' | 'dhcp'
  description: string
  weight: number
  // PPPoE
  pppoePhysical: string; pppoeUser: string; pppoePass: string; pppoeMtu: number
  // Static
  staticPhysical: string; staticIp: string; staticMask: string; staticGateway: string
  // DHCP
  dhcpPhysical: string
}

const wanLines = reactive<WanLine[]>([
  { connectionType:'pppoe',description:'电信',weight:1,
    pppoePhysical:'GigabitEthernet0/0/0',pppoeUser:'',pppoePass:'',pppoeMtu:1492,
    staticPhysical:'GigabitEthernet0/0/0',staticIp:'',staticMask:'255.255.255.0',staticGateway:'',
    dhcpPhysical:'GigabitEthernet0/0/0',
  },
])

const natEnabled = ref(true)

function addLine() {
  if (wanLines.length >= 3) return
  wanLines.push({
    connectionType:'pppoe',description:'联通',weight:1,
    pppoePhysical:`GigabitEthernet0/0/${wanLines.length}`,pppoeUser:'',pppoePass:'',pppoeMtu:1492,
    staticPhysical:`GigabitEthernet0/0/${wanLines.length}`,staticIp:'',staticMask:'255.255.255.0',staticGateway:'',
    dhcpPhysical:`GigabitEthernet0/0/${wanLines.length}`,
  })
  emitUpdate()
}

function removeLine() {
  if (wanLines.length <= 1) return
  wanLines.pop()
  emitUpdate()
}

// ─── 单线命令预览 ────────────────────────────────
const cmdH = (t: string) => `# ${t}\n`

function pppoePreview(li: number): string {
  const l = wanLines[li]; const u = l.pppoeUser || '{账号}'
  const pw = l.pppoePass || '{密码}'; const ph = l.pppoePhysical || `GE0/0/${li}`
  if (vendor.value === 'huawei') return `acl 2000 rule 5 permit\ninterface Dialer${li+1}\n link-protocol ppp\n ppp chap user ${u}\n ppp chap password simple ${pw}\n ip address ppp-negotiate\n dialer bundle ${li+1}\n dialer-group 1\n nat outbound 2000\n\ninterface ${ph}\n pppoe-client dial-bundle-number ${li+1}`
  if (vendor.value === 'h3c') return `interface Dialer${li+1}\n dialer bundle enable\n ip address ppp-negotiate\n ppp chap user ${u}\n ppp chap password simple ${pw}\n nat outbound\n\ninterface ${ph}\n pppoe-client dial-bundle-number ${li+1}`
  if (vendor.value === 'ruijie') return `interface ${ph}\n ip address pppoe-client\n pppoe-client dial-pool-number 1\n\ninterface Dialer 1\n ip address negotiated\n ppp chap hostname ${u}\n ppp chap password 0 ${pw}`
  return `interface Dialer${li+1}\n encapsulation ppp\n ppp chap hostname ${u}\n ppp chap password 0 ${pw}\n ip address negotiated\n dialer pool ${li+1}\n\ninterface ${ph}\n pppoe-client dial-pool-number ${li+1}`
}

function staticPreview(li: number): string {
  const l = wanLines[li]; const ip = l.staticIp || '{IP}'; const gw = l.staticGateway || '{网关}'
  const ph = l.staticPhysical || `GE0/0/${li}`
  if (vendor.value === 'huawei') return `interface ${ph}\n ip address ${ip} ${l.staticMask}\n nat outbound 2000\n\nip route-static 0.0.0.0 0.0.0.0 ${gw}`
  if (vendor.value === 'h3c') return `interface ${ph}\n ip address ${ip} ${l.staticMask}\n nat outbound\n\nip route-static 0.0.0.0 0 ${gw}`
  return `interface ${ph}\n ip address ${ip} ${l.staticMask}\n\nip route 0.0.0.0 0.0.0.0 ${gw}`
}

function dhcpPreview(li: number): string {
  const ph = wanLines[li].dhcpPhysical || `GE0/0/${li}`
  if (vendor.value === 'huawei') return `interface ${ph}\n ip address dhcp-alloc\n nat outbound 2000`
  if (vendor.value === 'h3c') return `interface ${ph}\n ip address dhcp-alloc\n nat outbound`
  return `interface ${ph}\n ip address dhcp-alloc`
}

// ─── 汇总预览 ────────────────────────────────────
const fullPreview = computed(() => {
  const parts: string[] = [cmdH(`=== ${vendorName} 路由器 WAN 配置 ===`)]
  for (let i = 0; i < wanLines.length; i++) {
    const l = wanLines[i]
    parts.push(cmdH(`线路 ${i+1}: ${l.description} (${l.connectionType.toUpperCase()})`))
    if (l.connectionType === 'pppoe') parts.push(pppoePreview(i))
    else if (l.connectionType === 'static') parts.push(staticPreview(i))
    else parts.push(dhcpPreview(i))
    parts.push('')
  }
  // 多线负载均衡
  if (wanLines.length > 1 && vendor.value === 'huawei') {
    parts.push(cmdH('策略路由（负载均衡）'))
    for (let i = 0; i < wanLines.length; i++) {
      const l = wanLines[i]
      parts.push(`acl number 300${i+1}`)
      parts.push(` rule 5 permit ip source 192.168.1.0 0.0.0.255`)
      parts.push(`policy-based-route pbr${i+1} permit node 10`)
      parts.push(` if-match acl 300${i+1}`)
      parts.push(` apply output-interface Dialer${i+1}`)
    }
  }
  return parts.join('\n')
})

// ─── emit ─────────────────────────────────────────
function emitUpdate() {
  emit('update:modelValue', {
    wanLines: wanLines.map(l => ({ ...l })),
    natEnabled: natEnabled.value,
    device_model: deviceModel.value,
  })
}

watch(wanLines, () => emitUpdate(), { deep: true })
watch(natEnabled, () => emitUpdate())

// 初始化
watch(() => props.modelValue, (v) => {
  if (!v || Object.keys(v).length === 0) return
  if (Array.isArray(v.wanLines) && v.wanLines.length > 0) {
    wanLines.length = 0
    v.wanLines.forEach((l: any) => wanLines.push({ ...l }))
  }
  if (typeof v.natEnabled === 'boolean') natEnabled.value = v.natEnabled
}, { immediate: true, once: true })
</script>

<style scoped>
.router-wan { max-width: 780px; }
.wan-lines { display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; }
.wan-line-card { border: 1px solid #e8ecf1; border-radius: 10px; padding: 14px; background: #fff; }
.wan-line-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.wan-line-title { display: flex; align-items: center; gap: 8px; }
.wan-line-num { font-size: 15px; font-weight: 700; color: #303133; }
.wan-line-tag { font-size: 11px; padding: 1px 8px; border-radius: 4px; background: #ecf5ff; color: #409eff; }
.wan-line-tag.backup { background: #fef0e6; color: #e6a23c; }
.wan-line-desc { display: flex; align-items: center; }
.wan-line-type { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.wan-label { font-size: 12px; color: #606266; font-weight: 500; min-width: 60px; }
.wan-line-fields { display: flex; gap: 8px; flex-wrap: wrap; }
.wan-field { flex: 1; min-width: 140px; }
.wan-field label { display: block; font-size: 11px; color: #909399; margin-bottom: 2px; font-weight: 500; }
.help-icon { display: inline-flex; align-items: center; justify-content: center; width: 14px; height: 14px; border-radius: 50%; background: #c0c4cc; color: #fff; font-size: 10px; cursor: help; margin-left: 2px; }
.cmd-preview-single { margin-top: 8px; padding: 8px 12px; background: #f0f9eb; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 11px; color: #67c23a; line-height: 1.4; white-space: pre-wrap; }
.wan-section { padding: 16px; background: #fafbfc; border: 1px solid #e8ecf1; border-radius: 10px; margin-bottom: 16px; }
.wan-section h4 { margin: 0 0 6px 0; font-size: 15px; color: #303133; }
.wan-desc { margin: 0 0 8px 0; font-size: 12px; color: #909399; }
.cmd-preview-full { margin: 0; padding: 12px; background: #1a1b2e; color: #a6e22e; font-family: 'Consolas', monospace; font-size: 12px; line-height: 1.5; border-radius: 6px; white-space: pre-wrap; max-height: 400px; overflow: auto; }
</style>

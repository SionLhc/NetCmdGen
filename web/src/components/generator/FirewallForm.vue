<template>
  <div class="firewall-form">
    <el-alert type="error" :closable="false" show-icon style="margin-bottom:16px">
      <template #title>⚠ 仅展示 CLI 命令行。不支持命令行的防火墙型号不在此处生成。</template>
      {{ vendor==='huawei' ? '适用: 华为 USG6000/6600/9500 系列' : vendor==='h3c' ? '适用: H3C SecPath F1000/F5000 系列' : '适用: ' + vendorName + ' CLI 管理型号' }}
    </el-alert>

    <el-tabs v-model="activeFwTab" type="card">
      <!-- ═══ 安全区域 ═══ -->
      <el-tab-pane label="安全区域" name="zone">
        <div class="fw-section">
          <h4>安全区域定义（Security Zone）</h4>
          <p class="fw-hint">Trust(内网) / Untrust(外网) / DMZ(隔离区) — 防火墙的核心是区域间策略控制</p>
          <div v-for="(_, i) in form.zones" :key="'z'+i" class="fw-row">
            <el-row :gutter="6" align="middle">
              <el-col :span="5"><el-input v-model="form.zones[i].name" size="small" placeholder="区域名称（如 Trust）" /></el-col>
              <el-col :span="6"><el-input-number v-model="form.zones[i].priority" :min="1" :max="100" size="small" placeholder="优先级" style="width:100%" /></el-col>
              <el-col :span="6">
                <el-select v-model="form.zones[i].ifaces" size="small" multiple placeholder="绑定接口" style="width:100%">
                  <el-option v-for="iface in knownIfaces" :key="iface" :label="iface" :value="iface" />
                </el-select>
              </el-col>
              <el-col :span="1"><el-button text type="danger" size="small" @click="form.zones.splice(i,1);emitUpdate()">✕</el-button></el-col>
            </el-row>
          </div>
          <el-button size="small" @click="form.zones.push({name:'Trust',priority:85,ifaces:['GE0/0/0']});emitUpdate()" style="width:100%">+ 添加区域</el-button>
          <div class="cmd-block">
            <div class="cmd-title">→ {{ vendor==='huawei'?'华为 USG':'H3C SecPath' }} 安全区域命令</div>
            <pre>{{ zoneCmdPreview }}</pre>
          </div>
        </div>
      </el-tab-pane>

      <!-- ═══ 安全策略 ═══ -->
      <el-tab-pane label="安全策略" name="policy">
        <div class="fw-section">
          <h4>域间安全策略（源 Zone → 目的 Zone）</h4>
          <p class="fw-hint">防火墙核心：控制 Trust→Untrust(上网)、Untrust→DMZ(外访服务器) 等跨区域流量</p>
          <div v-for="(_, i) in form.policies" :key="'p'+i" class="fw-card">
            <div class="card-hdr"><span>策略 {{ i+1 }}</span><el-button text type="danger" size="small" @click="form.policies.splice(i,1);emitUpdate()">删除</el-button></div>
            <el-row :gutter="4">
              <el-col :span="6"><label class="ml">源 Zone</label><el-select v-model="form.policies[i].fromZone" size="small" style="width:100%"><el-option v-for="z in form.zones" :key="z.name" :label="z.name" :value="z.name" /></el-select></el-col>
              <el-col :span="6"><label class="ml">目的 Zone</label><el-select v-model="form.policies[i].toZone" size="small" style="width:100%"><el-option v-for="z in form.zones" :key="z.name" :label="z.name" :value="z.name" /></el-select></el-col>
              <el-col :span="5"><label class="ml">源地址</label><el-input v-model="form.policies[i].srcAddr" size="small" placeholder="192.168.1.0/24" /></el-col>
              <el-col :span="5"><label class="ml">目的地址</label><el-input v-model="form.policies[i].dstAddr" size="small" placeholder="any" /></el-col>
            </el-row>
            <el-row :gutter="4" style="margin-top:4px">
              <el-col :span="6"><label class="ml">协议/端口</label><el-input v-model="form.policies[i].service" size="small" placeholder="tcp/80,443 或 any" /></el-col>
              <el-col :span="4"><label class="ml">动作</label><el-select v-model="form.policies[i].action" size="small" style="width:100%"><el-option label="permit(允许)" value="permit" /><el-option label="deny(拒绝)" value="deny" /></el-select></el-col>
              <el-col :span="4"><label class="ml">日志</label><el-switch v-model="form.policies[i].logging" size="small" /></el-col>
              <el-col :span="8"><label class="ml">描述</label><el-input v-model="form.policies[i].description" size="small" placeholder="如：允许内网上网" /></el-col>
            </el-row>
            <div class="cmd-block">
              <pre>{{ policyPreview(i) }}</pre>
            </div>
          </div>
          <el-button size="small" type="primary" plain @click="form.policies.push({fromZone:'Trust',toZone:'Untrust',srcAddr:'192.168.1.0/24',dstAddr:'any',service:'any',action:'permit',logging:true,description:''});emitUpdate()" style="width:100%">+ 添加策略</el-button>
        </div>
      </el-tab-pane>

      <!-- ═══ NAT 策略 ═══ -->
      <el-tab-pane label="NAT 策略" name="nat">
        <div class="fw-section">
          <h4>NAT 地址转换</h4>
          <el-switch v-model="form.natEnabled" active-text="启用 NAT" size="default" />
          <template v-if="form.natEnabled">
            <div v-for="(_, i) in form.natRules" :key="'nat'+i" class="fw-card">
              <div class="card-hdr"><span>SNAT {{ i+1 }}</span></div>
              <el-row :gutter="4">
                <el-col :span="6"><label class="ml">源 Zone</label><el-select v-model="form.natRules[i].srcZone" size="small" style="width:100%"><el-option v-for="z in form.zones" :key="z.name" :label="z.name" :value="z.name" /></el-select></el-col>
                <el-col :span="6"><label class="ml">目的 Zone</label><el-select v-model="form.natRules[i].dstZone" size="small" style="width:100%"><el-option v-for="z in form.zones" :key="z.name" :label="z.name" :value="z.name" /></el-select></el-col>
                <el-col :span="6"><label class="ml">源地址</label><el-input v-model="form.natRules[i].srcAddr" size="small" placeholder="192.168.1.0/24" /></el-col>
                <el-col :span="5"><label class="ml">转换后地址</label><el-input v-model="form.natRules[i].translatedAddr" size="small" placeholder="出接口IP或地址池" /></el-col>
              </el-row>
            </div>
            <div class="cmd-block">
              <div class="cmd-title">→ {{ vendor==='huawei'?'华为 USG':'H3C SecPath' }} NAT 命令</div>
              <pre>{{ natCmdPreview }}</pre>
            </div>
          </template>
        </div>
      </el-tab-pane>

      <!-- ═══ IPSec VPN ═══ -->
      <el-tab-pane label="IPSec VPN" name="vpn">
        <div class="fw-section">
          <h4>IPSec VPN 隧道</h4>
          <el-switch v-model="form.vpnEnabled" active-text="配置 VPN" size="default" />
          <template v-if="form.vpnEnabled">
            <el-row :gutter="8" style="margin-top:8px">
              <el-col :span="8"><label class="ml">对端公网 IP</label><el-input v-model="form.vpnPeerIp" size="small" placeholder="203.0.113.1" /></el-col>
              <el-col :span="8"><label class="ml">预共享密钥</label><el-input v-model="form.vpnPsk" size="small" type="password" show-password placeholder="Pre-Shared Key" /></el-col>
              <el-col :span="8"><label class="ml">本地私网</label><el-input v-model="form.vpnLocalNet" size="small" placeholder="192.168.1.0/24" /></el-col>
            </el-row>
            <el-row :gutter="8" style="margin-top:6px">
              <el-col :span="8"><label class="ml">对端私网</label><el-input v-model="form.vpnRemoteNet" size="small" placeholder="10.0.0.0/24" /></el-col>
              <el-col :span="8"><label class="ml">加密算法</label><el-select v-model="form.vpnEncryption" size="small" style="width:100%"><el-option label="AES-256" value="aes-256" /><el-option label="AES-128" value="aes-128" /><el-option label="3DES" value="3des" /></el-select></el-col>
              <el-col :span="8"><label class="ml">认证算法</label><el-select v-model="form.vpnAuth" size="small" style="width:100%"><el-option label="SHA2-256" value="sha2-256" /><el-option label="SHA1" value="sha1" /></el-select></el-col>
            </el-row>
            <div class="cmd-block" style="margin-top:8px">
              <div class="cmd-title">→ {{ vendor==='huawei'?'华为':'H3C' }} IPSec VPN 命令</div>
              <pre>{{ vpnCmdPreview }}</pre>
            </div>
          </template>
        </div>
      </el-tab-pane>

      <!-- ═══ 会话管理 ═══ -->
      <el-tab-pane label="会话管理" name="session">
        <div class="fw-section">
          <h4>会话表与老化时间</h4>
          <el-row :gutter="8">
            <el-col :span="8">
              <label class="ml">TCP 老化时间(秒)</label>
              <el-input-number v-model="form.sessionTcpTimeout" :min="60" :max="86400" size="small" style="width:100%" />
            </el-col>
            <el-col :span="8">
              <label class="ml">UDP 老化时间(秒)</label>
              <el-input-number v-model="form.sessionUdpTimeout" :min="30" :max="86400" size="small" style="width:100%" />
            </el-col>
            <el-col :span="8">
              <label class="ml">ICMP 老化时间(秒)</label>
              <el-input-number v-model="form.sessionIcmpTimeout" :min="5" :max="600" size="small" style="width:100%" />
            </el-col>
          </el-row>
          <div class="cmd-block" style="margin-top:8px">
            <pre>{{ sessionCmdPreview }}</pre>
          </div>
        </div>
      </el-tab-pane>

      <!-- ═══ 日志/审计 ═══ -->
      <el-tab-pane label="日志与审计" name="log">
        <div class="fw-section">
          <h4>Syslog / 日志服务器</h4>
          <el-row :gutter="8">
            <el-col :span="12"><label class="ml">日志服务器 IP</label><el-input v-model="form.logServer" size="small" placeholder="192.168.1.100" /></el-col>
            <el-col :span="6"><label class="ml">日志级别</label><el-select v-model="form.logLevel" size="small" style="width:100%"><el-option label="informational" value="informational" /><el-option label="warning" value="warning" /><el-option label="debugging" value="debugging" /></el-select></el-col>
            <el-col :span="6"><label class="ml">端口</label><el-input-number v-model="form.logPort" :min="1" :max="65535" size="small" style="width:100%" /></el-col>
          </el-row>
          <div class="cmd-block" style="margin-top:8px">
            <pre>{{ logCmdPreview }}</pre>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any>; vendor?: string }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

const vendor = computed(() => props.vendor || 'huawei')
const vendorName = computed(() => {
  const m: Record<string,string> = { huawei:'华为 USG', h3c:'H3C SecPath', ruijie:'锐捷 RG-WALL', maipu:'迈普 MSG' }
  return m[vendor.value] || vendor.value
})
const knownIfaces = ['GigabitEthernet0/0/0','GigabitEthernet0/0/1','GigabitEthernet0/0/2','Vlanif1']
const activeFwTab = ref('zone')

const form = reactive({
  zones: [{name:'Trust',priority:85,ifaces:['GE0/0/0']},{name:'Untrust',priority:5,ifaces:['GE0/0/1']},{name:'DMZ',priority:50,ifaces:['GE0/0/2']}],
  policies: [] as any[],
  natEnabled: false, natRules: [] as any[],
  vpnEnabled: false, vpnPeerIp:'', vpnPsk:'', vpnLocalNet:'192.168.1.0/24', vpnRemoteNet:'10.0.0.0/24', vpnEncryption:'aes-256', vpnAuth:'sha2-256',
  sessionTcpTimeout: 3600, sessionUdpTimeout: 120, sessionIcmpTimeout: 15,
  logServer: '', logLevel: 'informational', logPort: 514,
})

// ── 命令预览（全部在 computed 中，不放在模板 {{ }} 里用模板字面量）──

const zoneCmdPreview = computed(() => {
  if (vendor.value === 'huawei') {
    return 'firewall zone name Trust\n add interface GigabitEthernet0/0/0\n set priority 85\n# 验证: display zone\n# 回滚: undo firewall zone name Trust'
  }
  return 'security-zone name Trust\n import interface GigabitEthernet0/0/0\n# 验证: display security-zone\n# 回滚: undo security-zone name Trust'
})

function policyPreview(i: number): string {
  const p = form.policies[i]; if (!p) return ''
  if (vendor.value === 'huawei') {
    return 'security-policy\n rule name Policy' + (i+1) + '\n  source-zone ' + (p.fromZone||'Trust')
      + '\n  destination-zone ' + (p.toZone||'Untrust') + '\n  source-address ' + (p.srcAddr||'any')
      + '\n  destination-address ' + (p.dstAddr||'any') + '\n  service ' + (p.service||'any')
      + '\n  action ' + (p.action||'permit') + '\n  logging'
      + '\n# 验证: display security-policy rule all\n# 回滚: undo security-policy rule name Policy' + (i+1)
  }
  return 'rule ' + (i+1) + ' permit ip source ' + (p.srcAddr||'any') + ' destination ' + (p.dstAddr||'any')
    + '\n# 验证: display packet-filter\n# 回滚: undo rule ' + (i+1)
}

const natCmdPreview = computed(() => {
  if (vendor.value === 'huawei') {
    return 'nat-policy\n rule name NAT-Internet\n  source-zone Trust\n  destination-zone Untrust\n  source-address 192.168.1.0 24\n  action source-nat easy-ip\n# 验证: display nat-policy rule all\n# 回滚: undo nat-policy rule name NAT-Internet'
  }
  return 'nat-policy\n policy 1\n  source-zone Trust\n  destination-zone Untrust\n  action easy-ip\n# 验证: display nat policy\n# 回滚: undo nat-policy'})

const vpnCmdPreview = computed(() => {
  const peer = form.vpnPeerIp || '203.0.113.1'
  const psk = form.vpnPsk || '{密钥}'
  if (vendor.value === 'huawei') {
    return 'ipsec proposal prop1\n encapsulation-mode tunnel\n transform esp\n esp authentication-algorithm sha2-256\n esp encryption-algorithm aes-256\n# 验证: display ipsec proposal\n# 回滚: undo ipsec proposal prop1\n\nike peer ' + peer + '\n pre-shared-key ' + psk + '\n remote-address ' + peer + '\n# 验证: display ike peer\n# 回滚: undo ike peer ' + peer
  }
  return 'ipsec transform-set tset1\n encapsulation-mode tunnel\n transform esp\n esp authentication-algorithm sha2-256\n esp encryption-algorithm aes-256\n\nike keychain kc1\n pre-shared-key address ' + peer + ' key simple ' + psk
})

const sessionCmdPreview = computed(() => {
  const tcp = form.sessionTcpTimeout, udp = form.sessionUdpTimeout, icmp = form.sessionIcmpTimeout
  if (vendor.value === 'huawei') {
    return 'firewall session aging-time tcp ' + tcp + '\nfirewall session aging-time udp ' + udp + '\nfirewall session aging-time icmp ' + icmp + '\n# 验证: display firewall session aging-time\n# 查看会话表: display firewall session table\n# 清除会话: reset firewall session table'
  }
  return 'session aging-time tcp ' + tcp + '\nsession aging-time udp ' + udp + '\n# 验证: display session aging-time\n# 查看: display session table'
})

const logCmdPreview = computed(() => {
  const svr = form.logServer || '192.168.1.100'
  const level = form.logLevel || 'informational'
  const port = form.logPort || 514
  if (vendor.value === 'huawei') {
    return 'info-center enable\ninfo-center loghost ' + svr + ' facility local0\ninfo-center source default channel loghost log level ' + level + '\nfirewall log session enable\n# 验证: display info-center\n# 回滚: undo info-center loghost ' + svr
  }
  return 'info-center enable\ninfo-center loghost ' + svr + ' port ' + port + ' facility local7\n# 验证: display logbuffer\n# 回滚: undo info-center loghost'
})

function emitUpdate() { emit('update:modelValue', { ...form }) }
watch(() => props.modelValue, (v) => { if (v && Object.keys(v).length > 0) Object.assign(form, v) }, { immediate: true })
watch(form, () => emitUpdate(), { deep: true })
</script>

<style scoped>
.firewall-form { max-width: 820px; }
.fw-section { margin-bottom: 12px; }
.fw-section h4 { margin: 0 0 4px 0; font-size: 14px; color: #303133; }
.fw-hint { margin: 0 0 8px 0; font-size: 11px; color: #909399; }
.fw-row { margin-bottom: 6px; }
.fw-card { border: 1px solid #e8ecf1; border-radius: 8px; padding: 10px; margin-bottom: 10px; background: #fafbfc; }
.card-hdr { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; font-weight: 600; font-size: 13px; }
.ml { font-size: 10px; color: #909399; display: block; margin-bottom: 2px; }
.cmd-block { margin-top: 6px; background: #1e1e1e; color: #a6e22e; font-family: Consolas, monospace; font-size: 11px; padding: 8px; border-radius: 4px; }
.cmd-block pre { margin: 0; white-space: pre-wrap; }
.cmd-title { color: #569cd6; margin-bottom: 4px; font-weight: 600; }
</style>

<template>
  <div class="router-wan">
    <!-- 顶部步骤说明 -->
    <el-alert type="success" :closable="false" show-icon style="margin-bottom:16px">
      <template #title>📖 第 1 步：选上网方式 → 第 2 步：填账号/IP → 第 3 步：配 NAT → 第 4 步：配 DHCP</template>
      每一步完成后会在下方实时预览将要生成的命令。直接复制到 {{ vendorName }} 路由器 CLI 执行即可。
    </el-alert>
    <el-alert v-if="vendor==='ruijie'||vendor==='maipu'" type="info" :closable="false" show-icon style="margin-bottom:12px">
      <template #title>💻 {{ vendor==='ruijie'?'锐捷 eWeb':'迈普 Web' }} 管理页面也可以配置</template>
      浏览器访问 <b>https://{路由器IP}</b> → 登录 → 网络设置 → 广域网/WAN → 按下方表格填写字段即可，不需要敲命令。
    </el-alert>

    <el-form label-width="120px" size="default" @change="emitUpdate">
      <!-- ═══ 第1步：上网方式 ═══ -->
      <div class="step-section">
        <div class="step-number">1</div>
        <div class="step-content">
          <h4>选择上网方式</h4>
          <p class="step-desc">这是路由器连接互联网的方式。家庭宽带选 PPPoE，企业专线选静态 IP，光猫已拨号选 DHCP。</p>
          <el-radio-group v-model="form.connectionType" size="large" style="margin-top:8px">
            <el-radio-button value="pppoe">
              <span class="radio-label">🏠 PPPoE 拨号</span>
              <span class="radio-desc">家庭宽带</span>
            </el-radio-button>
            <el-radio-button value="static">
              <span class="radio-label">🏢 静态 IP</span>
              <span class="radio-desc">企业专线</span>
            </el-radio-button>
            <el-radio-button value="dhcp">
              <span class="radio-label">📡 DHCP 获取</span>
              <span class="radio-desc">光猫已拨号</span>
            </el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <!-- ═══ 第2步：填写参数 ═══ -->
      <div class="step-section">
        <div class="step-number">2</div>
        <div class="step-content">
          <h4>填写连接参数</h4>

          <!-- PPPoE -->
          <template v-if="form.connectionType === 'pppoe'">
            <p class="step-desc">填入运营商给你的宽带账号和密码。不知道可以打电话问运营商客服（10086/10010/10000）。</p>
            <el-row :gutter="12" style="margin-top:8px">
              <el-col :span="12">
                <div class="field-with-help">
                  <label>宽带账号 <el-tooltip content="运营商给你的上网账号，通常是手机号或固话号码加后缀" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.pppoeUser" placeholder="例如：075512345678@adsl.gd" />
                </div>
              </el-col>
              <el-col :span="12">
                <div class="field-with-help">
                  <label>宽带密码 <el-tooltip content="和宽带账号一起的密码，通常是6位数字" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.pppoePass" type="password" show-password placeholder="运营商给的密码" />
                </div>
              </el-col>
            </el-row>
            <el-row :gutter="12" style="margin-top:8px">
              <el-col :span="8">
                <div class="field-with-help">
                  <label>WAN 物理口 <el-tooltip content="路由器上插光猫网线的那个接口。华为: GE0/0/0, 华三: GE0/0" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.pppoePhysical" :placeholder="vendor==='huawei'?'GigabitEthernet0/0/0':'GigabitEthernet0/0'" />
                </div>
              </el-col>
              <el-col :span="8">
                <div class="field-with-help">
                  <label>MTU <el-tooltip content="最大传输单元。拨号用1492（默认），如部分网页打不开可调小到1452" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input-number v-model="form.pppoeMtu" :min="576" :max="1500" style="width:100%" />
                </div>
              </el-col>
              <el-col :span="8">
                <div class="field-with-help">
                  <label>首选 DNS <el-tooltip content="域名服务器，用于把网址翻译成IP。可用114.114.114.114或8.8.8.8" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.primaryDns" placeholder="114.114.114.114" />
                </div>
              </el-col>
            </el-row>
          </template>

          <!-- 静态 IP -->
          <template v-if="form.connectionType === 'static'">
            <p class="step-desc">填入运营商给你的固定 IP 地址、掩码和网关。企业专线才会有这些信息。</p>
            <el-row :gutter="12" style="margin-top:8px">
              <el-col :span="6">
                <div class="field-with-help">
                  <label>IP 地址 <el-tooltip content="运营商分配给你的公网IP地址" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.staticIp" placeholder="203.0.113.10" />
                </div>
              </el-col>
              <el-col :span="6">
                <div class="field-with-help">
                  <label>子网掩码 <el-tooltip content="通常是255.255.255.0 或 255.255.255.252" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.staticMask" placeholder="255.255.255.0" />
                </div>
              </el-col>
              <el-col :span="6">
                <div class="field-with-help">
                  <label>网关 <el-tooltip content="运营商提供的默认网关地址" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.staticGateway" placeholder="203.0.113.1" />
                </div>
              </el-col>
              <el-col :span="6">
                <div class="field-with-help">
                  <label>物理接口 <el-tooltip content="运营商网线插在路由器的哪个口" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.staticPhysical" placeholder="GigabitEthernet0/0/0" />
                </div>
              </el-col>
            </el-row>
          </template>

          <!-- DHCP -->
          <template v-if="form.connectionType === 'dhcp'">
            <p class="step-desc">光猫已经拨号了，路由器只要插上就能从光猫自动获取 IP。只需指定物理接口。</p>
            <div class="field-with-help" style="width:300px;margin-top:8px">
              <label>物理接口 <el-tooltip content="插光猫的接口" placement="top"><span class="help-icon">?</span></el-tooltip></label>
              <el-input v-model="form.dhcpPhysical" :placeholder="vendor==='huawei'?'GigabitEthernet0/0/0':'GigabitEthernet0/0'" />
            </div>
          </template>
        </div>
      </div>

      <!-- ═══ 实时命令预览 ═══ -->
      <div class="step-section">
        <div class="step-number" style="background:#67c23a">✅</div>
        <div class="step-content">
          <h4>命令预览 — 以下命令将复制到 {{ vendorName }} 路由器执行</h4>
          <div class="cmd-preview">{{ generatedPreview }}</div>
        </div>
      </div>

      <!-- ═══ 第3步：NAT ═══ -->
      <div class="step-section">
        <div class="step-number">3</div>
        <div class="step-content">
          <h4>NAT 地址转换</h4>
          <p class="step-desc">NAT 让内网的多台电脑、手机共享这一个公网 IP 上网。必须开启！</p>
          <el-switch v-model="form.natEnabled" active-text="必须开启（让内网上网）" size="large" />
          <div v-if="form.natEnabled" style="margin-top:12px">
            <p class="step-desc" style="font-weight:600">🔄 端口映射 / DNAT：让外网可以访问内网的服务器</p>
            <p class="step-desc">例如：把路由器的 8443 端口转发到内网 192.168.1.10 的 443 端口，这样外网就能访问你的内部 HTTPS 服务了。</p>
            <div v-for="(dnat, di) in form.dnatRules" :key="'dnat'+di" class="dnat-row">
              <el-row :gutter="6" align="middle">
                <el-col :span="3"><label class="mini-label">外网端口</label><el-input-number v-model="form.dnatRules[di].publicPort" :min="1" :max="65535" style="width:100%" /></el-col>
                <el-col :span="1" style="text-align:center;padding-top:18px">→</el-col>
                <el-col :span="6"><label class="mini-label">内网 IP</label><el-input v-model="form.dnatRules[di].internalIp" placeholder="192.168.1.10" /></el-col>
                <el-col :span="1" style="text-align:center;padding-top:18px">:</el-col>
                <el-col :span="3"><label class="mini-label">内网端口</label><el-input-number v-model="form.dnatRules[di].internalPort" :min="1" :max="65535" style="width:100%" /></el-col>
                <el-col :span="4"><label class="mini-label">协议</label><el-select v-model="form.dnatRules[di].protocol" style="width:100%"><el-option label="TCP" value="tcp" /><el-option label="UDP" value="udp" /></el-select></el-col>
                <el-col :span="5"><label class="mini-label">用途说明</label><el-input v-model="form.dnatRules[di].description" placeholder="如: 公司网站" /></el-col>
                <el-col :span="1" style="padding-top:18px"><el-button text type="danger" @click="form.dnatRules.splice(di,1);emitUpdate()">✕</el-button></el-col>
              </el-row>
              <div class="dnat-preview">
                {{ vendor==='huawei' ? 'nat server protocol '+(form.dnatRules[di]?.protocol||'tcp')+' global current-interface '+(form.dnatRules[di]?.publicPort||'')+' inside '+(form.dnatRules[di]?.internalIp||'x.x.x.x')+' '+(form.dnatRules[di]?.internalPort||'') : vendor==='h3c' ? 'nat server protocol '+(form.dnatRules[di]?.protocol||'tcp')+' global current-interface '+(form.dnatRules[di]?.publicPort||'')+' inside '+(form.dnatRules[di]?.internalIp||'x.x.x.x')+' '+(form.dnatRules[di]?.internalPort||'') : vendor==='ruijie' ? 'ip nat inside source static '+(form.dnatRules[di]?.protocol||'tcp')+' '+(form.dnatRules[di]?.internalIp||'x.x.x.x')+' '+(form.dnatRules[di]?.internalPort||'')+' interface {WAN口} '+(form.dnatRules[di]?.publicPort||'') : 'ip nat inside source static '+(form.dnatRules[di]?.protocol||'tcp')+' '+(form.dnatRules[di]?.internalIp||'x.x.x.x')+' '+(form.dnatRules[di]?.internalPort||'')+' interface {WAN口} '+(form.dnatRules[di]?.publicPort||'') }}
              </div>
            </div>
            <el-button size="small" type="primary" plain @click="form.dnatRules.push({publicPort:0,internalIp:'',internalPort:0,protocol:'tcp',description:''});emitUpdate()" style="width:100%;margin-top:4px">+ 添加端口映射</el-button>
          </div>
        </div>
      </div>

      <!-- ═══ 第4步：DHCP ═══ -->
      <div class="step-section">
        <div class="step-number">4</div>
        <div class="step-content">
          <h4>DHCP 服务（自动分配 IP 给内网设备）</h4>
          <p class="step-desc">开启后，接入路由器的电脑/手机/WiFi 设备会自动获得 IP 地址，不用手动设置。家庭和企业网络都建议开启。</p>
          <el-switch v-model="form.dhcpEnabled" active-text="建议开启" size="large" />
          <template v-if="form.dhcpEnabled">
            <el-row :gutter="12" style="margin-top:12px">
              <el-col :span="6">
                <div class="field-with-help">
                  <label>LAN 接口 <el-tooltip content="连接内网的接口。华为/H3C通常是Vlanif1或Vlanif101" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.dhcpInterface" placeholder="Vlanif1" />
                </div>
              </el-col>
              <el-col :span="6">
                <div class="field-with-help">
                  <label>网段 <el-tooltip content="内网的网络地址，一般用192.168.1.0" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.dhcpNetwork" placeholder="192.168.1.0" />
                </div>
              </el-col>
              <el-col :span="4">
                <div class="field-with-help">
                  <label>掩码 <el-tooltip content="子网掩码，通常255.255.255.0代表254个可用IP" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.dhcpMask" placeholder="255.255.255.0" />
                </div>
              </el-col>
              <el-col :span="4">
                <div class="field-with-help">
                  <label>网关 <el-tooltip content="内网设备的默认网关，一般是这个接口的IP" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.dhcpGateway" placeholder="192.168.1.1" />
                </div>
              </el-col>
              <el-col :span="4">
                <div class="field-with-help">
                  <label>DNS <el-tooltip content="分配给内网设备的DNS服务器" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                  <el-input v-model="form.dhcpDns" placeholder="114.114.114.114" />
                </div>
              </el-col>
            </el-row>
          </template>
        </div>
      </div>

      <!-- ═══ 多线接入（高级）═══ -->
      <div class="step-section">
        <div class="step-number" style="background:#e6a23c">⚡</div>
        <div class="step-content">
          <h4>多线接入（高级，接入多条宽带时使用）</h4>
          <p class="step-desc">如果你有多条宽带（如电信+联通），可以在这里配置负载均衡。单线用户跳过。</p>
          <el-radio-group v-model="form.wanCount">
            <el-radio-button :value="1">单线（默认）</el-radio-button>
            <el-radio-button :value="2">双线</el-radio-button>
            <el-radio-button :value="3">三线</el-radio-button>
          </el-radio-group>
          <div v-if="form.wanCount > 1" style="margin-top:8px">
            <div v-for="i in form.wanCount" :key="'wan'+i" class="wan-line">
              <span style="font-weight:600;margin-right:8px">线路 {{ i }}</span>
              <el-input v-model="wanConfigs[i-1].interface" size="small" placeholder="接口" style="width:120px" />
              <el-input v-model="wanConfigs[i-1].gateway" size="small" placeholder="网关 IP" style="width:130px;margin-left:4px" />
              <el-input-number v-model="wanConfigs[i-1].weight" :min="1" :max="100" size="small" placeholder="权重" style="width:80px;margin-left:4px" />
              <el-input v-model="wanConfigs[i-1].description" size="small" placeholder="备注(电信)" style="width:80px;margin-left:4px" />
            </div>
          </div>
        </div>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any>; vendor?: string }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

const vendor = computed(() => props.vendor || 'huawei')
const vendorName = computed(() => {
  const m: Record<string,string> = { huawei:'华为 AR', h3c:'H3C MSR', ruijie:'锐捷 RSR', maipu:'迈普 MP' }
  return m[vendor.value] || vendor.value
})

const wanConfigs: Array<{interface:string;gateway:string;weight:number;description:string}> = reactive([
  { interface:'GE0/0/0', gateway:'', weight:1, description:'电信' },
  { interface:'GE0/0/1', gateway:'', weight:1, description:'联通' },
  { interface:'GE0/0/2', gateway:'', weight:1, description:'移动' },
])

const form = reactive({
  connectionType: 'pppoe' as 'static'|'pppoe'|'dhcp',
  pppoeUser: '', pppoePass: '', pppoePhysical: 'GigabitEthernet0/0/0', pppoeMtu: 1492,
  staticIp: '', staticMask: '', staticGateway: '', staticPhysical: 'GigabitEthernet0/0/0',
  dhcpPhysical: 'GigabitEthernet0/0/0',
  primaryDns: '', secondaryDns: '',
  natEnabled: true,
  dnatRules: [] as Array<{publicPort:number;internalIp:string;internalPort:number;protocol:string;description:string}>,
  wanCount: 1,
  dhcpEnabled: false,
  dhcpInterface: 'Vlanif1', dhcpNetwork: '192.168.1.0', dhcpMask: '255.255.255.0',
  dhcpGateway: '192.168.1.1', dhcpDns: '114.114.114.114', dhcpRangeStart: '192.168.1.100', dhcpRangeEnd: '192.168.1.200', dhcpLease: '1d',
})

/** 实时生成命令预览 */
const generatedPreview = computed(() => {
  const u = form.pppoeUser || '{宽带账号}'
  const pw = form.pppoePass || '{宽带密码}'
  const phy = form.pppoePhysical || 'GE0/0/0'

  if (form.connectionType === 'pppoe') {
    if (vendor.value === 'huawei') {
      return `acl number 2000\n rule 5 permit source 192.168.1.0 0.0.0.255\n\ninterface Dialer1\n link-protocol ppp\n ppp chap user ${u}\n ppp chap password simple ${pw}\n ip address ppp-negotiate\n dialer user ${u}\n dialer bundle 1\n dialer-group 1\n nat outbound 2000\n\ninterface ${phy}\n pppoe-client dial-bundle-number 1\n\nip route-static 0.0.0.0 0.0.0.0 Dialer1`
    }
    if (vendor.value === 'h3c') {
      return `dialer-group 1 rule ip permit\n\ninterface Dialer1\n dialer bundle enable\n dialer-group 1\n ip address ppp-negotiate\n ppp chap user ${u}\n ppp chap password simple ${pw}\n dialer timer idle 0\n nat outbound\n\ninterface ${phy}\n pppoe-client dial-bundle-number 1\n\nip route-static 0.0.0.0 0 Dialer 1`
    }
    if (vendor.value === 'ruijie') {
      return `interface ${phy}\n ip address pppoe-client\n pppoe-client dial-pool-number 1\n\ninterface Dialer 1\n ip address negotiated\n ppp authentication chap\n ppp chap hostname ${u}\n ppp chap password 0 ${pw}\n\nip route 0.0.0.0 0.0.0.0 Dialer 1`
    }
    if (vendor.value === 'maipu') {
      return `interface Dialer1\n encapsulation ppp\n ppp chap hostname ${u}\n ppp chap password 0 ${pw}\n ip address negotiated\n dialer pool 1\n\ninterface ${phy}\n pppoe-client dial-pool-number 1\n\nip route 0.0.0.0 0.0.0.0 Dialer1`
    }
  }

  if (form.connectionType === 'static') {
    const ip = form.staticIp || '{公网IP}'
    const mask = form.staticMask || '255.255.255.0'
    const gw = form.staticGateway || '{网关}'
    const iface = form.staticPhysical || 'GE0/0/0'
    if (vendor.value === 'huawei') return `interface ${iface}\n ip address ${ip} ${mask}\n nat outbound 2000\n\nip route-static 0.0.0.0 0.0.0.0 ${gw}`
    if (vendor.value === 'h3c') return `interface ${iface}\n ip address ${ip} ${mask}\n nat outbound\n\nip route-static 0.0.0.0 0 ${gw}`
    if (vendor.value === 'ruijie') return `interface ${iface}\n ip address ${ip} ${mask}\n ip nat outside\n\nip route 0.0.0.0 0.0.0.0 ${gw}`
    return `interface ${iface}\n ip address ${ip} ${mask}\n\nip route 0.0.0.0 0.0.0.0 ${gw}`
  }

  // DHCP
  const iface = form.dhcpPhysical || 'GE0/0/0'
  if (vendor.value === 'huawei') return `interface ${iface}\n ip address dhcp-alloc\n nat outbound 2000`
  if (vendor.value === 'h3c') return `interface ${iface}\n ip address dhcp-alloc\n nat outbound`
  if (vendor.value === 'ruijie') return `interface ${iface}\n ip address dhcp\n ip nat outside`
  return `interface ${iface}\n ip address dhcp-alloc`
})

function emitUpdate() {
  const params: Record<string, any> = { ...form }
  if (form.wanCount > 1) params.wanInterfaces = wanConfigs.slice(0, form.wanCount).map(w=>({...w}))
  emit('update:modelValue', params)
}

watch(() => props.modelValue, (v) => { if (v && Object.keys(v).length > 0) Object.assign(form, v) }, { immediate: true })
watch(form, () => emitUpdate(), { deep: true })
</script>

<style scoped>
.router-wan { max-width: 780px; }
.step-section { display:flex; gap:16px; margin-bottom:20px; padding:16px; background:#fafbfc; border-radius:10px; border:1px solid #e8ecf1; }
.step-number { width:36px; height:36px; min-width:36px; border-radius:50%; background:#409eff; color:#fff; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:700; }
.step-content { flex:1; }
.step-content h4 { margin:0 0 4px 0; font-size:15px; color:#303133; }
.step-desc { margin:0 0 4px 0; font-size:12px; color:#909399; line-height:1.6; }
.radio-label { display:block; font-size:14px; font-weight:600; }
.radio-desc { display:block; font-size:10px; color:#909399; margin-top:2px; }
.field-with-help { margin-bottom:4px; }
.field-with-help label { display:block; font-size:11px; color:#606266; margin-bottom:2px; font-weight:500; }
.help-icon { display:inline-flex; align-items:center; justify-content:center; width:16px; height:16px; border-radius:50%; background:#c0c4cc; color:#fff; font-size:10px; cursor:help; margin-left:4px; }
.mini-label { font-size:10px; color:#909399; display:block; margin-bottom:1px; }
.dnat-row { padding:10px; margin:8px 0; background:#fff; border-radius:6px; border:1px solid #ebeef5; }
.dnat-preview { margin-top:6px; font-family:'Consolas',monospace; font-size:11px; color:#67c23a; background:#f0f9eb; padding:4px 8px; border-radius:4px; }
.cmd-preview { margin-top:8px; padding:12px; background:#2d2d2d; color:#a6e22e; font-family:'Consolas',monospace; font-size:12px; line-height:1.5; border-radius:6px; white-space:pre; }
.wan-line { margin:4px 0; display:flex; align-items:center; }
</style>

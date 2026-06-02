<template>
  <div class="router-routing">
    <el-alert type="success" :closable="false" show-icon style="margin-bottom:16px">
      <template #title>📖 路由配置说明</template>
      出口路由器至少需要一条<b>默认路由</b>指向运营商网关。如果需要内网多网段互通，再加<b>静态路由</b>。大型网络再配 OSPF/BGP。
    </el-alert>

    <el-form label-width="110px" size="default" @change="emitUpdate">
      <!-- ═══ 默认路由 ═══ -->
      <div class="step-section">
        <div class="step-number">1</div>
        <div class="step-content">
          <h4>默认路由（上网必经之路）</h4>
          <p class="step-desc">告诉路由器：所有上网流量从这里出去。一般填运营商网关地址或 Dialer 接口。</p>
          <el-row :gutter="12" style="margin-top:8px">
            <el-col :span="10">
              <div class="field-with-help">
                <label>下一跳 IP <el-tooltip content="运营商网关地址。如果用PPPoE拨号，应该填 Dialer1 而不是IP" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                <el-input v-model="form.defaultNextHop" placeholder="例如：203.0.113.1 或 Dialer1" />
              </div>
            </el-col>
            <el-col :span="10">
              <div class="field-with-help">
                <label>出接口（可选）<el-tooltip content="可以不填IP，直接指定从哪个物理口出去" placement="top"><span class="help-icon">?</span></el-tooltip></label>
                <el-input v-model="form.defaultInterface" placeholder="GigabitEthernet0/0/0" />
              </div>
            </el-col>
          </el-row>
          <div class="cmd-hint">→ ip route-static 0.0.0.0 0.0.0.0 {{ form.defaultNextHop || '{下一跳}' }}</div>
        </div>
      </div>

      <!-- ═══ 静态路由 ═══ -->
      <div class="step-section">
        <div class="step-number">2</div>
        <div class="step-content">
          <h4>静态路由（网络互通）</h4>
          <p class="step-desc">内网有多个网段时，告诉路由器怎么找到对方。只有一个 192.168.1.x 网段？不用填，跳过就行。</p>
          <div v-for="(_, i) in form.staticRoutes" :key="'sr'+i" class="route-card">
            <el-row :gutter="6" align="middle">
              <el-col :span="6"><label class="mini-label">目的网络</label><el-input v-model="form.staticRoutes[i].dest_network" size="small" placeholder="192.168.2.0" /></el-col>
              <el-col :span="4"><label class="mini-label">掩码</label><el-input v-model="form.staticRoutes[i].mask" size="small" placeholder="255.255.255.0" /></el-col>
              <el-col :span="6"><label class="mini-label">下一跳</label><el-input v-model="form.staticRoutes[i].next_hop" size="small" placeholder="192.168.1.2" /></el-col>
              <el-col :span="4"><label class="mini-label">优先级</label><el-input-number v-model="form.staticRoutes[i].preference" :min="1" :max="255" size="small" style="width:100%" /></el-col>
              <el-col :span="3"><label class="mini-label">出接口(可选)</label><el-input v-model="form.staticRoutes[i].interface" size="small" /></el-col>
              <el-col :span="1"><el-button text type="danger" size="small" @click="form.staticRoutes.splice(i,1);emitUpdate()">✕</el-button></el-col>
            </el-row>
            <div class="cmd-hint">→ ip route-static {{ form.staticRoutes[i].dest_network||'{目的}' }} {{ form.staticRoutes[i].mask||'{掩码}' }} {{ form.staticRoutes[i].next_hop||'{下一跳}' }}</div>
          </div>
          <el-button size="small" type="primary" plain @click="form.staticRoutes.push({dest_network:'',mask:'255.255.255.0',next_hop:'',interface:'',preference:60});emitUpdate()" style="width:100%">+ 添加静态路由</el-button>
        </div>
      </div>

      <!-- ═══ OSPF ═══ -->
      <div class="step-section">
        <div class="step-number" style="background:#e6a23c">⚡</div>
        <div class="step-content">
          <h4>OSPF 动态路由（高级，大中型网络才用）</h4>
          <p class="step-desc">OSPF 让路由器自动学习网络拓扑。小型网络不需要，关掉即可。Router ID 通常填这台路由器的 Loopback 地址。</p>
          <el-switch v-model="form.ospfEnabled" active-text="启用 OSPF" size="large" />
          <template v-if="form.ospfEnabled">
            <el-row :gutter="12" style="margin-top:12px">
              <el-col :span="6"><label class="mini-label">进程ID</label><el-input-number v-model="form.ospfProcessId" :min="1" :max="65535" size="small" style="width:100%" /></el-col>
              <el-col :span="10"><label class="mini-label">Router ID <el-tooltip content="唯一标识这台路由器，一般用Loopback地址如1.1.1.1" placement="top"><span class="help-icon">?</span></el-tooltip></label><el-input v-model="form.ospfRouterId" size="small" placeholder="1.1.1.1" /></el-col>
              <el-col :span="6"><label class="mini-label">默认 Cost</label><el-input-number v-model="form.ospfCost" :min="1" :max="65535" size="small" style="width:100%" /></el-col>
            </el-row>
            <div v-for="(area, ai) in form.ospfAreas" :key="'area'+ai" class="route-card" style="margin-top:8px">
              <div class="card-header">
                <span class="card-title">区域 {{ area.area_id || '新' }}</span>
                <el-select v-model="form.ospfAreas[ai].type" size="small" style="width:100px"><el-option label="普通" value="normal" /><el-option label="Stub" value="stub" /><el-option label="NSSA" value="nssa" /></el-select>
                <el-input v-model="form.ospfAreas[ai].area_id" size="small" placeholder="区域ID" style="width:100px" />
                <el-button text type="danger" size="small" @click="form.ospfAreas.splice(ai,1);emitUpdate()" :disabled="form.ospfAreas.length<=1">删除</el-button>
              </div>
              <div v-for="(_, ni) in area.networks" :key="'net'+ni" class="route-row">
                <el-row :gutter="4" align="middle">
                  <el-col :span="8"><el-input v-model="area.networks[ni].address" size="small" placeholder="网段 10.0.0.0" /></el-col>
                  <el-col :span="5"><el-input v-model="area.networks[ni].mask" size="small" placeholder="通配符掩码" /></el-col>
                  <el-col :span="10"><el-input v-model="area.networks[ni].interface" size="small" placeholder="接口（可选）" /></el-col>
                  <el-col :span="1"><el-button text type="danger" size="small" @click="area.networks.splice(ni,1);emitUpdate()">✕</el-button></el-col>
                </el-row>
              </div>
              <el-button size="small" text type="primary" @click="area.networks.push({address:'',mask:'0.0.0.255',interface:''});emitUpdate()">+ 添加网段</el-button>
            </div>
            <el-button size="small" type="primary" plain @click="form.ospfAreas.push({area_id:'0',type:'normal',networks:[{address:'',mask:'0.0.0.255',interface:''}]});emitUpdate()" style="width:100%;margin-top:4px">+ 添加区域</el-button>
          </template>
        </div>
      </div>

      <!-- ═══ BGP ═══ -->
      <div class="step-section">
        <div class="step-number" style="background:#e6a23c">⚡</div>
        <div class="step-content">
          <h4>BGP 边界网关协议（高级，运营商互联才用）</h4>
          <p class="step-desc">用于不同自治系统之间交换路由。普通企业网络不需要，关闭即可。AS 号需要向 CNNIC 申请。</p>
          <el-switch v-model="form.bgpEnabled" active-text="启用 BGP" size="large" />
          <template v-if="form.bgpEnabled">
            <el-row :gutter="12" style="margin-top:12px">
              <el-col :span="8"><label class="mini-label">AS 号</label><el-input-number v-model="form.bgpAsNumber" :min="1" :max="4294967295" size="small" style="width:100%" /></el-col>
              <el-col :span="10"><label class="mini-label">Router ID</label><el-input v-model="form.bgpRouterId" size="small" placeholder="1.1.1.1" /></el-col>
            </el-row>
            <div style="margin-top:8px">
              <label class="mini-label">BGP 邻居（运营商给你的对端地址和AS号）</label>
              <div v-for="(_, pi) in form.bgpPeers" :key="'peer'+pi" class="route-row">
                <el-row :gutter="4" align="middle">
                  <el-col :span="8"><el-input v-model="form.bgpPeers[pi].ip" size="small" placeholder="邻居 IP" /></el-col>
                  <el-col :span="6"><el-input-number v-model="form.bgpPeers[pi].as" :min="1" size="small" style="width:100%" /></el-col>
                  <el-col :span="9"><el-input v-model="form.bgpPeers[pi].description" size="small" placeholder="描述" /></el-col>
                  <el-col :span="1"><el-button text type="danger" size="small" @click="form.bgpPeers.splice(pi,1);emitUpdate()">✕</el-button></el-col>
                </el-row>
              </div>
              <el-button size="small" type="primary" plain @click="form.bgpPeers.push({ip:'',as:65002,description:''});emitUpdate()" style="width:100%">+ 添加邻居</el-button>
            </div>
          </template>
        </div>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

const form = reactive({
  defaultNextHop: '', defaultInterface: '',
  staticRoutes: [] as Array<{dest_network:string;mask:string;next_hop:string;interface:string;preference:number}>,
  ospfEnabled: false, ospfProcessId: 1, ospfRouterId: '', ospfCost: 10,
  ospfAreas: [{ area_id:'0', type:'normal', networks: [{address:'',mask:'0.0.0.255',interface:''}] }],
  ospfInterfaces: [] as Array<{interface:string;cost:number;priority:number;hello_time:number;dead_time:number}>,
  bgpEnabled: false, bgpAsNumber: 65001, bgpRouterId: '',
  bgpPeers: [] as Array<{ip:string;as:number;description:string}>,
  bgpNetworks: [] as string[], bgpImportRoutes: [] as string[],
})

function emitUpdate() {
  const params: Record<string, any> = {}
  if (form.staticRoutes.length > 0) params.static_routes = [...form.staticRoutes]
  if (form.defaultNextHop||form.defaultInterface) params.default_route = {next_hop:form.defaultNextHop,interface:form.defaultInterface}
  if (form.ospfEnabled) {
    const allNets: Array<{address:string;mask:string;interface:string}> = []
    form.ospfAreas.forEach(a=>allNets.push(...a.networks.filter(n=>n.address)))
    params.ospf = {process_id:form.ospfProcessId,router_id:form.ospfRouterId,area_id:form.ospfAreas[0]?.area_id||'0',networks:allNets,cost:form.ospfCost}
    if (form.ospfInterfaces.length>0) params.ospf_interfaces = [...form.ospfInterfaces]
  }
  if (form.bgpEnabled) params.bgp = {as_number:form.bgpAsNumber,router_id:form.bgpRouterId,peers:form.bgpPeers.filter(p=>p.ip),networks:form.bgpNetworks.filter(n=>n),import_routes:form.bgpImportRoutes}
  emit('update:modelValue', params)
}

watch(() => props.modelValue, (v) => {
  if (v && Object.keys(v).length > 0) Object.assign(form, v)
  if (v.default_route) { form.defaultNextHop=v.default_route.next_hop||''; form.defaultInterface=v.default_route.interface||'' }
  if (v.ospf) { form.ospfEnabled=true; form.ospfProcessId=v.ospf.process_id||1; form.ospfRouterId=v.ospf.router_id||'' }
  if (v.bgp) { form.bgpEnabled=true; form.bgpAsNumber=v.bgp.as_number||65001; form.bgpRouterId=v.bgp.router_id||'' }
}, { immediate: true })

watch(form, () => emitUpdate(), { deep: true })
</script>

<style scoped>
.router-routing { max-width: 780px; }
.step-section { display:flex; gap:16px; margin-bottom:20px; padding:16px; background:#fafbfc; border-radius:10px; border:1px solid #e8ecf1; }
.step-number { width:36px; height:36px; min-width:36px; border-radius:50%; background:#409eff; color:#fff; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:700; }
.step-content { flex:1; }
.step-content h4 { margin:0 0 4px 0; font-size:15px; color:#303133; }
.step-desc { margin:0 0 4px 0; font-size:12px; color:#909399; line-height:1.6; }
.field-with-help label { display:block; font-size:11px; color:#606266; margin-bottom:2px; font-weight:500; }
.help-icon { display:inline-flex; align-items:center; justify-content:center; width:16px; height:16px; border-radius:50%; background:#c0c4cc; color:#fff; font-size:10px; cursor:help; margin-left:4px; }
.mini-label { font-size:10px; color:#909399; display:block; margin-bottom:2px; }
.route-card { border:1px solid #e8ecf1; border-radius:8px; padding:10px; margin-bottom:8px; background:#fff; }
.route-row { margin-bottom:4px; padding:4px 6px; background:#fff; border-radius:4px; border:1px solid #ebeef5; }
.card-header { display:flex; gap:8px; align-items:center; margin-bottom:6px; }
.card-title { font-size:13px; font-weight:600; color:#303133; }
.cmd-hint { margin-top:4px; font-family:'Consolas',monospace; font-size:11px; color:#67c23a; background:#f0f9eb; padding:4px 8px; border-radius:4px; }
</style>

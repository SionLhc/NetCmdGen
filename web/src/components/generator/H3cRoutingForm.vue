<template>
  <div class="router-routing">
    <el-alert type="success" :closable="false" show-icon style="margin-bottom:16px">
      <template #title>📖 H3C 路由配置</template>
      出口路由器至少需要一条<b>默认路由</b>。内网多网段加<b>静态路由</b>，大型网络开 OSPF/BGP。
    </el-alert>
    <el-form label-width="110px" size="default" @change="emitUpdate">
      <!-- 默认路由 -->
      <div class="step-section"><div class="step-number">1</div><div class="step-content">
        <h4>默认路由</h4><p class="step-desc">所有上网流量走这个出口。用 PPPoE 的话填 Dialer 1。</p>
        <div class="field-with-help" style="width:300px;margin-top:8px">
          <label>下一跳 <el-tooltip content="运营商网关IP或用Dialer 1" placement="top"><span class="help-icon">?</span></el-tooltip></label>
          <el-input v-model="form.defaultNextHop" placeholder="203.0.113.1 或 Dialer 1" />
        </div>
        <div class="cmd-hint">→ ip route-static 0.0.0.0 0 {{ form.defaultNextHop || '{下一跳}' }}</div>
      </div></div>

      <!-- 静态路由 -->
      <div class="step-section"><div class="step-number">2</div><div class="step-content">
        <h4>静态路由</h4><p class="step-desc">内网多网段互通用，只有一个网段不用配。</p>
        <div v-for="(_, i) in form.staticRoutes" :key="'sr'+i" class="route-card">
          <el-row :gutter="4" align="middle">
            <el-col :span="6"><label class="mini-label">目的网络</label><el-input v-model="form.staticRoutes[i].destination" size="small" /></el-col>
            <el-col :span="4"><label class="mini-label">掩码</label><el-input v-model="form.staticRoutes[i].mask" size="small" /></el-col>
            <el-col :span="6"><label class="mini-label">下一跳</label><el-input v-model="form.staticRoutes[i].next_hop" size="small" /></el-col>
            <el-col :span="4"><label class="mini-label">优先级</label><el-input-number v-model="form.staticRoutes[i].preference" :min="1" :max="255" size="small" style="width:100%" /></el-col>
            <el-col :span="3"><label class="mini-label">描述</label><el-input v-model="form.staticRoutes[i].description" size="small" /></el-col>
            <el-col :span="1"><el-button text type="danger" size="small" @click="form.staticRoutes.splice(i,1);emitUpdate()">✕</el-button></el-col>
          </el-row>
          <div class="cmd-hint">→ ip route-static {{ form.staticRoutes[i].destination||'{目的}' }} {{ form.staticRoutes[i].mask||'{掩码}' }} {{ form.staticRoutes[i].next_hop||'{下一跳}' }}</div>
        </div>
        <el-button size="small" type="primary" plain @click="form.staticRoutes.push({destination:'',mask:'255.255.255.0',next_hop:'',preference:60,description:''});emitUpdate()" style="width:100%">+ 添加静态路由</el-button>
      </div></div>

      <!-- OSPF -->
      <div class="step-section"><div class="step-number" style="background:#e6a23c">⚡</div><div class="step-content">
        <h4>OSPF（高级，大中型网络用）</h4>
        <el-switch v-model="form.ospfEnabled" active-text="启用 OSPF" size="large" />
        <template v-if="form.ospfEnabled">
          <el-row :gutter="12" style="margin-top:12px">
            <el-col :span="6"><label class="mini-label">进程ID</label><el-input-number v-model="form.ospfProcessId" :min="1" :max="65535" size="small" style="width:100%" /></el-col>
            <el-col :span="10"><label class="mini-label">Router ID</label><el-input v-model="form.ospfRouterId" size="small" placeholder="1.1.1.1" /></el-col>
            <el-col :span="8"><label class="mini-label">区域ID</label><el-input v-model="form.ospfAreaId" size="small" placeholder="0" /></el-col>
          </el-row>
          <div v-for="(_, ni) in form.ospfNetworks" :key="'on'+ni" class="route-row" style="margin-top:6px">
            <el-row :gutter="4" align="middle">
              <el-col :span="9"><el-input v-model="form.ospfNetworks[ni].address" size="small" placeholder="网段" /></el-col>
              <el-col :span="7"><el-input v-model="form.ospfNetworks[ni].mask" size="small" placeholder="通配符掩码" /></el-col>
              <el-col :span="7"><el-input v-model="form.ospfNetworks[ni].description" size="small" placeholder="备注" /></el-col>
              <el-col :span="1"><el-button text type="danger" size="small" @click="form.ospfNetworks.splice(ni,1);emitUpdate()">✕</el-button></el-col>
            </el-row>
          </div>
          <el-button size="small" type="primary" plain @click="form.ospfNetworks.push({address:'',mask:'0.0.0.255',description:''});emitUpdate()" style="width:100%">+ 宣告网段</el-button>
        </template>
      </div></div>

      <!-- BGP -->
      <div class="step-section"><div class="step-number" style="background:#e6a23c">⚡</div><div class="step-content">
        <h4>BGP（高级，运营商互联用）</h4>
        <el-switch v-model="form.bgpEnabled" active-text="启用 BGP" size="large" />
        <template v-if="form.bgpEnabled">
          <el-row :gutter="12" style="margin-top:12px">
            <el-col :span="8"><label class="mini-label">AS 号</label><el-input-number v-model="form.bgpAsNumber" :min="1" size="small" style="width:100%" /></el-col>
            <el-col :span="10"><label class="mini-label">Router ID</label><el-input v-model="form.bgpRouterId" size="small" placeholder="1.1.1.1" /></el-col>
          </el-row>
          <div v-for="(_, pi) in form.bgpNeighbors" :key="'bp'+pi" class="route-row" style="margin-top:6px">
            <el-row :gutter="4" align="middle">
              <el-col :span="9"><el-input v-model="form.bgpNeighbors[pi].ip" size="small" placeholder="邻居 IP" /></el-col>
              <el-col :span="6"><el-input-number v-model="form.bgpNeighbors[pi].remote_as" :min="1" size="small" style="width:100%" /></el-col>
              <el-col :span="8"><el-input v-model="form.bgpNeighbors[pi].description" size="small" placeholder="描述" /></el-col>
              <el-col :span="1"><el-button text type="danger" size="small" @click="form.bgpNeighbors.splice(pi,1);emitUpdate()">✕</el-button></el-col>
            </el-row>
          </div>
          <el-button size="small" type="primary" plain @click="form.bgpNeighbors.push({ip:'',remote_as:65002,description:''});emitUpdate()" style="width:100%">+ 添加邻居</el-button>
        </template>
      </div></div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()
const form = reactive({
  defaultNextHop: '', defaultPreference: 60,
  staticRoutes: [] as Array<{destination:string;mask:string;next_hop:string;preference:number;description:string}>,
  ospfEnabled: false, ospfProcessId: 1, ospfRouterId: '', ospfAreaId: '0',
  ospfNetworks: [] as Array<{address:string;mask:string;description:string}>,
  bgpEnabled: false, bgpAsNumber: 65001, bgpRouterId: '',
  bgpNeighbors: [] as Array<{ip:string;remote_as:number;description:string}>,
  bgpNetworks: [] as Array<{address:string;mask_length:number;description:string}>,
  vrrpGroups: [] as Array<{interface:string;vrid:number;virtual_ip:string;priority:number}>,
})
function emitUpdate() {
  const params: Record<string, any> = {}
  if (form.defaultNextHop) params.default = { next_hop: form.defaultNextHop, preference: form.defaultPreference }
  if (form.staticRoutes.length > 0) params.static = form.staticRoutes.filter(r=>r.destination&&r.next_hop)
  if (form.ospfEnabled) params.ospf = { process_id: form.ospfProcessId, router_id: form.ospfRouterId, area_id: form.ospfAreaId, networks: form.ospfNetworks.filter(n=>n.address) }
  if (form.bgpEnabled) params.bgp = { as_number: form.bgpAsNumber, router_id: form.bgpRouterId, neighbors: form.bgpNeighbors.filter(p=>p.ip), networks: form.bgpNetworks.filter(n=>n.address) }
  if (form.vrrpGroups.length > 0) params.vrrp = [...form.vrrpGroups]
  emit('update:modelValue', params)
}
watch(() => props.modelValue, (v) => {
  if (v && Object.keys(v).length > 0) Object.assign(form, v)
  if (v.default) { form.defaultNextHop = v.default.next_hop||'' }
  if (v.ospf) { form.ospfEnabled = true; form.ospfProcessId = v.ospf.process_id||1; form.ospfRouterId = v.ospf.router_id||'' }
  if (v.bgp) { form.bgpEnabled = true; form.bgpAsNumber = v.bgp.as_number||65001 }
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
.route-card { border:1px solid #e8ecf1; border-radius:8px; padding:8px; margin-bottom:8px; background:#fff; }
.route-row { margin-bottom:4px; padding:4px 6px; background:#fff; border-radius:4px; border:1px solid #ebeef5; }
.cmd-hint { margin-top:4px; font-family:'Consolas',monospace; font-size:11px; color:#67c23a; background:#f0f9eb; padding:4px 8px; border-radius:4px; }
</style>

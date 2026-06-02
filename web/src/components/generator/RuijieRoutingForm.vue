<template>
  <div class="router-routing">
    <el-alert type="success" :closable="false" show-icon style="margin-bottom:16px">
      <template #title>📖 锐捷 RSR 路由配置</template>
      出口路由器至少配<b>静态路由</b>（默认+回程），大型网络开 OSPF/BGP。
    </el-alert>
    <el-form label-width="110px" size="default" @change="emitUpdate">
      <div class="step-section"><div class="step-number">1</div><div class="step-content">
        <h4>静态路由</h4><p class="step-desc">第1条通常是默认路由（0.0.0.0 → 下一跳），再加内网回程路由。</p>
        <div v-for="(_, i) in form.staticRoutes" :key="'sr'+i" class="route-card">
          <el-row :gutter="4" align="middle">
            <el-col :span="6"><label class="mini-label">目的</label><el-input v-model="form.staticRoutes[i].dest" size="small" placeholder="0.0.0.0（默认）" /></el-col>
            <el-col :span="4"><label class="mini-label">掩码</label><el-input v-model="form.staticRoutes[i].mask" size="small" placeholder="0.0.0.0" /></el-col>
            <el-col :span="5"><label class="mini-label">下一跳</label><el-input v-model="form.staticRoutes[i].nexthop" size="small" placeholder="203.0.113.1" /></el-col>
            <el-col :span="3"><label class="mini-label">距离</label><el-input-number v-model="form.staticRoutes[i].distance" :min="1" :max="255" size="small" style="width:100%" /></el-col>
            <el-col :span="5"><label class="mini-label">备注</label><el-input v-model="form.staticRoutes[i].description" size="small" /></el-col>
            <el-col :span="1"><el-button text type="danger" size="small" @click="form.staticRoutes.splice(i,1);emitUpdate()">✕</el-button></el-col>
          </el-row>
          <div class="cmd-hint">→ ip route {{ form.staticRoutes[i].dest||'{目的}' }} {{ form.staticRoutes[i].mask||'{掩码}' }} {{ form.staticRoutes[i].nexthop||'{下一跳}' }}</div>
        </div>
        <el-button size="small" type="primary" plain @click="form.staticRoutes.push({dest:'',mask:'255.255.255.0',nexthop:'',distance:1,description:''});emitUpdate()" style="width:100%">+ 添加静态路由</el-button>
      </div></div>
      <div class="step-section"><div class="step-number" style="background:#e6a23c">⚡</div><div class="step-content">
        <h4>OSPF（高级）</h4><el-switch v-model="form.ospfEnabled" active-text="启用" size="large" />
        <template v-if="form.ospfEnabled">
          <el-row :gutter="12" style="margin-top:12px">
            <el-col :span="6"><label class="mini-label">进程ID</label><el-input-number v-model="form.ospfProcessId" :min="1" :max="65535" size="small" style="width:100%" /></el-col>
            <el-col :span="10"><label class="mini-label">Router ID</label><el-input v-model="form.ospfRouterId" size="small" placeholder="1.1.1.1" /></el-col>
          </el-row>
          <div v-for="(_, ni) in form.ospfNetworks" :key="'on'+ni" class="route-row" style="margin-top:6px">
            <el-row :gutter="4" align="middle">
              <el-col :span="8"><el-input v-model="form.ospfNetworks[ni].address" size="small" placeholder="网段" /></el-col>
              <el-col :span="7"><el-input v-model="form.ospfNetworks[ni].mask" size="small" placeholder="通配符掩码" /></el-col>
              <el-col :span="7"><el-input v-model="form.ospfNetworks[ni].area" size="small" placeholder="区域" /></el-col>
              <el-col :span="1"><el-button text type="danger" size="small" @click="form.ospfNetworks.splice(ni,1);emitUpdate()">✕</el-button></el-col>
            </el-row>
          </div>
          <el-button size="small" type="primary" plain @click="form.ospfNetworks.push({address:'',mask:'0.0.0.255',area:'0'});emitUpdate()" style="width:100%">+ 宣告网段</el-button>
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
  staticRoutes: [] as Array<{dest:string;mask:string;nexthop:string;distance:number;description:string}>,
  ospfEnabled: false, ospfProcessId: 1, ospfRouterId: '',
  ospfNetworks: [] as Array<{address:string;mask:string;area:string}>,
})
function emitUpdate() {
  const params: Record<string, any> = {}
  if (form.staticRoutes.length > 0) params.static_routes = form.staticRoutes.filter(r=>r.dest&&r.nexthop)
  if (form.ospfEnabled) params.ospf = { process_id: form.ospfProcessId, router_id: form.ospfRouterId, networks: form.ospfNetworks.filter(n=>n.address) }
  emit('update:modelValue', params)
}
watch(() => props.modelValue, (v) => { if (v && Object.keys(v).length > 0) Object.assign(form, v); if (v.ospf) { form.ospfEnabled=true } }, { immediate: true })
watch(form, () => emitUpdate(), { deep: true })
</script>

<style scoped>
.router-routing { max-width: 780px; }
.step-section { display:flex; gap:16px; margin-bottom:20px; padding:16px; background:#fafbfc; border-radius:10px; border:1px solid #e8ecf1; }
.step-number { width:36px; height:36px; min-width:36px; border-radius:50%; background:#409eff; color:#fff; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:700; }
.step-content { flex:1; }
.step-content h4 { margin:0 0 4px 0; font-size:15px; color:#303133; }
.step-desc { margin:0 0 4px 0; font-size:12px; color:#909399; line-height:1.6; }
.mini-label { font-size:10px; color:#909399; display:block; margin-bottom:2px; }
.route-card { border:1px solid #e8ecf1; border-radius:8px; padding:8px; margin-bottom:8px; background:#fff; }
.route-row { margin-bottom:4px; padding:4px 6px; background:#fff; border-radius:4px; border:1px solid #ebeef5; }
.cmd-hint { margin-top:4px; font-family:'Consolas',monospace; font-size:11px; color:#67c23a; background:#f0f9eb; padding:4px 8px; border-radius:4px; }
</style>

<template>
  <el-form label-width="90px" size="small" @change="emitUpdate">
    <!-- 静态路由 -->
    <el-divider content-position="left">静态路由</el-divider>
    <div v-for="(r, idx) in staticRoutes" :key="'sr'+idx" class="route-row">
      <el-row :gutter="4">
        <el-col :span="10"><el-input v-model="r.dest" placeholder="目的网络" /></el-col>
        <el-col :span="6"><el-input v-model="r.mask" placeholder="掩码" /></el-col>
        <el-col :span="6"><el-input v-model="r.nexthop" placeholder="下一跳" /></el-col>
        <el-col :span="2"><el-button text type="danger" @click="staticRoutes.splice(idx,1);emitUpdate()">✕</el-button></el-col>
      </el-row>
    </div>
    <el-button size="small" plain @click="staticRoutes.push({dest:'',mask:'255.255.255.0',nexthop:''});emitUpdate()" style="width:100%">+ 添加静态路由</el-button>

    <!-- OSPF -->
    <el-divider content-position="left">OSPF</el-divider>
    <el-form-item label="启用 OSPF">
      <el-switch v-model="enableOspf" @change="emitUpdate" />
    </el-form-item>
    <template v-if="enableOspf">
      <el-form-item label="进程 ID">
        <el-input-number v-model="ospf.process_id" :min="1" :max="65535" @change="emitUpdate" />
      </el-form-item>
      <el-form-item label="Router ID">
        <el-input v-model="ospf.router_id" placeholder="1.1.1.1" @change="emitUpdate" />
      </el-form-item>
      <el-form-item label="区域 ID">
        <el-input v-model="ospf.area_id" placeholder="0" @change="emitUpdate" />
      </el-form-item>
      <div v-for="(n, idx) in ospfNetworks" :key="'on'+idx" class="route-row">
        <el-row :gutter="4">
          <el-col :span="7"><el-input v-model="n.network" placeholder="网段" @change="emitUpdate" /></el-col>
          <el-col :span="7"><el-input v-model="n.wildcard" placeholder="通配符" @change="emitUpdate" /></el-col>
          <el-col :span="7"><el-input v-model="n.area" placeholder="区域" @change="emitUpdate" /></el-col>
          <el-col :span="3"><el-button text type="danger" @click="ospfNetworks.splice(idx,1);emitUpdate()">✕</el-button></el-col>
        </el-row>
      </div>
      <el-button size="small" plain @click="ospfNetworks.push({network:'',wildcard:'0.0.0.255',area:'0'});emitUpdate()" style="width:100%">+ 添加网段</el-button>
    </template>

    <!-- BGP -->
    <el-divider content-position="left">BGP</el-divider>
    <el-form-item label="启用 BGP">
      <el-switch v-model="enableBgp" @change="emitUpdate" />
    </el-form-item>
    <template v-if="enableBgp">
      <el-form-item label="AS 号">
        <el-input-number v-model="bgp.as_number" :min="1" :max="4294967295" @change="emitUpdate" />
      </el-form-item>
      <el-form-item label="Router ID">
        <el-input v-model="bgp.router_id" placeholder="1.1.1.1" @change="emitUpdate" />
      </el-form-item>
      <div v-for="(p, idx) in bgpPeers" :key="'bp'+idx" class="route-row">
        <el-row :gutter="4">
          <el-col :span="10"><el-input v-model="p.ip" placeholder="邻居 IP" @change="emitUpdate" /></el-col>
          <el-col :span="10"><el-input-number v-model="p.remote_as" :min="1" placeholder="远端 AS" @change="emitUpdate" /></el-col>
          <el-col :span="4"><el-button text type="danger" @click="bgpPeers.splice(idx,1);emitUpdate()">✕</el-button></el-col>
        </el-row>
      </div>
      <el-button size="small" plain @click="bgpPeers.push({ip:'',remote_as:65001});emitUpdate()" style="width:100%">+ 添加 BGP 邻居</el-button>
    </template>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const enableOspf = ref(!!props.modelValue.ospf)
const enableBgp = ref(!!props.modelValue.bgp)

const staticRoutes = reactive<Array<{dest:string;mask:string;nexthop:string}>>(
    props.modelValue.static_routes || []
)
const ospf = reactive(props.modelValue.ospf || { process_id: 1, router_id: '', area_id: '0' })
const ospfNetworks = reactive<Array<{network:string;wildcard:string;area:string}>>(
    props.modelValue.ospf?.networks || []
)
const bgp = reactive(props.modelValue.bgp || { as_number: 65001, router_id: '' })
const bgpPeers = reactive<Array<{ip:string;remote_as:number}>>(
    props.modelValue.bgp?.peers || []
)

function emitUpdate() {
    const params: Record<string, any> = {}
    if (staticRoutes.length > 0) params.static_routes = [...staticRoutes]
    if (enableOspf.value) {
        params.ospf = { ...ospf, networks: [...ospfNetworks] }
    }
    if (enableBgp.value) {
        params.bgp = { ...bgp, peers: [...bgpPeers] }
    }
    emit('update:modelValue', params)
}

watch([staticRoutes, ospfNetworks, bgpPeers], emitUpdate, { deep: true })
</script>

<style scoped>
.route-row { margin-bottom: 6px; padding: 6px; background: #fff; border-radius: 4px; border: 1px solid #f0f0f0; }
</style>

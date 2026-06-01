<template>
  <el-form label-width="90px" size="small" @change="emitUpdate">
    <!-- DHCP Server -->
    <el-divider content-position="left">DHCP Server</el-divider>
    <el-form-item label="启用 DHCP">
      <el-switch v-model="enableDhcp" @change="emitUpdate" />
    </el-form-item>
    <div v-for="(pool, idx) in dhcpPools" :key="'dp'+idx" class="sec-section">
      <div class="sec-header">
        <span>地址池: {{ pool.name || '(未命名)' }}</span>
        <el-button text type="danger" size="small" @click="dhcpPools.splice(idx,1);emitUpdate()">删除</el-button>
      </div>
      <el-form-item label="池名称" label-width="70px">
        <el-input v-model="pool.name" size="small" placeholder="vlan10-pool" @change="emitUpdate" />
      </el-form-item>
      <el-form-item label="网段" label-width="70px">
        <el-input v-model="pool.network" size="small" placeholder="192.168.1.0" @change="emitUpdate" />
      </el-form-item>
      <el-form-item label="掩码" label-width="70px">
        <el-input v-model="pool.mask" size="small" placeholder="255.255.255.0" @change="emitUpdate" />
      </el-form-item>
      <el-form-item label="网关" label-width="70px">
        <el-input v-model="pool.default_router" size="small" placeholder="192.168.1.1" @change="emitUpdate" />
      </el-form-item>
      <el-form-item label="DNS" label-width="70px">
        <el-input v-model="pool.dnsInput" size="small" placeholder="8.8.8.8, 114.114.114.114" @change="onDnsChange(pool)" />
      </el-form-item>
    </div>
    <el-button size="small" plain @click="dhcpPools.push({name:'',network:'',mask:'255.255.255.0',default_router:'',dns_servers:[],dnsInput:''});emitUpdate()" style="width:100%">+ 添加地址池</el-button>

    <!-- DHCP Snooping -->
    <el-divider content-position="left">DHCP Snooping</el-divider>
    <el-form-item label="启用 Snooping">
      <el-switch v-model="dhcpSnooping.enable" @change="emitUpdate" />
    </el-form-item>
    <template v-if="dhcpSnooping.enable">
      <el-form-item label="信任端口">
        <el-input v-model="trustedPortsStr" placeholder="G0/0/1, G0/0/2" @change="onTrustedChange" />
      </el-form-item>
    </template>

    <!-- DHCP Relay -->
    <el-divider content-position="left">DHCP Relay</el-divider>
    <div v-for="(r, idx) in dhcpRelay" :key="'dr'+idx" class="sec-section">
      <el-row :gutter="6">
        <el-col :span="10"><el-input v-model="r.name" placeholder="接口名" @change="emitUpdate" /></el-col>
        <el-col :span="10"><el-input v-model="r.server_ip" placeholder="DHCP服务器IP" @change="emitUpdate" /></el-col>
        <el-col :span="4"><el-button text type="danger" @click="dhcpRelay.splice(idx,1);emitUpdate()">✕</el-button></el-col>
      </el-row>
    </div>
    <el-button size="small" plain @click="dhcpRelay.push({name:'',server_ip:''});emitUpdate()" style="width:100%">+ 添加 Relay</el-button>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const enableDhcp = ref(props.modelValue.dhcp_server != null)
const trustedPortsStr = ref('')

const dhcpPools = reactive<Array<any>>(props.modelValue.dhcp_server?.pools || [])
const dhcpSnooping = reactive(props.modelValue.dhcp_snooping || { enable: false, trusted_ports: [] })
const dhcpRelay = reactive<Array<any>>(props.modelValue.dhcp_relay?.interfaces || [])

function onDnsChange(pool: any) {
    pool.dns_servers = pool.dnsInput.split(',').map((s: string) => s.trim()).filter(Boolean)
    emitUpdate()
}

function onTrustedChange() {
    dhcpSnooping.trusted_ports = trustedPortsStr.value.split(',').map((s: string) => s.trim()).filter(Boolean)
    emitUpdate()
}

function emitUpdate() {
    const params: Record<string, any> = {}
    if (enableDhcp.value && dhcpPools.length > 0) {
        params.dhcp_server = { pools: dhcpPools.map(p => ({
            name: p.name,
            network: p.network,
            mask: p.mask,
            default_router: p.default_router,
            dns_servers: p.dns_servers,
        }))}
    }
    if (dhcpSnooping.enable) {
        params.dhcp_snooping = { enable: true, trusted_ports: [...dhcpSnooping.trusted_ports] }
    }
    if (dhcpRelay.length > 0) {
        params.dhcp_relay = { interfaces: [...dhcpRelay] }
    }
    emit('update:modelValue', params)
}

watch([dhcpPools, dhcpSnooping, dhcpRelay], emitUpdate, { deep: true })
</script>

<style scoped>
.sec-section { margin-bottom: 10px; padding: 8px; background: #fff; border-radius: 6px; border: 1px solid #ebeef5; }
.sec-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 12px; color: #606266; }
</style>

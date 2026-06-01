<template>
  <el-form label-width="90px" size="small" @change="emitUpdate">
    <!-- ACL -->
    <el-divider content-position="left">ACL 规则</el-divider>
    <div v-for="(acl, aclIdx) in acls" :key="'acl'+aclIdx" class="sec-section">
      <div class="sec-header">
        <span>ACL #{{ acl.number }}</span>
        <el-button text type="danger" size="small" @click="acls.splice(aclIdx,1);emitUpdate()">删除</el-button>
      </div>
      <el-row :gutter="6">
        <el-col :span="8"><el-input-number v-model="acl.number" :min="100" :max="3999" @change="emitUpdate" /></el-col>
        <el-col :span="16"><el-input v-model="acl.description" placeholder="描述" @change="emitUpdate" /></el-col>
      </el-row>
      <div v-for="(rule, idx) in acl.rules" :key="'ar'+idx" class="rule-row">
        <el-row :gutter="3">
          <el-col :span="6">
            <el-select v-model="rule.action" @change="emitUpdate">
              <el-option label="放行" value="permit" />
              <el-option label="拒绝" value="deny" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select v-model="rule.protocol" @change="emitUpdate">
              <el-option label="IP" value="ip" />
              <el-option label="TCP" value="tcp" />
              <el-option label="UDP" value="udp" />
              <el-option label="ICMP" value="icmp" />
            </el-select>
          </el-col>
          <el-col :span="8"><el-input v-model="rule.source" placeholder="源 IP" @change="emitUpdate" /></el-col>
          <el-col :span="2"><el-button text type="danger" size="small" @click="acl.rules.splice(idx,1);emitUpdate()">✕</el-button></el-col>
        </el-row>
      </div>
      <el-button size="small" plain @click="acl.rules.push({action:'permit',protocol:'ip',source:'any'});emitUpdate()" style="width:100%">+ 添加规则</el-button>
    </div>
    <el-button size="small" plain @click="acls.push({number:2000,rules:[{action:'permit',protocol:'ip',source:'any'}],description:''});emitUpdate()" style="width:100%">+ 添加 ACL</el-button>

    <!-- 端口安全 -->
    <el-divider content-position="left">端口安全</el-divider>
    <div v-for="(ps, idx) in portSecurity" :key="'ps'+idx" class="sec-section">
      <div class="sec-header">
        <span>端口安全</span>
        <el-button text type="danger" size="small" @click="portSecurity.splice(idx,1);emitUpdate()">删除</el-button>
      </div>
      <el-row :gutter="6">
        <el-col :span="10"><el-input v-model="ps.interface" placeholder="接口" @change="emitUpdate" /></el-col>
        <el-col :span="6"><el-input-number v-model="ps.max_mac" :min="1" :max="256" @change="emitUpdate" /></el-col>
        <el-col :span="8">
          <el-select v-model="ps.violation" @change="emitUpdate">
            <el-option label="protect" value="protect" />
            <el-option label="shutdown" value="shutdown" />
          </el-select>
        </el-col>
      </el-row>
      <el-checkbox v-model="ps.sticky" @change="emitUpdate">Sticky MAC</el-checkbox>
    </div>
    <el-button size="small" plain @click="portSecurity.push({interface:'',max_mac:1,violation:'protect',sticky:false});emitUpdate()" style="width:100%">+ 添加端口安全</el-button>

    <!-- 流量过滤 -->
    <el-divider content-position="left">流量过滤</el-divider>
    <div v-for="(tf, idx) in trafficFilters" :key="'tf'+idx" class="sec-section">
      <el-row :gutter="6">
        <el-col :span="10"><el-input v-model="tf.interface" placeholder="接口" @change="emitUpdate" /></el-col>
        <el-col :span="6"><el-input-number v-model="tf.acl_number" :min="2000" @change="emitUpdate" /></el-col>
        <el-col :span="6">
          <el-select v-model="tf.direction" @change="emitUpdate">
            <el-option label="入站" value="inbound" />
            <el-option label="出站" value="outbound" />
          </el-select>
        </el-col>
        <el-col :span="2"><el-button text type="danger" @click="trafficFilters.splice(idx,1);emitUpdate()">✕</el-button></el-col>
      </el-row>
    </div>
    <el-button size="small" plain @click="trafficFilters.push({interface:'',acl_number:3000,direction:'inbound'});emitUpdate()" style="width:100%">+ 添加流量过滤</el-button>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const acls = reactive<Array<any>>(props.modelValue.acls || [])
const portSecurity = reactive<Array<any>>(props.modelValue.port_security || [])
const trafficFilters = reactive<Array<any>>(props.modelValue.traffic_filters || [])

function emitUpdate() {
    // 保留模板中额外字段（dhcp_snooping/storm_controls/anti_attack/arp_inspection等）
    const params: Record<string, any> = { ...props.modelValue }
    if (acls.length > 0) params.acls = [...acls]
    if (portSecurity.length > 0) params.port_security = [...portSecurity]
    if (trafficFilters.length > 0) params.traffic_filters = [...trafficFilters]
    emit('update:modelValue', params)
}

watch([acls, portSecurity, trafficFilters], emitUpdate, { deep: true })
</script>

<style scoped>
.sec-section { margin-bottom: 10px; padding: 8px; background: #fff; border-radius: 6px; border: 1px solid #ebeef5; }
.sec-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 12px; color: #606266; }
.rule-row { margin: 4px 0; }
</style>

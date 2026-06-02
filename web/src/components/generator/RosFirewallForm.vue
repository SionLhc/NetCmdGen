<template>
  <div class="form-section">
    <el-alert type="info" :closable="false" show-icon style="margin-bottom:14px">
      <template #title>RouterOS 使用 Chain 链式防火墙，代替传统的 ACL 和端口安全</template>
    </el-alert>

    <!-- NAT (源地址转换) -->
    <h4 class="sec-title">🔄 NAT 上网</h4>
    <el-form label-width="120px" size="small">
      <el-form-item label="启用 Masquerade">
        <el-switch v-model="model.nat" />
        <span class="tip">SNAT源地址伪装，用于内网上网</span>
      </el-form-item>
      <el-form-item v-if="model.nat" label="WAN 出口接口">
        <el-input v-model="model.natInterface" placeholder="例如: ether1" style="width:200px" />
      </el-form-item>
    </el-form>

    <!-- 防火墙规则 -->
    <h4 class="sec-title">🛡 防火墙过滤规则</h4>
    <el-form label-width="120px" size="small">
      <el-form-item label="Input 链规则">
        <el-input v-model="model.inputRules" type="textarea" :rows="4"
          placeholder="每行一条规则，格式: 动作,协议,端口&#10;例如:&#10;accept,tcp,22&#10;accept,icmp&#10;drop,tcp,8291" />
        <span class="tip">接受来自外部的 SSH(22)、ICMP(ping)；拒绝 WinBox(8291)</span>
      </el-form-item>
      <el-form-item label="Forward 链规则">
        <el-input v-model="model.forwardRules" type="textarea" :rows="3"
          placeholder="例如:&#10;drop,udp,445&#10;drop,tcp,135&#10;拒绝常见漏洞端口转发" />
      </el-form-item>
    </el-form>

    <!-- 端口映射 (DNAT) -->
    <h4 class="sec-title">🔀 端口映射 (DNAT)</h4>
    <el-form label-width="120px" size="small">
      <el-form-item v-for="(dnat, i) in model.dnatRules" :key="i" :label="'规则 ' + (i + 1)">
        <el-input v-model="dnat.publicPort" placeholder="公网端口" style="width:100px" />
        <span style="margin:0 6px;color:#909399">→</span>
        <el-input v-model="dnat.internalIp" placeholder="内网 IP" style="width:130px" />
        <span style="margin:0 6px;color:#909399">:</span>
        <el-input v-model="dnat.internalPort" placeholder="内网端口" style="width:100px" />
        <el-button text type="danger" @click="model.dnatRules.splice(i,1)" :disabled="model.dnatRules.length <= 1">✕</el-button>
      </el-form-item>
      <el-button size="small" @click="model.dnatRules.push({publicPort:'',internalIp:'',internalPort:''})">+ 添加映射</el-button>
    </el-form>

    <!-- WireGuard (V7) -->
    <h4 class="sec-title">🔐 WireGuard VPN (V7)</h4>
    <el-form label-width="120px" size="small">
      <el-form-item label="启用 WireGuard">
        <el-switch v-model="model.wireguard" />
        <span class="tip">RouterOS V7 原生支持</span>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

// 初始化默认值
const model = reactive({
  nat: false,
  natInterface: 'ether1',
  inputRules: '',
  forwardRules: '',
  dnatRules: [{ publicPort: '', internalIp: '', internalPort: '' }] as Array<{ publicPort: string; internalIp: string; internalPort: string }>,
  wireguard: false,
  ...props.modelValue,
})

watch(() => model, () => emit('update:modelValue', { ...model }), { deep: true })
</script>

<style scoped>
.form-section { padding: 4px 0; }
.sec-title { font-size: 14px; color: #303133; margin: 16px 0 10px; font-weight: 600; }
.tip { font-size: 11px; color: #909399; margin-left: 8px; }
</style>

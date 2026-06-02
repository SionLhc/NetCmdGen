<template>
  <el-card>
    <template #header><span class="title">网络工具箱</span></template>
    <el-tabs v-model="activeTool">
      <!-- 子网计算器 -->
      <el-tab-pane label="子网计算器" name="subnet">
        <el-form :inline="true" :model="subnetForm" label-width="80px">
          <el-form-item label="IP 地址">
            <el-input v-model="subnetForm.ip" placeholder="192.168.1.10" />
          </el-form-item>
          <el-form-item label="掩码/前缀">
            <el-input v-model="subnetForm.mask" placeholder="255.255.255.0 或 24" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onCalcSubnet" :loading="loading">计算</el-button>
          </el-form-item>
        </el-form>
        <el-descriptions v-if="subnetResult" :column="2" border class="result-table">
          <el-descriptions-item label="网络地址">{{ subnetResult.network_address }}</el-descriptions-item>
          <el-descriptions-item label="广播地址">{{ subnetResult.broadcast_address }}</el-descriptions-item>
          <el-descriptions-item label="可用主机范围">{{ subnetResult.first_usable }} ~ {{ subnetResult.last_usable }}</el-descriptions-item>
          <el-descriptions-item label="可用主机数">{{ subnetResult.usable_hosts }}</el-descriptions-item>
          <el-descriptions-item label="IP 类型">{{ subnetResult.ip_type }}</el-descriptions-item>
          <el-descriptions-item label="前缀长度">/{{ subnetResult.prefix_length }}</el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>

      <!-- 子网划分 -->
      <el-tab-pane label="子网划分" name="split">
        <el-form :inline="true" :model="splitForm" label-width="80px">
          <el-form-item label="网络地址">
            <el-input v-model="splitForm.network" placeholder="192.168.1.0" />
          </el-form-item>
          <el-form-item label="原前缀">
            <el-input-number v-model="splitForm.prefix" :min="0" :max="32" />
          </el-form-item>
          <el-form-item label="新前缀">
            <el-input-number v-model="splitForm.newPrefix" :min="1" :max="32" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onSplit" :loading="loading">划分</el-button>
          </el-form-item>
        </el-form>
        <el-table v-if="splitResult?.subnets?.length" :data="splitResult.subnets" border class="result-table">
          <el-table-column type="index" label="#" width="60" />
          <el-table-column prop="subnet" label="子网" />
          <el-table-column label="可用范围">
            <template #default="{ row }">{{ row.first_host }} ~ {{ row.last_host }}</template>
          </el-table-column>
          <el-table-column prop="hosts" label="主机数" width="100" />
        </el-table>
      </el-tab-pane>

      <!-- Ping 测试 -->
      <el-tab-pane label="Ping 测试" name="ping">
        <el-form :inline="true" :model="pingForm" label-width="80px">
          <el-form-item label="目标">
            <el-input v-model="pingForm.host" placeholder="8.8.8.8 或 baidu.com" />
          </el-form-item>
          <el-form-item label="次数">
            <el-input-number v-model="pingForm.count" :min="1" :max="20" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onPing" :loading="loading">Ping</el-button>
          </el-form-item>
        </el-form>
        <el-descriptions v-if="pingResult" :column="3" border class="result-table">
          <el-descriptions-item label="目标">{{ pingResult.host }}</el-descriptions-item>
          <el-descriptions-item label="解析IP">{{ pingResult.ip_address }}</el-descriptions-item>
          <el-descriptions-item label="丢包率">{{ pingResult.loss_rate }}%</el-descriptions-item>
          <el-descriptions-item label="发送/接收">{{ pingResult.packets_sent }} / {{ pingResult.packets_received }}</el-descriptions-item>
          <el-descriptions-item label="最小延迟">{{ pingResult.min_time }} ms</el-descriptions-item>
          <el-descriptions-item label="最大延迟">{{ pingResult.max_time }} ms</el-descriptions-item>
          <el-descriptions-item label="平均延迟">{{ pingResult.avg_time }} ms</el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>

      <!-- 端口扫描 -->
      <el-tab-pane label="端口扫描" name="portscan">
        <el-form :inline="true" :model="scanForm" label-width="80px">
          <el-form-item label="目标">
            <el-input v-model="scanForm.host" placeholder="192.168.1.1" />
          </el-form-item>
          <el-form-item label="端口">
            <el-input v-model="scanForm.ports" placeholder="22,80,443,3389" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onScan" :loading="loading">扫描</el-button>
          </el-form-item>
        </el-form>
        <el-table v-if="scanResult?.ports?.length" :data="scanResult.ports" border class="result-table">
          <el-table-column prop="port" label="端口" width="100" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="service" label="服务" width="150" />
          <el-table-column prop="banner" label="Banner" />
        </el-table>
      </el-tab-pane>

      <!-- 路由跟踪 -->
      <el-tab-pane label="路由跟踪" name="trace">
        <el-form :inline="true" :model="traceForm" label-width="80px">
          <el-form-item label="目标">
            <el-input v-model="traceForm.host" placeholder="8.8.8.8" />
          </el-form-item>
          <el-form-item label="最大跳数">
            <el-input-number v-model="traceForm.maxHops" :min="1" :max="50" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onTrace" :loading="loading">跟踪</el-button>
          </el-form-item>
        </el-form>
        <el-table v-if="traceResult?.hops?.length" :data="traceResult.hops" border class="result-table">
          <el-table-column prop="hop_number" label="跳" width="80" />
          <el-table-column prop="ip" label="IP" width="180" />
          <el-table-column label="主机名" min-width="200">
            <template #default="{ row }">
              {{ row.hostname || row.ip || '*' }}
            </template>
          </el-table-column>
          <el-table-column label="延迟" width="120">
            <template #default="{ row }">
              {{ row.avg_rtt ? row.avg_rtt.toFixed(1) + 'ms' : row.rtt_times?.join(', ') || '*' }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- DNS/Whois -->
      <el-tab-pane label="DNS/Whois" name="dns">
        <el-form :inline="true" :model="dnsForm" label-width="80px">
          <el-form-item label="域名">
            <el-input v-model="dnsForm.domain" placeholder="baidu.com" />
          </el-form-item>
          <el-form-item label="记录类型">
            <el-select v-model="dnsForm.recordType" style="width: 120px">
              <el-option label="A" value="A" />
              <el-option label="AAAA" value="AAAA" />
              <el-option label="MX" value="MX" />
              <el-option label="NS" value="NS" />
              <el-option label="TXT" value="TXT" />
              <el-option label="CNAME" value="CNAME" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onDns" :loading="loading">查询</el-button>
            <el-button @click="onWhois" :loading="loading">Whois</el-button>
          </el-form-item>
        </el-form>
        <el-table v-if="dnsResult?.records?.length" :data="dnsResult.records.map((r: any) => typeof r === 'string' ? { value: r } : r)" border class="result-table">
          <el-table-column prop="value" label="结果" />
          <el-table-column v-if="dnsResult.records[0]?.priority" prop="priority" label="优先级" width="100" />
        </el-table>
        <pre v-if="whoisResult" class="output-block">{{ JSON.stringify(whoisResult.info, null, 2) }}</pre>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  calcSubnet, splitSubnet, doPing, doPortScan, doTrace, doDns, doWhois,
} from '@/api'

const activeTool = ref('subnet')
const loading = ref(false)

// 子网计算器
const subnetForm = ref({ ip: '192.168.1.10', mask: '255.255.255.0' })
const subnetResult = ref<any>(null)

async function onCalcSubnet() {
  loading.value = true
  try {
    subnetResult.value = await calcSubnet(subnetForm.value.ip, subnetForm.value.mask)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '计算失败')
  } finally {
    loading.value = false
  }
}

// 子网划分
const splitForm = ref({ network: '192.168.1.0', prefix: 24, newPrefix: 26 })
const splitResult = ref<any>(null)

async function onSplit() {
  loading.value = true
  try {
    splitResult.value = await splitSubnet(splitForm.value.network, splitForm.value.prefix, splitForm.value.newPrefix)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '划分失败')
  } finally {
    loading.value = false
  }
}

// Ping
const pingForm = ref({ host: '8.8.8.8', count: 4 })
const pingResult = ref<any>(null)

async function onPing() {
  loading.value = true
  try {
    pingResult.value = await doPing(pingForm.value.host, pingForm.value.count)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || 'Ping 失败')
  } finally {
    loading.value = false
  }
}

// 端口扫描
const scanForm = ref({ host: '192.168.1.1', ports: '22,80,443,3389' })
const scanResult = ref<any>(null)

async function onScan() {
  loading.value = true
  try {
    scanResult.value = await doPortScan(scanForm.value.host, scanForm.value.ports)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '扫描失败')
  } finally {
    loading.value = false
  }
}

// 路由跟踪
const traceForm = ref({ host: '8.8.8.8', maxHops: 30 })
const traceResult = ref<any>(null)

async function onTrace() {
  loading.value = true
  try {
    traceResult.value = await doTrace(traceForm.value.host, traceForm.value.maxHops)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '跟踪失败')
  } finally {
    loading.value = false
  }
}

// DNS/Whois
const dnsForm = ref({ domain: 'baidu.com', recordType: 'A' })
const dnsResult = ref<any>(null)
const whoisResult = ref<any>(null)

async function onDns() {
  loading.value = true
  try {
    dnsResult.value = await doDns(dnsForm.value.domain, dnsForm.value.recordType)
    whoisResult.value = null
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || 'DNS 查询失败')
  } finally {
    loading.value = false
  }
}

async function onWhois() {
  loading.value = true
  try {
    whoisResult.value = await doWhois(dnsForm.value.domain)
    dnsResult.value = null
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || 'Whois 查询失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.result-table { margin-top: 16px; }
.output-block {
  background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 6px;
  font-family: 'Consolas', monospace; font-size: 13px; margin-top: 16px;
  max-height: 400px; overflow: auto; white-space: pre-wrap;
}
</style>

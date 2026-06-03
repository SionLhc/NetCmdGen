<template>
  <el-form label-width="110px" size="small">
    <!-- PCC 多线负载均衡 -->
    <el-divider content-position="left">⚖ PCC 多线负载均衡（对标 WinBox）</el-divider>
    <el-form-item label="启用 PCC">
      <el-switch v-model="form.pccEnabled" active-text="启用" inactive-text="关闭" />
    </el-form-item>
    <template v-if="form.pccEnabled">
      <!-- PCC 分类器模式 -->
      <el-form-item label="分类器模式">
        <el-select v-model="form.pccClassifier" style="width:100%">
          <el-option label="both-addresses（按源+目的，推荐★）" value="both-addresses" />
          <el-option label="both-addresses-and-ports（源+目的+端口，最细）" value="both-addresses-and-ports" />
          <el-option label="src-address（按源IP，同用户走同线）" value="src-address" />
          <el-option label="dst-address（按目的IP，同网站走同线）" value="dst-address" />
          <el-option label="src-port（按源端口）" value="src-port" />
          <el-option label="dst-port（按目的端口）" value="dst-port" />
        </el-select>
        <div class="ros-hint">WinBox: Mangle → New Mangle Rule → Advanced → Per Connection Classifier</div>
      </el-form-item>
      <!-- PCC 选项 -->
      <el-form-item label="回程标记">
        <el-switch v-model="form.pccMarkOutput" size="small" />
        <span class="ros-hint">output 链 mark-routing，确保回包走正确的线路</span>
      </el-form-item>
      <el-form-item label="局域网接口">
        <el-input v-model="form.pccLanInterface" size="small" placeholder="bridge1（内网接口，留空则不过滤入口）" />
      </el-form-item>
      <!-- WAN 线路列表 -->
      <el-divider content-position="left">WAN 线路 & Bucket 分配</el-divider>
      <div class="ros-hint" style="margin-bottom:8px">
        总Bucket数 = 各线路 Bucket 总数之和。WinBox 中用 <b>both-addresses:N/T</b> 控制每条线拿哪些 bucket。
      </div>
      <div v-for="(wan, wi) in form.pccWans" :key="'pcc'+wi" class="pcc-card">
        <div class="pcc-card-header">
          <span class="pcc-line-label">线路 {{ wi + 1 }}</span>
          <el-button text type="danger" size="small" @click="form.pccWans.splice(wi,1);emitUpdate()" :disabled="form.pccWans.length<=1">删除</el-button>
        </div>
        <el-row :gutter="6">
          <el-col :span="7">
            <div class="field-label">WAN 接口</div>
            <el-input v-model="wan.interface" size="small" placeholder="ether1" />
          </el-col>
          <el-col :span="7">
            <div class="field-label">网关 IP</div>
            <el-input v-model="wan.gateway" size="small" placeholder="203.0.113.1" />
          </el-col>
          <el-col :span="10">
            <div class="field-label">路由标记</div>
            <el-input v-model="wan.routingMark" size="small" placeholder="WAN1" />
          </el-col>
        </el-row>
        <el-row :gutter="6" style="margin-top:6px" align="middle">
          <el-col :span="8">
            <div class="field-label">流量份额</div>
            <el-input-number v-model="wan.bucketCount" size="small" :min="1" :max="100" style="width:100%" placeholder="1" @change="recalcBuckets" />
          </el-col>
          <el-col :span="16">
            <div class="field-label">选项</div>
            <el-checkbox v-model="wan.isDefault" size="small" border>设为默认路由</el-checkbox>
            <el-checkbox v-model="wan.autoNat" size="small" border style="margin-left:4px">自动 NAT</el-checkbox>
          </el-col>
        </el-row>
        <div class="ros-hint pcc-hint">
          WinBox: {{ form.pccClassifier }}:{{ totalBuckets }}/{{ wan.bucketStart }}{{ wan.bucketCount > 1 ? '-' + wan.bucketEnd : '' }}
          <span v-if="wan.bucketCount > 1" style="color:#67c23a">（{{ wan.bucketCount }}倍流量）</span>
        </div>
      </div>
      <el-button size="small" type="primary" plain @click="addPccWan();emitUpdate()" style="width:100%">+ 添加 WAN 线路</el-button>
    </template>

    <!-- 静态路由 -->
    <el-divider content-position="left">📡 静态路由</el-divider>
    <div v-for="(r, i) in form.staticRoutes" :key="'sr'+i" class="route-row">
      <el-row :gutter="4">
        <el-col :span="6">
          <el-input v-model="r.dst" size="small" placeholder="目标网络" />
        </el-col>
        <el-col :span="1" style="text-align:center;line-height:32px;color:#909399">/</el-col>
        <el-col :span="3">
          <el-input v-model="r.prefix" size="small" placeholder="前缀" />
        </el-col>
        <el-col :span="6">
          <el-input v-model="r.gateway" size="small" placeholder="下一跳" />
        </el-col>
        <el-col :span="4">
          <el-input v-model="r.routingMark" size="small" placeholder="路由标签（必填）" />
        </el-col>
        <el-col :span="3">
          <el-input v-model="r.comment" size="small" placeholder="备注" />
        </el-col>
        <el-col :span="1">
          <el-button text type="danger" size="small" @click="form.staticRoutes.splice(i,1);emitUpdate()">✕</el-button>
        </el-col>
      </el-row>
    </div>
    <el-button size="small" type="primary" plain @click="form.staticRoutes.push({dst:'0.0.0.0',prefix:'0',gateway:'',routingMark:'',comment:'默认路由'});emitUpdate()" style="width:100%">+ 添加路由</el-button>

    <!-- OSPF -->
    <el-divider content-position="left">🔄 OSPF 动态路由</el-divider>
    <el-form-item label="启用 OSPF">
      <el-switch v-model="form.ospfEnabled" active-text="启用" inactive-text="关闭" />
      <span class="ros-hint" style="margin-left:8px">V6/V7 语法不同，后端自动处理</span>
    </el-form-item>
    <template v-if="form.ospfEnabled">
      <el-form-item label="Router ID">
        <el-input v-model="form.ospfRouterId" size="small" placeholder="1.1.1.1" style="width:200px" />
      </el-form-item>
      <el-form-item label="OSPF 网络">
        <div v-for="(net, ni) in form.ospfNetworks" :key="'os'+ni" class="route-row">
          <el-row :gutter="4">
            <el-col :span="9"><el-input v-model="net.address" size="small" placeholder="网络地址" /></el-col>
            <el-col :span="7"><el-input v-model="net.area" size="small" placeholder="区域 (如 0.0.0.0)" /></el-col>
            <el-col :span="7">
              <el-select v-model="net.type" size="small" style="width:100%">
                <el-option label="broadcast" value="broadcast" />
                <el-option label="ptp（点对点）" value="ptp" />
              </el-select>
            </el-col>
            <el-col :span="1"><el-button text type="danger" size="small" @click="form.ospfNetworks.splice(ni,1);emitUpdate()">✕</el-button></el-col>
          </el-row>
        </div>
        <el-button size="small" type="primary" plain @click="form.ospfNetworks.push({address:'',area:'0.0.0.0',type:'broadcast'});emitUpdate()" style="width:100%">+ 添加 OSPF 网络</el-button>
      </el-form-item>
    </template>

    <!-- 策略路由（mangle 标记后的分流） -->
    <el-divider content-position="left">🔀 策略路由分流</el-divider>
    <div v-for="(pr, pi) in form.policyRoutes" :key="'pr'+pi" class="policy-row">
      <el-row :gutter="4" align="middle">
        <el-col :span="6"><el-input v-model="pr.srcAddr" size="small" placeholder="源IP/网段" /></el-col>
        <el-col :span="5"><el-input v-model="pr.dstAddr" size="small" placeholder="目标IP/网段" /></el-col>
        <el-col :span="4"><el-input v-model="pr.routingMark" size="small" placeholder="路由标签（必填）" /></el-col>
        <el-col :span="4"><el-input v-model="pr.gateway" size="small" placeholder="指定网关" /></el-col>
        <el-col :span="4"><el-input v-model="pr.comment" size="small" placeholder="备注" /></el-col>
        <el-col :span="1"><el-button text type="danger" size="small" @click="form.policyRoutes.splice(pi,1);emitUpdate()">✕</el-button></el-col>
      </el-row>
    </div>
    <el-button size="small" type="primary" plain @click="form.policyRoutes.push({srcAddr:'',dstAddr:'',routingMark:'',gateway:'',comment:''});emitUpdate()" style="width:100%">+ 添加策略路由</el-button>
  </el-form>
</template>

<script setup lang="ts">
import { computed, reactive, watch, nextTick } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string, any>] }>()

interface PccWan {
  interface: string; gateway: string; routingMark: string
  bucketStart: number; bucketEnd: number; bucketCount: number; isDefault: boolean; autoNat: boolean
}

const defaultWan = (i: number): PccWan => ({
  interface: `ether${i + 1}`,
  gateway: '',
  routingMark: `WAN${i + 1}`,
  bucketStart: i,
  bucketEnd: i,
  bucketCount: 1,
  isDefault: i === 0,
  autoNat: true,
})

const form = reactive({
  pccEnabled: false,
  pccClassifier: 'both-addresses-and-ports' as 'both-addresses-and-ports' | 'both-addresses' | 'src-address' | 'dst-address' | 'src-port' | 'dst-port',
  pccMarkOutput: true,
  pccLanInterface: 'bridge1',
  pccWans: [defaultWan(0)] as PccWan[],
  staticRoutes: [
    { dst: '0.0.0.0', prefix: '0', gateway: '', routingMark: '', comment: '默认路由' },
  ] as Array<{ dst: string; prefix: string; gateway: string; routingMark: string; comment: string }>,
  ospfEnabled: false,
  ospfRouterId: '',
  ospfNetworks: [
    { address: '', area: '0.0.0.0', type: 'broadcast' },
  ] as Array<{ address: string; area: string; type: string }>,
  policyRoutes: [] as Array<{ srcAddr: string; dstAddr: string; routingMark: string; gateway: string; comment: string }>,
})

/** 所有线路 Bucket 总数（分母） */
const totalBuckets = computed(() => {
  return form.pccWans.reduce((sum, w) => sum + w.bucketCount, 0)
})

/** 防抖 emit（200ms）避免高频触发 */
let emitTimer: ReturnType<typeof setTimeout> | null = null
function emitUpdate() {
  if (emitTimer) clearTimeout(emitTimer)
  emitTimer = setTimeout(() => emit('update:modelValue', { ...form }), 200)
}

/** 根据每条的 bucketCount 重新计算连续的 bucketStart/bucketEnd（从0开始）
 *  关键优化：for 循环内只修改数据不 emit，循环结束后统一 emit */
function recalcBuckets() {
  let pos = 0
  for (const w of form.pccWans) {
    w.bucketStart = pos
    w.bucketEnd = pos + w.bucketCount - 1
    pos = w.bucketEnd + 1
  }
  emitUpdate()
}

/** 添加一条新WAN，自动分配 bucket 范围（从0开始） */
function addPccWan() {
  const n = form.pccWans.length
  const last = form.pccWans[n - 1]
  const start = last ? last.bucketEnd + 1 : n
  form.pccWans.push({
    interface: `ether${n + 1}`,
    gateway: '',
    routingMark: `WAN${n + 1}`,
    bucketStart: start,
    bucketEnd: start,
    bucketCount: 1,
    isDefault: false,
    autoNat: true,
  })
  emitUpdate()
}

// 单向 props → form 同步（用 syncing 锁防止回环，不能用 once:true）
let _syncing = false
watch(() => props.modelValue, (v) => {
  if (_syncing || !v || Object.keys(v).length === 0) return
  _syncing = true
  const { pccWans, staticRoutes, ospfNetworks, policyRoutes, ...rest } = v as any
  Object.assign(form, rest)
  if (Array.isArray(pccWans)) { form.pccWans.length = 0; form.pccWans.push(...pccWans) }
  if (Array.isArray(staticRoutes)) { form.staticRoutes.length = 0; form.staticRoutes.push(...staticRoutes) }
  if (Array.isArray(ospfNetworks)) { form.ospfNetworks.length = 0; form.ospfNetworks.push(...ospfNetworks) }
  if (Array.isArray(policyRoutes)) { form.policyRoutes.length = 0; form.policyRoutes.push(...policyRoutes) }
  nextTick(() => { _syncing = false })
}, { immediate: true })

// 轻量 watch：只监听关键字段变化，不用 deep watch
watch([() => form.pccEnabled, () => form.pccClassifier, () => form.pccMarkOutput,
  () => form.ospfEnabled, () => form.ospfRouterId],
  () => emitUpdate()
)
// 数组字段单独 watch（轻量）
watch(() => form.pccWans.length, () => emitUpdate())
watch(() => form.staticRoutes.length, () => emitUpdate())
watch(() => form.ospfNetworks.length, () => emitUpdate())
watch(() => form.policyRoutes.length, () => emitUpdate())
</script>

<style scoped>
.route-row { margin-bottom: 6px; }
.ros-hint { font-size: 11px; color: #909399; margin-top: 2px; }
.field-label { font-size: 10px; color: #909399; margin-bottom: 1px; }
.pcc-card { border: 1px solid #e8ecf1; border-radius: 8px; padding: 10px; margin-bottom: 8px; background: #fafbfc; }
.pcc-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.pcc-line-label { font-size: 13px; font-weight: 600; color: #303133; }
.pcc-hint { margin-top: 6px; padding: 4px 8px; background: #ecf5ff; border-radius: 4px; color: #409eff; font-family: 'Consolas', monospace; font-size: 11px; }
</style>

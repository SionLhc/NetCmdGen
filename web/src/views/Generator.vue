<template>
  <div class="workbench-page">
    <!-- 顶部 Tab 切换 -->
    <div class="wb-tabs-bar">
      <el-radio-group v-model="activeTab" size="default">
        <el-radio-button value="config">⚙ 配置生成</el-radio-button>
        <el-radio-button value="project">📁 拓扑项目</el-radio-button>
      </el-radio-group>
      <span v-if="activeTab === 'project'" style="margin-left:12px;font-size:12px;color:#909399">
        从拓扑导入 → 逐台生成命令 → 保存 → 一键导出 MD
      </span>
    </div>

    <!-- ═══ Tab: 配置生成 ═══ -->
    <div v-show="activeTab === 'config'" class="wb-tab-content">
      <!-- 工具栏 -->
      <div class="wb-toolbar">
        <div class="wb-left">
          <span class="wb-title">命令工作台</span>
          <el-select v-model="scene" placeholder="设备场景" size="default" @change="onSceneChange" style="width:140px">
            <el-option v-for="s in sceneList" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
          <el-divider direction="vertical" />
          <span class="vendor-label">厂商:</span>
          <el-select v-model="activeVendor" placeholder="选择厂商" size="default" style="width:140px">
            <el-option v-for="v in vendorStore.vendors" :key="v.code" :label="v.name" :value="v.code" />
          </el-select>
          <!-- 华为 VRP 版本选择 -->
          <el-select v-if="activeVendor === 'huawei'" v-model="vrpVersion" size="default" style="width:120px">
            <el-option label="VRP V5" value="v5" />
            <el-option label="VRP V8" value="v8" />
            <el-option label="VRP V300" value="v300" />
          </el-select>
          <!-- 华三 Comware 版本选择 -->
          <el-select v-if="activeVendor === 'h3c'" v-model="vrpVersion" size="default" style="width:130px">
            <el-option label="Comware V5" value="v5" />
            <el-option label="Comware V7" value="v7" />
          </el-select>
          <!-- RouterOS 版本选择 -->
          <el-select v-if="activeVendor === 'routeros'" v-model="vrpVersion" size="default" style="width:120px">
            <el-option label="RouterOS V6" value="v6" />
            <el-option label="RouterOS V7" value="v7" />
          </el-select>
          <el-divider direction="vertical" />
          <el-dropdown @command="handleLoadTemplate" trigger="click">
            <el-button size="default" plain>加载模板 <el-icon><ArrowDown /></el-icon></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="t in allTemplates" :key="t.id" :command="t.id">
                  <div class="template-item"><span class="template-name">{{ t.name }}</span><span class="template-desc">{{ t.desc }}</span></div>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button size="default" plain @click="batchVisible = true">批量设备</el-button>
          <el-button v-if="topoStore.exportedDevices.length > 0" type="warning" size="default" plain @click="topoImportVisible = true">从拓扑导入 ({{ topoStore.exportedDevices.length }})</el-button>
        </div>
        <div class="wb-right">
          <el-button type="primary" size="default" @click="onGenerateAll" :loading="generating" :disabled="!activeVendor">生成完整命令</el-button>
          <el-button size="default" @click="onCompareAll" :loading="generating">对比全部厂商</el-button>
          <el-button @click="onCopyAll" :disabled="allOutputs.length===0" size="default">复制</el-button>
          <el-button @click="handleExport" :disabled="allOutputs.length===0" size="default">导出 .cfg</el-button>
          <el-button @click="handleExportExcel" :disabled="allOutputs.length===0" size="default">导出 Excel</el-button>
          <el-button @click="onClear" size="default">清空</el-button>
        </div>
      </div>

      <!-- 主内容 -->
      <div class="wb-body">
        <div class="wb-form">
          <!-- RouterOS 专属表单 -->
          <el-tabs v-if="isRouterOS" v-model="activeFormTab" class="form-tabs">
            <el-tab-pane label="系统设置" name="basic"><RosBasicForm v-model="formBasic" :key="'rosb-'+formKey" /></el-tab-pane>
            <el-tab-pane label="接口/Bridge" name="interface"><RosInterfaceForm v-model="formInterface" :key="'rosi-'+formKey" /></el-tab-pane>
            <el-tab-pane label="路由/PCC" name="routing"><RosRoutingForm v-model="formRouting" :key="'rosr-'+formKey" /></el-tab-pane>
            <el-tab-pane label="防火墙/NAT" name="security"><RosFirewallForm v-model="formSecurity" :key="'rosfw-'+formKey" /></el-tab-pane>
          </el-tabs>
          <!-- 路由器专属表单（华为/华三/锐捷/迈普） -->
          <el-tabs v-else-if="isRouterScene" v-model="activeFormTab" class="form-tabs">
            <el-tab-pane label="基础配置" name="basic"><BasicForm v-model="formBasic" :key="'basic-'+formKey" /></el-tab-pane>
            <el-tab-pane label="WAN 广域网" name="wan">
              <RouterWanForm v-model="formWan" :vendor="activeVendor" :key="'wan-'+formKey" />
            </el-tab-pane>
            <el-tab-pane label="路由" name="routing">
              <HuaweiRoutingForm v-if="activeVendor === 'huawei'" v-model="formRouting" :key="'hwr-'+formKey" />
              <H3cRoutingForm v-else-if="activeVendor === 'h3c'" v-model="formRouting" :key="'h3cr-'+formKey" />
              <RuijieRoutingForm v-else-if="activeVendor === 'ruijie'" v-model="formRouting" :key="'rjr-'+formKey" />
              <MaipuRoutingForm v-else-if="activeVendor === 'maipu'" v-model="formRouting" :key="'mpr-'+formKey" />
              <RoutingForm v-else v-model="formRouting" :key="'rout-'+formKey" />
            </el-tab-pane>
            <el-tab-pane label="ACL/防火墙" name="security"><SecurityForm v-model="formSecurity" :key="'sec-'+formKey" /></el-tab-pane>
            <el-tab-pane label="服务" name="service" v-if="hasService"><ServiceForm v-model="formService" :key="'svc-'+formKey" /></el-tab-pane>
          </el-tabs>
          <!-- 交换机专属表单（华为/华三/锐捷/迈普） -->
          <el-tabs v-else v-model="activeFormTab" class="form-tabs">
            <el-tab-pane label="基础配置" name="basic"><BasicForm v-model="formBasic" :key="'basic-'+formKey" /></el-tab-pane>
            <el-tab-pane label="VLAN" name="vlan"><VlanForm v-model="formVlan" :key="'vlan-'+formKey" /></el-tab-pane>
            <el-tab-pane label="路由" name="routing">
              <HuaweiRoutingForm v-if="activeVendor === 'huawei'" v-model="formRouting" :key="'hwr-'+formKey" />
              <H3cRoutingForm v-else-if="activeVendor === 'h3c'" v-model="formRouting" :key="'h3cr-'+formKey" />
              <RuijieRoutingForm v-else-if="activeVendor === 'ruijie'" v-model="formRouting" :key="'rjr-'+formKey" />
              <MaipuRoutingForm v-else-if="activeVendor === 'maipu'" v-model="formRouting" :key="'mpr-'+formKey" />
              <RoutingForm v-else v-model="formRouting" :key="'rout-'+formKey" />
            </el-tab-pane>
            <el-tab-pane label="安全" name="security"><SecurityForm v-model="formSecurity" :key="'sec-'+formKey" /></el-tab-pane>
            <el-tab-pane label="接口" name="interface"><InterfaceForm v-model="formInterface" :key="'if-'+formKey" /></el-tab-pane>
            <el-tab-pane label="服务" name="service" v-if="hasService"><ServiceForm v-model="formService" :key="'svc-'+formKey" /></el-tab-pane>
            <el-tab-pane label="QoS" name="qos" v-if="scene.includes('core')"><QosForm v-model="formQos" :key="'qos-'+formKey" /></el-tab-pane>
          </el-tabs>
        </div>
        <div class="wb-output">
          <template v-if="allOutputs.length > 0">
            <el-tabs v-model="activeOutputTab" type="card" class="output-tabs">
              <el-tab-pane v-for="(out, idx) in allOutputs" :key="idx" :label="out.vendorName" :name="String(idx)">
                <div class="output-info-bar">
                  <span>{{ out.vendorName }} — {{ out.lines }} 行</span>
                  <span style="display:flex;gap:8px">
                    <el-button text size="small" @click="copyOne(out.output)">复制</el-button>
                  </span>
                </div>
                <pre class="output-block"><code>{{ out.output }}</code></pre>
              </el-tab-pane>
            </el-tabs>
            <el-checkbox v-model="showDiff" style="margin:8px 16px" size="small">并排对比（{{ allOutputs.length }} 厂商，差异高亮）</el-checkbox>
            <div v-if="showDiff" class="diff-view">
              <div v-for="(out, idx) in allOutputs" :key="'d'+idx" class="diff-col">
                <div class="diff-header">{{ out.vendorName }}</div>
                <div class="diff-body">
                  <div class="diff-line" v-for="(line, li) in getDiffRows(idx)" :key="li" :class="line.cls">
                    <span class="diff-num">{{ String(li+1).padStart(3,' ') }}</span>
                    <span class="diff-code">{{ line.text }}</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="output-empty">
            <span class="empty-icon">⚙</span>
            <p>选择设备场景和厂商，配置参数后</p>
            <p><strong>点击"生成完整命令"</strong></p>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Tab: 拓扑项目 ═══ -->
    <div v-show="activeTab === 'project'" class="wb-tab-content">
      <ProjectView />
    </div>

    <!-- 批量设备对话框 -->
    <el-dialog v-model="batchVisible" title="批量设备生成" width="900px" top="5vh">
      <div style="margin-bottom:12px;display:flex;gap:8px;align-items:center">
        <el-select v-model="batchVendor" placeholder="厂商" size="small" style="width:140px"><el-option v-for="v in vendorStore.vendors" :key="v.code" :label="v.name" :value="v.code" /></el-select>
        <el-select v-model="batchScene" placeholder="场景" size="small" style="width:140px"><el-option v-for="s in sceneList" :key="s.id" :label="s.name" :value="s.id" /></el-select>
        <el-button size="small" @click="batchAddRow">+ 添加设备</el-button>
        <el-button size="small" plain @click="batchImportCsv">📄 导入CSV</el-button>
        <span style="font-size:12px;color:#909399;margin-left:auto">当前 {{ batchDevices.length }} 台设备</span>
      </div>
      <div style="max-height:420px;overflow:auto">
        <el-table :data="batchDevices" size="small" border>
          <el-table-column type="index" label="#" width="44" />
          <el-table-column label="主机名" min-width="140"><template #default="{row}"><el-input v-model="row.hostname" size="small" placeholder="SW-01" /></template></el-table-column>
          <el-table-column label="管理IP" min-width="140"><template #default="{row}"><el-input v-model="row.mgmtIp" size="small" placeholder="192.168.1.1" /></template></el-table-column>
          <el-table-column label="VLAN范围" min-width="160"><template #default="{row}"><el-input v-model="row.vlanRange" size="small" placeholder="10,20,30-50" /></template></el-table-column>
          <el-table-column label="描述" min-width="140"><template #default="{row}"><el-input v-model="row.description" size="small" placeholder="接入层交换机" /></template></el-table-column>
          <el-table-column label="操作" width="60" fixed="right"><template #default="{$index}"><el-button link type="danger" size="small" @click="batchDevices.splice($index,1)">删除</el-button></template></el-table-column>
        </el-table>
      </div>
      <div v-if="batchResults.length > 0" style="margin-top:12px">
        <el-divider>生成结果</el-divider>
        <div style="max-height:300px;overflow:auto">
          <div v-for="(r,i) in batchResults" :key="i" style="margin-bottom:8px;border:1px solid #ebeef5;border-radius:6px;overflow:hidden">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 12px;background:#f5f7fa;font-size:12px;cursor:pointer" @click="r.expanded=!r.expanded">
              <span><span :style="{color:r.error?'#f56c6c':'#67c23a',fontWeight:600}">{{ r.hostname }}</span> — {{ r.error ? '失败' : r.lines+' 行' }}</span>
              <span style="display:flex;gap:8px"><el-button link size="small" @click.stop="copyOne(r.output)">复制</el-button><span style="color:#909399">{{ r.expanded ? '▲' : '▼' }}</span></span>
            </div>
            <pre v-show="r.expanded" style="background:#1a1b2e;color:#c9d1d9;padding:8px 12px;margin:0;font-size:12px;line-height:1.5;max-height:200px;overflow:auto;white-space:pre-wrap">{{ r.output }}</pre>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="batchVisible = false">关闭</el-button>
        <el-button type="primary" @click="batchGenerateAll" :loading="batchGenerating" :disabled="!batchVendor||batchDevices.length===0">生成全部 {{ batchDevices.length }} 台设备</el-button>
      </template>
    </el-dialog>

    <!-- 从拓扑导入对话框 -->
    <el-dialog v-model="topoImportVisible" title="从拓扑导入设备" width="700px">
      <el-table :data="topoStore.exportedDevices" size="small" highlight-current-row @row-click="onTopoDeviceClick">
        <el-table-column type="index" label="#" width="44" />
        <el-table-column prop="hostname" label="主机名" min-width="120" />
        <el-table-column prop="typeName" label="类型" width="110"><template #default="{row}"><el-tag :type="typeTagFromRow(row)" size="small">{{ row.typeName }}</el-tag></template></el-table-column>
        <el-table-column prop="mgmtIp" label="管理IP" width="140" />
        <el-table-column prop="vlans" label="VLAN" min-width="120" />
        <el-table-column label="操作" width="80" fixed="right"><template #default="{row}"><el-button link type="primary" size="small" @click.stop="loadTopoDevice(row)">加载</el-button></template></el-table-column>
      </el-table>
      <div style="margin-top:10px;font-size:12px;color:#909399">点击行直接加载参数并关闭</div>
      <template #footer><el-button @click="topoImportVisible = false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useVendorStore } from '@/stores/vendor'
import { useTopologyStore, type TopologyDevice } from '@/stores/topology'
import { ArrowDown } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { generateFull as apiGenerateFull } from '@/api'
import { getAllTemplates, getTemplateById } from '@/data/templates'
import { validateBeforeGenerate, showValidationResult } from '@/utils/validator'
import ProjectView from '@/components/generator/ProjectView.vue'
import BasicForm from '@/components/generator/BasicForm.vue'
import VlanForm from '@/components/generator/VlanForm.vue'
import RoutingForm from '@/components/generator/RoutingForm.vue'
import SecurityForm from '@/components/generator/SecurityForm.vue'
import InterfaceForm from '@/components/generator/InterfaceForm.vue'
import QosForm from '@/components/generator/QosForm.vue'
import ServiceForm from '@/components/generator/ServiceForm.vue'
import RosFirewallForm from '@/components/generator/RosFirewallForm.vue'
import RosBasicForm from '@/components/generator/RosBasicForm.vue'
import RosInterfaceForm from '@/components/generator/RosInterfaceForm.vue'
import RosRoutingForm from '@/components/generator/RosRoutingForm.vue'
import HuaweiRoutingForm from '@/components/generator/HuaweiRoutingForm.vue'
import H3cRoutingForm from '@/components/generator/H3cRoutingForm.vue'
import RuijieRoutingForm from '@/components/generator/RuijieRoutingForm.vue'
import MaipuRoutingForm from '@/components/generator/MaipuRoutingForm.vue'
import RouterWanForm from '@/components/generator/RouterWanForm.vue'

const vendorStore = useVendorStore()
const topoStore = useTopologyStore()
const activeTab = ref<'config' | 'project'>('config')

interface SceneDef { id: string; name: string; desc: string; features: string[] }
const sceneList: SceneDef[] = [
  // ── 交换机 ──
  { id: 'core-switch', name: '核心交换机', desc: '园区/数据中心核心层', features: ['basic','vlan','routing','security','interface','qos','service'] },
  { id: 'agg-switch', name: '汇聚交换机', desc: '园区汇聚层', features: ['basic','vlan','routing','security','interface','service'] },
  { id: 'access-switch', name: '接入交换机', desc: '终端接入层', features: ['basic','vlan','security','interface','service'] },
  // ── 路由器 ──
  { id: 'router', name: '🛣 出口路由器', desc: '多线接入/负载均衡/NAT', features: ['basic','wan','routing','security','interface','service'] },
  // ── 防火墙 ──
  { id: 'firewall', name: '🛡 防火墙', desc: '安全策略/入侵防御/DMZ', features: ['basic','wan','routing','security','interface','service'] },
]

const scene = ref('core-switch')
const activeVendor = ref('')
const vrpVersion = ref<'v5'|'v8'|'v300'|'v7'|'v6'>('v8')
const activeFormTab = ref('basic')
const activeOutputTab = ref('0')
const showDiff = ref(false)
const generating = ref(false)
const formKey = ref(0)

const formBasic = ref<Record<string,any>>({})
const formVlan = ref<Record<string,any>>({})
const formRouting = ref<Record<string,any>>({})
const formSecurity = ref<Record<string,any>>({})
const formInterface = ref<Record<string,any>>({})
const formWan = ref<Record<string,any>>({})
const formQos = ref<Record<string,any>>({})
const formService = ref<Record<string,any>>({})

const hasService = computed(() => sceneList.find(x => x.id === scene.value)?.features.includes('service') ?? false)
const isRouterOS = computed(() => activeVendor.value === 'routeros')
const isRouterScene = computed(() => ['router','firewall'].includes(scene.value))

interface OutputItem { vendor: string; vendorName: string; output: string; lines: number }
const allOutputs = ref<OutputItem[]>([])

onMounted(() => vendorStore.loadVendors())

function onSceneChange() { activeFormTab.value = 'basic'; allOutputs.value = [] }

function buildFullConfig(): Record<string, any> {
  const cfg: Record<string, any> = { description: `场景: ${sceneList.find(x=>x.id===scene.value)?.name||''}`,
    basic: {...formBasic.value}, routing: {...formRouting.value},
    security: {...formSecurity.value}, interface: {...formInterface.value},
    service: {...formService.value} }
  if (isRouterScene.value) { cfg.wan = {...formWan.value} }
  else { cfg.vlan = {...formVlan.value}; cfg.qos = {...formQos.value} }
  return cfg
}

async function onGenerateAll() {
  if (!activeVendor.value) { ElMessage.warning('请选择厂商'); return }
  // 参数预检
  const config = buildFullConfig()
  const issues = validateBeforeGenerate(config)
  if (!showValidationResult(issues)) return
  generating.value = true; allOutputs.value = []
  const vObj = vendorStore.vendors.find(v => v.code === activeVendor.value)
  try {
    const vrp = ['huawei','h3c','routeros'].includes(activeVendor.value) ? vrpVersion.value : undefined
    const res = await apiGenerateFull({ vendor: activeVendor.value, config, vrp_version: vrp })
    allOutputs.value.push({ vendor: activeVendor.value, vendorName: vObj?.name || activeVendor.value, output: res.output, lines: res.output.split('\n').length })
  } catch (e: any) {
    allOutputs.value.push({ vendor: activeVendor.value, vendorName: vObj?.name || activeVendor.value, output: `# 生成失败: ${e.response?.data?.detail||e.message}`, lines: 1 })
  }
  generating.value = false; activeOutputTab.value = '0'
  ElMessage.success('生成完成')
}

async function onCompareAll() {
  // 参数预检
  const config = buildFullConfig()
  const issues = validateBeforeGenerate(config)
  if (!showValidationResult(issues)) return
  generating.value = true; allOutputs.value = []
  for (const v of vendorStore.vendors) {
    try {
      const vrp = ['huawei','h3c','routeros'].includes(v.code) ? vrpVersion.value : undefined
      const res = await apiGenerateFull({ vendor: v.code, config, vrp_version: vrp })
      allOutputs.value.push({ vendor: v.code, vendorName: v.name, output: res.output, lines: res.output.split('\n').length })
    } catch (e: any) { allOutputs.value.push({ vendor: v.code, vendorName: v.name, output: `# 失败: ${(e as Error).message}`, lines: 1 }) }
  }
  generating.value = false; activeOutputTab.value = '0'; showDiff.value = true
  ElMessage.success(`已对比 ${allOutputs.value.length} 个厂商`)
}

function onCopyAll() { const idx = Number(activeOutputTab.value); const out = allOutputs.value[idx]; if (out) { navigator.clipboard.writeText(out.output); ElMessage.success('已复制') } }
function copyOne(text: string) { navigator.clipboard.writeText(text); ElMessage.success('已复制') }
function onClear() { allOutputs.value = []; Object.keys({formBasic,formVlan,formRouting,formSecurity,formInterface,formQos,formService}).forEach(k => (eval(k).value = {})); showDiff.value = false }
function formatDiff(output: string): string { return output.split('\n').map((line,i)=>`${String(i+1).padStart(4,' ')}  ${line}`).join('\n') }

/** 计算行级 diff：相同行绿色、差异行黄色、仅此厂商有蓝色 */
const diffCache = computed(() => {
  const allLines = allOutputs.value.map(o => o.output.split('\n'))
  if (allLines.length < 2) return []
  const maxLen = Math.max(...allLines.map(l => l.length))
  const result: Array<Array<{ line: string; same: boolean; unique: boolean }>> = allLines.map(() => [])
  for (let i = 0; i < maxLen; i++) {
    const lines = allLines.map(l => l[i] || '')
    const unique = new Set(lines.filter(l => l))
    // 如果所有非空行都相同，标记为 same
    const same = unique.size <= 1 && lines.some(l => l)
    for (let v = 0; v < allLines.length; v++) {
      result[v].push({ line: lines[v], same: lines[v] ? same : false, unique: !lines[v] || (unique.size > 1 && !same) })
    }
  }
  return result
})

interface DiffRow { text: string; cls: string }
function getDiffRows(vendorIdx: number): DiffRow[] {
  const rows = diffCache.value
  if (rows.length === 0) {
    return allOutputs.value[vendorIdx]?.output.split('\n').map(t => ({ text: t, cls: '' })) || []
  }
  return (rows[vendorIdx] || []).map(item => ({
    text: item.line,
    cls: !item.line ? 'diff-empty' : item.same ? 'diff-same' : 'diff-changed',
  }))
}

// 模板加载
const allTemplates = getAllTemplates()
function handleLoadTemplate(id: string) {
  const tpl = getTemplateById(id); if (!tpl) return
  scene.value = tpl.scene; activeVendor.value = tpl.vendor; activeFormTab.value = 'basic'
  const c = tpl.config
  formBasic.value = c.basic||{}; formVlan.value = c.vlan||{}; formRouting.value = c.routing||{}
  formSecurity.value = c.security||{}; formInterface.value = c.interface||{}; formQos.value = c.qos||{}; formService.value = c.service||{}
  formWan.value = c.wan||{}
  formKey.value++; ElMessage.success(`已加载模板: ${tpl.name}`)
}

// 导出 .cfg
function handleExport() {
  const out = allOutputs.value[Number(activeOutputTab.value)]; if (!out) return
  const sname = sceneList.find(s=>s.id===scene.value)?.name||'device'
  const fname = `${formBasic.value.hostname||'NetCmdGen'}_${sname}_${out.vendor}.cfg`.replace(/\s+/g,'_')
  const b = new Blob([out.output],{type:'text/plain;charset=utf-8'}); const u = URL.createObjectURL(b)
  const a = document.createElement('a'); a.href=u; a.download=fname; a.click(); URL.revokeObjectURL(u)
  ElMessage.success(`已导出: ${fname}`)
}

// 导出 Excel（多厂商配置对比表）
function handleExportExcel() {
  if (allOutputs.value.length === 0) return
  // 每个厂商一列，加上行号列
  const maxLines = Math.max(...allOutputs.value.map(o => o.output.split('\n').length))
  const rows: Record<string, string>[] = []
  for (let i = 0; i < maxLines; i++) {
    const row: Record<string, string> = { '行号': String(i + 1) }
    for (const out of allOutputs.value) {
      const lines = out.output.split('\n')
      row[out.vendorName] = i < lines.length ? lines[i] : ''
    }
    rows.push(row)
  }
  const ws = XLSX.utils.json_to_sheet(rows)
  ws['!cols'] = [{ wch: 6 }, ...allOutputs.value.map(() => ({ wch: 50 }))]
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '配置对比')
  const hostname = formBasic.value.hostname || 'NetCmdGen'
  XLSX.writeFile(wb, `${hostname}_config_compare.xlsx`)
  ElMessage.success('Excel 已导出')
}

// 拓扑导入
function typeTagFromRow(row: TopologyDevice): string { return row.type.includes('core')?'':row.type.includes('router')?'danger':row.type.includes('firewall')?'warning':'success' }
const topoImportVisible = ref(false)
const typeToScene: Record<string,string> = { 'core-switch':'core-switch','agg-switch':'agg-switch','access-switch':'access-switch','router':'router','firewall':'firewall' }

function onTopoDeviceClick(row: TopologyDevice) { loadTopoDevice(row) }
function parseVlanIds(str: string): Array<{id:number;name:string}> {
  if (!str.trim()) return []
  const ids = new Set<number>()
  for (const p of str.split(',')) { const t=p.trim(); if(t.includes('-')){ const [s,e]=t.split('-').map(Number); if(!isNaN(s)&&!isNaN(e)) for(let i=s;i<=Math.min(e,s+50);i++) ids.add(i) } else { const n=Number(t); if(!isNaN(n)&&n>=1&&n<=4094) ids.add(n) } }
  return [...ids].map(id=>({id,name:`VLAN${id}`}))
}
function loadTopoDevice(dev: TopologyDevice) {
  scene.value = typeToScene[dev.type] || 'access-switch'
  formBasic.value = { hostname: dev.hostname, mgmt_ip: dev.mgmtIp, enable_ssh: true, ssh_port: 22 }
  const vids = parseVlanIds(dev.vlans||'')
  if (vids.length>0) formVlan.value = { vlans: vids, interfaces: vids.map(v=>({interface:`GigabitEthernet0/0/${v.id}`,type:'access',vlan_id:v.id})) }
  if (dev.ports && dev.ports.length > 0) {
    formInterface.value = { eth_trunks: dev.ports.filter((p:any)=>p.direction==='uplink').map((p:any,i:number)=>({trunk_id:i+1,mode:p.linkType==='trunk'?'lacp':'manual',members:[p.interface],description:`To-${p.remoteDevice}`})) }
  }
  formRouting.value={}; formSecurity.value={}; formQos.value={}; formService.value={}
  formKey.value++; topoImportVisible.value = false
  ElMessage.success(`已加载: ${dev.hostname}`)
}

// 项目编辑（已废弃：ProjectView 现在内联生成，不再跳转到配置生成页）

// 批量设备
const batchVisible = ref(false); const batchVendor = ref(''); const batchScene = ref('access-switch'); const batchGenerating = ref(false)
interface BatchDevice { hostname: string; mgmtIp: string; vlanRange: string; description: string }
const batchDevices = ref<BatchDevice[]>([{hostname:'SW-ACC-01',mgmtIp:'192.168.1.11',vlanRange:'10',description:'1F接入交换机'},{hostname:'SW-ACC-02',mgmtIp:'192.168.1.12',vlanRange:'20',description:'2F接入交换机'}])
interface BatchResult { hostname: string; output: string; lines: number; error: boolean; expanded: boolean }
const batchResults = ref<BatchResult[]>([])
function batchAddRow() { const n = batchDevices.value.length + 1; batchDevices.value.push({hostname:`SW-${String(n).padStart(2,'0')}`,mgmtIp:'',vlanRange:'',description:''}) }
function batchImportCsv() {
  const inp = document.createElement('input'); inp.type='file'; inp.accept='.csv'
  inp.onchange=async e=>{ const f=(e.target as HTMLInputElement).files?.[0]; if(!f)return; const t=await f.text(); const ls=t.split('\n').filter(l=>l.trim()); if(ls.length<2){ElMessage.warning('CSV至少需要标题行+1行数据');return}
    const h=ls[0].toLowerCase().split(',').map(x=>x.trim()); const hi=h.indexOf('hostname'); const ii=Math.max(h.indexOf('ip'),h.indexOf('mgmt_ip')); const vi=h.indexOf('vlan'); const di=Math.max(h.indexOf('description'),h.indexOf('desc'))
    batchDevices.value=[]; for(let i=1;i<ls.length;i++){const c=ls[i].split(',').map(x=>x.trim()); if(c.length<h.length)continue
    batchDevices.value.push({hostname:hi>=0?c[hi]:`SW-${i}`,mgmtIp:ii>=0?c[ii]:'',vlanRange:vi>=0?c[vi]:'',description:di>=0?c[di]:''})}
    ElMessage.success(`已导入 ${batchDevices.value.length} 台设备`) }; inp.click()
}
async function batchGenerateAll() {
  if (!batchVendor.value) { ElMessage.warning('请选择厂商'); return }
  // 批量设备预检
  const batchIssues = batchDevices.value.flatMap((dev, i) => {
    const issues: Array<{ field: string; message: string; severity: 'error' | 'warning' }> = []
    if (!dev.hostname || dev.hostname.trim() === '') {
      issues.push({ field: `batch[${i}].hostname`, message: '主机名不能为空', severity: 'error' })
    }
    return issues
  })
  if (!showValidationResult(batchIssues)) return
  batchGenerating.value = true; batchResults.value = []
  for (const dev of batchDevices.value) {
    const vlans = parseVlanIds(dev.vlanRange)
    const config: Record<string,any> = { description: dev.description||'批量生成', basic: { hostname: dev.hostname, mgmt_ip: dev.mgmtIp }, vlan: vlans.length>0?{vlans,interfaces:vlans.map(v=>({interface:`GigabitEthernet0/0/${v.id}`,type:'access',vlan_id:v.id}))}:{}, routing:{}, security:{}, interface:{}, service:{} }
    try { const bv = batchVendor.value; const vrp = ['huawei','h3c','routeros'].includes(bv)?vrpVersion.value:undefined; const res = await apiGenerateFull({ vendor: bv, config, vrp_version: vrp })
      batchResults.value.push({ hostname: dev.hostname, output: res.output, lines: res.output.split('\n').length, error: false, expanded: false })
    } catch (e: any) { batchResults.value.push({ hostname: dev.hostname, output: `# 失败: ${e.response?.data?.detail||(e as Error).message}`, lines: 1, error: true, expanded: true }) }
  }
  batchGenerating.value = false; ElMessage.success(`已生成 ${batchResults.value.length} 台设备`)
}
</script>

<style scoped>
.workbench-page { height: 100%; display: flex; flex-direction: column; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04); }
.wb-tabs-bar { display: flex; align-items: center; padding: 10px 20px; background: #fafbfc; border-bottom: 1px solid #f0f0f0; }
.wb-tab-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-height: 0; }
.wb-toolbar { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; background: #fff; border-bottom: 1px solid #f0f0f0; flex-wrap: wrap; gap: 12px; }
.wb-left { display: flex; align-items: center; gap: 12px; }
.wb-title { font-size: 17px; font-weight: 700; color: #1e293b; margin-right: 4px; }
.vendor-label { font-size: 13px; color: #64748b; font-weight: 500; }
.wb-right { display: flex; gap: 8px; }
.wb-body { flex: 1; display: flex; overflow: hidden; min-height: 0; }
.wb-form { width: 440px; border-right: 1px solid #f0f0f0; background: #fafbfc; overflow-y: auto; }
.wb-output { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-height: 0; }
.form-tabs :deep(.el-tabs__header) { padding: 0 16px; margin: 0; position: sticky; top: 0; background: #fafbfc; z-index: 10; border-bottom: 1px solid #e8ecf1; }
.form-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
.form-tabs :deep(.el-tabs__content) { padding: 12px 16px; }
.output-tabs { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.output-tabs :deep(.el-tabs__header) { margin: 0; padding: 0 12px; background: #fff; border-bottom: 1px solid #e8ecf1; }
.output-tabs :deep(.el-tabs__item) { color: #64748b; font-size: 13px; }
.output-tabs :deep(.el-tabs__item.is-active) { color: #6366f1; }
.output-tabs :deep(.el-tabs__content) { flex: 1; overflow: hidden; min-height: 0; }
.output-tabs :deep(.el-tab-pane) { height: 100%; display: flex; flex-direction: column; }
.output-info-bar { display: flex; align-items: center; justify-content: space-between; padding: 8px 16px; background: #f8f9fb; color: #64748b; font-size: 12px; border-bottom: 1px solid #f0f0f0; flex-shrink: 0; }
.output-block { flex: 1; background: #1a1b2e; color: #c9d1d9; padding: 16px 20px; margin: 0; font-family: 'JetBrains Mono','Fira Code','Consolas',monospace; font-size: 13px; line-height: 1.8; overflow: auto; white-space: pre-wrap; word-break: break-all; tab-size: 4; min-height: 0; }
.output-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; gap: 8px; font-size: 14px; background: #f8f9fb; }
.diff-view { display: flex; gap: 1px; background: #2d2d3d; flex: 1; overflow: auto; }
.diff-col { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.diff-header { padding: 6px 12px; background: #1a1b2e; color: #818cf8; font-size: 12px; font-weight: 600; text-align: center; border-bottom: 1px solid #2d2d3d; flex-shrink: 0; }
.diff-body { flex: 1; overflow-y: auto; min-height: 0; font-family: 'JetBrains Mono','Consolas',monospace; font-size: 11px; line-height: 1.6; }
.diff-line { display: flex; white-space: pre-wrap; word-break: break-all; }
.diff-line.diff-same { background: rgba(16,185,129,.06); }
.diff-line.diff-changed { background: rgba(250,204,21,.15); }
.diff-line.diff-empty { background: rgba(148,163,184,.05); }
.diff-num { flex-shrink: 0; width: 32px; text-align: right; padding-right: 8px; color: #475569; user-select: none; }
.diff-code { flex: 1; min-width: 0; }
.diff-line.diff-same .diff-code { color: #86efac; }
.diff-line.diff-changed .diff-code { color: #fde68a; }
.diff-line.diff-empty .diff-code { color: #4b5563; }
.diff-block { flex: 1; background: #1a1b2e; color: #c9d1d9; padding: 10px 12px; margin: 0; font-family: 'JetBrains Mono','Consolas',monospace; font-size: 11px; line-height: 1.5; overflow: auto; white-space: pre-wrap; word-break: break-all; min-height: 0; }
.template-item { display: flex; flex-direction: column; gap: 2px; }
.template-name { font-size: 14px; font-weight: 500; color: #303133; }
.template-desc { font-size: 11px; color: #909399; }
</style>

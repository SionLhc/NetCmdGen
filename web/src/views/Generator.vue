<template>
  <el-card class="gen-card">
    <template #header>
      <div class="gen-header">
        <span class="title">配置命令生成器</span>
        <el-select v-model="vendor" placeholder="选择厂商" style="width: 160px" @change="onVendorChange">
          <el-option v-for="v in vendorStore.vendors" :key="v.code" :label="v.name" :value="v.code" />
        </el-select>
        <el-select v-model="feature" placeholder="选择特性" style="width: 140px">
          <el-option v-for="f in currentFeatures" :key="f" :label="f" :value="f" />
        </el-select>
      </div>
    </template>

    <el-row :gutter="16">
      <!-- 参数面板 -->
      <el-col :span="10">
        <el-card shadow="never" class="param-card">
          <template #header>参数配置</template>
          <div class="param-form">
            <el-alert v-if="!vendor" title="请先选择厂商" type="info" :closable="false" />
            <template v-else>
              <el-form :model="params" label-width="100px" size="default">
                <el-form-item label="主机名">
                  <el-input v-model="params.hostname" placeholder="SW-CORE-01" />
                </el-form-item>
                <el-form-item label="VLAN ID">
                  <el-input-number v-model="params.vlan_id" :min="1" :max="4094" />
                </el-form-item>
                <el-form-item label="VLAN 名称">
                  <el-input v-model="params.vlan_name" placeholder="Office" />
                </el-form-item>
                <el-form-item label="接口">
                  <el-input v-model="params.interface" placeholder="GigabitEthernet0/0/1" />
                </el-form-item>
                <el-form-item label="接口类型">
                  <el-select v-model="params.link_type" style="width: 100%">
                    <el-option label="access" value="access" />
                    <el-option label="trunk" value="trunk" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="onGenerate" :loading="generating">生成命令</el-button>
                  <el-button @click="onGenerateFull" :loading="generating">生成完整脚本</el-button>
                  <el-button @click="onCopy" :disabled="!output">复制</el-button>
                </el-form-item>
              </el-form>
            </template>
          </div>
        </el-card>
      </el-col>

      <!-- 命令输出 -->
      <el-col :span="14">
        <el-card shadow="never" class="output-card">
          <template #header>
            <span>生成结果</span>
          </template>
          <pre class="output-block"><code>{{ output || '← 选择厂商和特性后点击生成' }}</code></pre>
        </el-card>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useVendorStore } from '@/stores/vendor'
import { generate, generateFull } from '@/api'

const vendorStore = useVendorStore()
const vendor = ref('')
const feature = ref('vlan')
const output = ref('')
const generating = ref(false)

const currentFeatures = computed(() => {
  const v = vendorStore.vendors.find((x) => x.code === vendor.value)
  return v?.features ?? []
})

const params = ref({
  hostname: 'SW-CORE-01',
  vlan_id: 10,
  vlan_name: 'Office',
  interface: 'GigabitEthernet0/0/1',
  link_type: 'access',
})

onMounted(() => vendorStore.loadVendors())

function onVendorChange() {
  output.value = ''
}

async function onGenerate() {
  if (!vendor.value) return ElMessage.warning('请选择厂商')
  generating.value = true
  try {
    const res = await generate({
      vendor: vendor.value,
      feature: feature.value,
      params: {
        vlans: [{ id: params.value.vlan_id, name: params.value.vlan_name }],
        interfaces: [{
          interface: params.value.interface,
          type: params.value.link_type,
          vlan_id: params.value.vlan_id,
        }],
      },
    })
    output.value = res.output
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '生成失败')
  } finally {
    generating.value = false
  }
}

async function onGenerateFull() {
  if (!vendor.value) return ElMessage.warning('请选择厂商')
  generating.value = true
  try {
    const res = await generateFull({
      vendor: vendor.value,
      config: {
        description: 'NetCmdGen Demo',
        basic: {
          hostname: params.value.hostname,
          enable_ssh: true,
        },
        vlan: {
          vlans: [{ id: params.value.vlan_id, name: params.value.vlan_name }],
          interfaces: [{
            interface: params.value.interface,
            type: params.value.link_type,
            vlan_id: params.value.vlan_id,
          }],
        },
      },
    })
    output.value = res.output
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '生成失败')
  } finally {
    generating.value = false
  }
}

function onCopy() {
  navigator.clipboard.writeText(output.value)
  ElMessage.success('已复制到剪贴板')
}
</script>

<style scoped>
.gen-card { height: 100%; }
.gen-header { display: flex; align-items: center; gap: 12px; }
.gen-header .title { font-size: 16px; font-weight: bold; flex: 1; }
.param-form { padding: 8px 0; }
.output-block {
  background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 6px;
  font-family: 'Consolas', 'Courier New', monospace; font-size: 13px;
  min-height: 400px; max-height: calc(100vh - 260px); overflow: auto;
  white-space: pre-wrap; word-break: break-all;
}
</style>

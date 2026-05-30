<template>
  <el-card>
    <template #header>
      <div class="manual-header">
        <span class="title">命令速查百科</span>
        <el-select v-model="vendor" placeholder="选择厂商" style="width: 140px" @change="loadManual">
          <el-option label="华为 Huawei" value="huawei" />
          <el-option label="华三 H3C" value="h3c" />
          <el-option label="锐捷 Ruijie" value="ruijie" />
          <el-option label="迈普 Maipu" value="maipu" />
        </el-select>
        <el-input
          v-model="keyword"
          placeholder="搜索命令 / 名称 / 描述"
          style="width: 280px"
          clearable
          @input="loadManual"
        />
      </div>
    </template>

    <el-table v-if="items.length" :data="items" stripe style="width: 100%">
      <el-table-column prop="category" label="分类" width="200" />
      <el-table-column prop="name" label="名称" width="180" />
      <el-table-column label="命令" min-width="250">
        <template #default="{ row }">
          <code class="cmd">{{ row.command }}</code>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="说明" min-width="200" />
      <el-table-column width="80">
        <template #default="{ row }">
          <el-button size="small" @click="copyCmd(row.command)">复制</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-else description="选择厂商开始浏览命令速查" />
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getManualList, type ManualItem } from '@/api'

const vendor = ref('huawei')
const keyword = ref('')
const items = ref<ManualItem[]>([])

onMounted(() => loadManual())

async function loadManual() {
  try {
    const res = await getManualList(vendor.value, keyword.value)
    items.value = res.items
  } catch {
    ElMessage.error('加载失败')
  }
}

function copyCmd(cmd: string) {
  navigator.clipboard.writeText(cmd)
  ElMessage.success('已复制')
}
</script>

<style scoped>
.manual-header { display: flex; align-items: center; gap: 12px; }
.manual-header .title { font-size: 16px; font-weight: bold; flex: 1; }
.cmd { color: #409eff; font-family: 'Consolas', monospace; font-size: 12px; }
</style>

<template>
  <div class="diag-page">
    <div class="diag-header">
      <el-button text @click="$router.push('/diagnostics')">← 返回诊断中心</el-button>
      <h2>📏 MTU 路径发现</h2>
    </div>

    <el-card class="param-card">
      <el-form :inline="true" size="default">
        <el-form-item label="目标地址">
          <el-input v-model="target" placeholder="8.8.8.8" style="width:200px" />
        </el-form-item>
        <el-form-item label="最小 MTU">
          <el-input-number v-model="minMtu" :min="68" :max="1500" /> bytes
        </el-form-item>
        <el-form-item label="最大 MTU">
          <el-input-number v-model="maxMtu" :min="68" :max="9000" /> bytes
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startDiag" :loading="isRunning">开始探测</el-button>
          <el-button v-if="isRunning" type="danger" @click="stop">停止</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 最终结果 -->
    <el-alert v-if="pathMtu" :title="`路径 MTU = ${pathMtu} bytes`" type="success" :closable="false" show-icon style="margin:12px 0" />

    <el-table :data="results" style="margin-top:12px" v-if="results.length" size="small" border max-height="450">
      <el-table-column prop="mtu" label="MTU" width="100" />
      <el-table-column label="结果" width="100" align="center">
        <template #default="{row}">
          <el-tag :type="row.success?'success':'danger'" size="small">{{ row.success ? '通过' : row.error || '失败' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="rtt_ms" label="延迟" width="80" align="center">
        <template #default="{row}">{{ row.success ? row.rtt_ms+'ms' : '-' }}</template>
      </el-table-column>
      <el-table-column label="进度" min-width="200">
        <template #default="{row}">
          <div class="mtu-bar">
            <div :class="'bar-fill '+(row.success?'ok':'fail')" :style="{width:Math.min(100,(row.mtu/1500*100))+'%'}">{{ row.mtu }}</div>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!isRunning && !results.length" description="输入目标IP，二分法探测路径MTU" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSseStream } from '@/composables/useSseStream'

const target = ref('')
const minMtu = ref(68)
const maxMtu = ref(1500)

interface MtuItem { mtu: number; success: boolean; rtt_ms: number; error: string; current_best: number; fragmented: boolean }
const results = ref<MtuItem[]>([])
const pathMtu = ref(0)
const sseUrl = computed(() => `/api/v1/diagnostics/mtu/stream?target=${encodeURIComponent(target.value)}&min_mtu=${minMtu.value}&max_mtu=${maxMtu.value}`)
const { isRunning, start, stop } = useSseStream<MtuItem>(sseUrl as any)

function startDiag() {
    results.value = []
    pathMtu.value = 0
    const s = useSseStream<MtuItem>(sseUrl.value)
    s.onProgress = (d) => { results.value.push(d) }
    s.onComplete = (_d) => {
        // 找到最大的 successful mtu
        const best = results.value.filter(r => r.success).map(r => r.mtu)
        pathMtu.value = best.length ? Math.max(...best) : 0
    }
    s.start()
}
</script>

<style scoped>
.diag-page { padding: 24px; max-width: 1100px; margin: 0 auto; }
.diag-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.diag-header h2 { margin: 0; font-size: 20px; }
.param-card { margin-bottom: 12px; }
.mtu-bar { height: 20px; background: #f0f0f0; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; font-size: 11px; line-height: 20px; text-align: center; color: #fff; transition: width .3s; }
.bar-fill.ok { background: #67c23a; }
.bar-fill.fail { background: #f56c6c; }
</style>

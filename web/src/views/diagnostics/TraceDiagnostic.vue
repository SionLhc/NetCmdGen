<template>
  <div class="diag-page">
    <div class="diag-header">
      <el-button text @click="$router.push('/diagnostics')">← 返回诊断中心</el-button>
      <h2>🗺️ 路由追踪</h2>
    </div>
    <TraceMap />
  </div>
</template>

<script setup lang="ts">
import TraceMap from '@/components/diagnostics/TraceMap.vue'
</script>

<style scoped>
.diag-page { padding: 24px; max-width: 1200px; margin: 0 auto; }
.diag-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.diag-header h2 { margin: 0; font-size: 20px; }
</style>

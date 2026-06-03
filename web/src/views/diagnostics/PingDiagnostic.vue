<template>
  <div class="diag-page">
    <div class="diag-header">
      <el-button text @click="$router.push('/diagnostics')">← 返回诊断中心</el-button>
      <h2>📡 Ping 实时诊断</h2>
    </div>
    <PingProbe />
  </div>
</template>

<script setup lang="ts">
import PingProbe from '@/components/diagnostics/PingProbe.vue'
</script>

<style scoped>
.diag-page { padding: 24px; max-width: 1200px; margin: 0 auto; }
.diag-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.diag-header h2 { margin: 0; font-size: 20px; }
</style>

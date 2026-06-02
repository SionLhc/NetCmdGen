<template>
  <div class="stat-box">
    <div class="lbl">{{ label }}</div>
    <div class="val" :style="{ color: c || '#303133' }">{{ v || '--' }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; v: any; c?: string }>()
</script>

<style scoped>
.stat-box{background:#f5f7fa;border:1px solid #ebeef5;border-radius:10px;padding:10px 16px;text-align:center;min-width:80px}
.lbl{font-size:11px;color:#909399;margin-bottom:2px}
.val{font-size:20px;font-weight:700}
</style>

<template>
  <div class="diagnostics-page">
    <!-- 页头 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 16v-4"/><path d="M12 8h.01"/>
          </svg>
          网络诊断
        </h1>
        <p class="page-subtitle">实时 Ping 探测 &middot; 路由追踪可视化</p>
      </div>
      <div class="header-right">
        <el-tooltip content="Ping 使用 ICMP 协议测试网络连通性，追踪使用 TTL 递增逐跳探测路由路径" placement="bottom">
          <el-tag type="info" size="small" style="cursor:help">💡 使用说明</el-tag>
        </el-tooltip>
      </div>
    </div>

    <!-- 双栏看板 -->
    <div class="dashboard-grid">
      <!-- 左栏：Ping -->
      <div class="dashboard-card ping-card">
        <div class="card-label">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="label-icon">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="2" x2="12" y2="6"/>
            <line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
          </svg>
          Ping 探测
        </div>
        <PingProbe />
      </div>

      <!-- 右栏：Traceroute -->
      <div class="dashboard-card trace-card">
        <div class="card-label">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="label-icon">
            <circle cx="12" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><circle cx="5" cy="19" r="2"/>
            <line x1="12" y1="7" x2="7" y2="16"/><line x1="12" y1="7" x2="17" y2="16"/>
          </svg>
          路由追踪
        </div>
        <TraceMap />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import PingProbe from '@/components/diagnostics/PingProbe.vue'
import TraceMap from '@/components/diagnostics/TraceMap.vue'
</script>

<style scoped>
.diagnostics-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* 页头 */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-icon {
  width: 24px;
  height: 24px;
  color: #6366f1;
}
.page-subtitle {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 2px;
}

/* 双栏布局 */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

@media (max-width: 960px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

.dashboard-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card-label {
  font-size: 15px;
  font-weight: 700;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 8px;
}
.label-icon {
  width: 20px;
  height: 20px;
  color: #6366f1;
}
</style>

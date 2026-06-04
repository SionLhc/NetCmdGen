<template>
  <div class="diag-home">
    <h2>🔬 网络诊断中心</h2>
    <p class="subtitle">对企业网络链路进行全面诊断，Ping / 路由追踪 / DNS / TCP端口 / HTTP / MTU / 抖动 / 历史趋势</p>

    <!-- 路由守卫重定向提示 -->
    <el-alert v-if="unavailableName" type="warning" :closable="true" show-icon style="margin-bottom:16px">
      <template #title>「{{ unavailableName }}」功能暂未开放</template>
      当前版本仅支持 Ping 诊断和路由追踪，其余功能正在开发中，敬请期待。
    </el-alert>

    <div class="tool-grid">
      <!-- Ping：可用 -->
      <router-link to="/diagnostics/ping" class="tool-card">
        <div class="tc-icon">📡</div>
        <div class="tc-name">Ping 诊断</div>
        <div class="tc-desc">ICMP 连通性测试 · ECharts 延迟波形图 · 丢包率统计</div>
        <div class="tc-status"><span class="dot ok" /> 可用</div>
      </router-link>

      <!-- Traceroute：可用 -->
      <router-link to="/diagnostics/traceroute" class="tool-card">
        <div class="tc-icon">🗺️</div>
        <div class="tc-name">路由追踪</div>
        <div class="tc-desc">逐跳 Traceroute · 节点路径可视化 · 每跳延迟柱状图</div>
        <div class="tc-status"><span class="dot ok" /> 可用</div>
      </router-link>

      <!-- DNS：可用 -->
      <router-link to="/diagnostics/dns" class="tool-card">
        <div class="tc-icon">🌐</div>
        <div class="tc-name">DNS 诊断</div>
        <div class="tc-desc">多记录类型 × 多解析器 · 8 个公共 DNS 对比 · 响应时间矩阵</div>
        <div class="tc-status"><span class="dot ok" /> 可用</div>
      </router-link>

      <!-- TCP Port：可用 -->
      <router-link to="/diagnostics/tcp-port" class="tool-card">
        <div class="tc-icon">🔌</div>
        <div class="tc-name">TCP 端口检测</div>
        <div class="tc-desc">端口连通 + 服务识别 + 风险评级 · 快捷预设（Web/全栈/远程）</div>
        <div class="tc-status"><span class="dot ok" /> 可用</div>
      </router-link>

      <!-- HTTP：可用 -->
      <router-link to="/diagnostics/http" class="tool-card">
        <div class="tc-icon">🌍</div>
        <div class="tc-name">HTTP 可用性</div>
        <div class="tc-desc">状态码 / 响应时间 / SSL 证书 / 重定向链 · GET/HEAD 探测</div>
        <div class="tc-status"><span class="dot ok" /> 可用</div>
      </router-link>

      <!-- MTU：可用 -->
      <router-link to="/diagnostics/mtu" class="tool-card">
        <div class="tc-icon">📏</div>
        <div class="tc-name">MTU 发现</div>
        <div class="tc-desc">二分法 DF 位探测 · 递增包大小 · 可视化进度条</div>
        <div class="tc-status"><span class="dot ok" /> 可用</div>
      </router-link>

      <!-- Jitter：可用 -->
      <router-link to="/diagnostics/jitter" class="tool-card">
        <div class="tc-icon">📊</div>
        <div class="tc-name">抖动分析</div>
        <div class="tc-desc">高频 Ping · RFC 3550 Jitter 计算 · ECharts 双轴对比图</div>
        <div class="tc-status"><span class="dot ok" /> 可用</div>
      </router-link>

      <!-- History：可用 -->
      <router-link to="/diagnostics/history" class="tool-card">
        <div class="tc-icon">📈</div>
        <div class="tc-name">历史趋势</div>
        <div class="tc-desc">多目标多时段对比 · 异常事件标注 · 延迟/丢包趋势图</div>
        <div class="tc-status"><span class="dot ok" /> 可用</div>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

/** 如果通过路由守卫跳转回来（?unavailable=xxx），显示友好提示 */
const nameMap: Record<string, string> = {
  dns: 'DNS 诊断', 'tcp-port': 'TCP 端口检测', http: 'HTTP 可用性',
  mtu: 'MTU 发现', jitter: '抖动分析', history: '历史趋势',
}
const unavailableName = computed(() => {
  const key = route.query.unavailable as string
  return nameMap[key] || ''
})
</script>

<style scoped>
.diag-home { padding: 32px; max-width: 1200px; margin: 0 auto; }
.diag-home h2 { font-size: 24px; margin-bottom: 4px; }
.subtitle { color: #909399; font-size: 14px; margin-bottom: 28px; }
.tool-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }

/* 可用工具卡片 */
.tool-card {
  background: #fff; border: 1px solid #e8ecf1; border-radius: 12px;
  padding: 20px; text-decoration: none; color: inherit;
  transition: all .2s; display: flex; flex-direction: column; gap: 8px;
  cursor: pointer;
}
.tool-card:hover {
  border-color: #409eff; box-shadow: 0 4px 12px rgba(64,158,255,.15);
  transform: translateY(-2px);
}

/* 不可用工具卡片 */
.tool-card.disabled {
  opacity: .55; background: #fafafa; cursor: not-allowed;
  pointer-events: none; user-select: none;
}
.tool-card.disabled:hover { border-color: #e8ecf1; box-shadow: none; transform: none; }
.tool-card.disabled .tc-icon { filter: grayscale(1); }
.tool-card.disabled .tc-name { color: #c0c4cc; }
.tool-card.disabled .tc-desc { color: #c0c4cc; }

.tc-icon { font-size: 32px; }
.tc-name { font-size: 16px; font-weight: 600; }
.tc-desc { font-size: 12px; color: #909399; line-height: 1.5; }
.tc-status {
  font-size: 11px; color: #909399; border-top: 1px solid #f0f0f0;
  padding-top: 8px; font-weight: 500;
}
.tool-card.disabled .tc-status { color: #c0c4cc; border-top-color: #e8e8e8; }

.dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 4px; }
.dot.ok { background: #67c23a; }
.dot.na { background: #c0c4cc; }
</style>

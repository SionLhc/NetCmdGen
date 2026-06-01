<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">NetCmdGen</span>
      </div>
      <el-menu
        :default-active="route.path"
        mode="horizontal"
        router
        class="header-menu"
      >
        <el-menu-item index="/">工作台</el-menu-item>
        <el-menu-item index="/topology">拓扑画图</el-menu-item>
        <el-menu-item index="/tools">网络工具</el-menu-item>
        <el-menu-item index="/manual">命令速查</el-menu-item>
      </el-menu>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
    <el-footer class="app-footer">
      <span>NetCmdGen v0.1.0 — 多厂商网络配置命令生成与网络工具集</span>
    </el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: 'Microsoft YaHei UI', 'PingFang SC', sans-serif; }

.app-container { height: 100vh; display: flex; flex-direction: column; }
.app-header {
  display: flex; align-items: center; gap: 24px;
  background: linear-gradient(135deg, #1e88e5, #0d47a1);
  padding: 0 24px; height: 56px !important;
  border-bottom: 2px solid #1565c0;
}
.logo { display: flex; align-items: center; gap: 8px; color: #fff; font-size: 20px; font-weight: bold; }
.logo-icon { font-size: 24px; }
.logo-text { letter-spacing: 1px; }
.header-menu {
  flex: 1; background: transparent !important; border: none !important;
}
.header-menu .el-menu-item {
  color: rgba(255,255,255,0.85) !important; font-size: 14px;
}
.header-menu .el-menu-item:hover,
.header-menu .el-menu-item.is-active {
  color: #fff !important; background: rgba(255,255,255,0.15) !important;
}
.app-main { flex: 1; background: #f5f7fa; padding: 16px; overflow: auto; }
.app-footer {
  text-align: center; color: #909399; font-size: 12px;
  height: 36px !important; line-height: 36px;
  background: #fff; border-top: 1px solid #e4e7ed;
}
</style>

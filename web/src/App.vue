<template>
  <div class="app-shell">
    <!-- 侧边导航 -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-icon-wrap">
          <svg viewBox="0 0 32 32" class="logo-svg"><rect x="4" y="4" width="24" height="24" rx="6" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="18" r="3" fill="currentColor"/><circle cx="21" cy="18" r="3" fill="currentColor"/><line x1="12" y1="11" x2="12" y2="14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><line x1="21" y1="11" x2="21" y2="14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </div>
        <span class="logo-text">NetCmdGen</span>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" active-class="nav-active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
          <span>命令工作台</span>
        </router-link>
        <router-link to="/topology" class="nav-item" active-class="nav-active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><line x1="12" y1="7" x2="7" y2="16"/><line x1="12" y1="7" x2="17" y2="16"/></svg>
          <span>拓扑画图</span>
        </router-link>
        <router-link to="/tools" class="nav-item" active-class="nav-active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
          <span>网络工具</span>
        </router-link>
        <router-link to="/manual" class="nav-item" active-class="nav-active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
          <span>命令速查</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="version-tag">v0.2.0</div>
      </div>
    </aside>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts"></script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif; background: #f0f2f5; -webkit-font-smoothing: antialiased; }

:root { --el-color-primary: #6366f1; --el-color-primary-light-3: #818cf8; --el-color-primary-light-5: #a5b4fc; --el-border-radius-base: 8px; }

.el-button--primary { background: linear-gradient(135deg, #6366f1, #4f46e5) !important; border: none !important; box-shadow: 0 2px 8px rgba(99,102,241,0.3) !important; }
.el-button--primary:hover { box-shadow: 0 4px 16px rgba(99,102,241,0.45) !important; }
.el-tabs__active-bar { background: #6366f1 !important; }
.el-tabs__item.is-active { color: #6366f1 !important; }
.el-divider__text { background: #f8f9fb !important; }

.app-shell { display: flex; height: 100vh; overflow: hidden; }

.sidebar { width: 220px; height: 100vh; background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); display: flex; flex-direction: column; flex-shrink: 0; border-right: 1px solid rgba(255,255,255,0.06); }
.sidebar-logo { display: flex; align-items: center; gap: 10px; padding: 20px 20px 24px; }
.logo-icon-wrap { width: 36px; height: 36px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(99,102,241,0.4); }
.logo-svg { width: 22px; height: 22px; color: #fff; }
.logo-text { font-size: 18px; font-weight: 700; color: #f1f5f9; letter-spacing: 0.5px; }

.sidebar-nav { flex: 1; display: flex; flex-direction: column; gap: 2px; padding: 0 12px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 14px; font-weight: 500; transition: all 0.2s ease; }
.nav-item:hover { background: rgba(255,255,255,0.06); color: #e2e8f0; }
.nav-active { background: rgba(99,102,241,0.15) !important; color: #a5b4fc !important; }
.nav-active .nav-icon { color: #818cf8; }
.nav-icon { width: 20px; height: 20px; flex-shrink: 0; }

.sidebar-footer { padding: 16px 20px; border-top: 1px solid rgba(255,255,255,0.06); }
.version-tag { font-size: 11px; color: #475569; text-align: center; }

.main-content { flex: 1; overflow: auto; padding: 20px 24px; background: #f0f2f5; }
</style>

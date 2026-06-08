<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-icon-wrap">
          <svg viewBox="0 0 32 32" class="logo-svg"><rect x="4" y="4" width="24" height="24" rx="6" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="18" r="3" fill="currentColor"/><circle cx="21" cy="18" r="3" fill="currentColor"/><line x1="12" y1="11" x2="12" y2="14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><line x1="21" y1="11" x2="21" y2="14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </div>
        <div class="logo-text-area">
          <span class="logo-text">NetCmdGen</span>
          <span class="logo-sub">网络命令生成器</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">
          <router-link to="/" class="nav-item" exact-active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            <span>首页</span>
          </router-link>
          <router-link to="/dashboard" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
            <span>工作台</span>
          </router-link>
        </div>

        <div class="nav-section">
          <div class="nav-label">核心工作台</div>
          <router-link to="/topology" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><line x1="12" y1="7" x2="7" y2="16"/><line x1="12" y1="7" x2="17" y2="16"/></svg>
            <span>拓扑画图</span>
          </router-link>
          <router-link to="/generate" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
            <span>命令工作台</span>
          </router-link>
        </div>

        <div class="nav-section">
          <div class="nav-label">网络工具</div>
          <router-link to="/diagnostics" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
            <span>网络诊断</span>
          </router-link>
          <router-link to="/tools" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            <span>网络工具</span>
          </router-link>
          <router-link to="/manual" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
            <span>命令速查</span>
          </router-link>
        </div>

        <div class="nav-section">
          <div class="nav-label">运维工具</div>
          <router-link to="/bigscreen" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            <span>态势大屏</span>
          </router-link>
          <router-link to="/ipam" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6" y2="6.01"/><line x1="6" y1="18" x2="6" y2="18.01"/></svg>
            <span>IP 管理</span>
          </router-link>
          <router-link to="/batch" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/></svg>
            <span>批量命令</span>
          </router-link>
          <router-link to="/backup" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>配置备份</span>
          </router-link>
          <router-link to="/health" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            <span>网络巡检</span>
          </router-link>
          <router-link to="/ros" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            <span>SNMP 监控</span>
          </router-link>
          <router-link to="/scheduler" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <span>计划任务</span>
          </router-link>
          <router-link to="/alert" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
            <span>告警配置</span>
          </router-link>
          <router-link to="/security" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            <span>安全基线</span>
          </router-link>
          <router-link to="/rack" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="4" height="18"/><rect x="10" y="3" width="4" height="18"/><rect x="18" y="3" width="4" height="18"/><line x1="2" y1="9" x2="6" y2="9"/><line x1="2" y1="15" x2="6" y2="15"/></svg>
            <span>机柜管理</span>
          </router-link>
          <router-link to="/ssh" class="nav-item" active-class="nav-active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
            <span>SSH 终端</span>
          </router-link>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="version-badge">v0.2.0</div>
        <div class="footer-divider"></div>
        <span class="footer-text">MIT · 社区共建</span>
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
:root { --el-color-primary: #6366f1; --el-color-primary-light-3: #818cf8; --el-border-radius-base: 8px; }
.el-button { border-radius: 8px; font-weight: 500; }
.el-button--primary { background: linear-gradient(135deg, #6366f1, #4f46e5) !important; border: none !important; color: #fff !important; box-shadow: 0 2px 8px rgba(99,102,241,0.3) !important; }
.el-button--primary:hover { box-shadow: 0 4px 16px rgba(99,102,241,0.45) !important; transform: translateY(-1px); }
.el-tabs__active-bar { background: #6366f1 !important; }
.el-tabs__item.is-active { color: #6366f1 !important; }

.app-shell { display: flex; height: 100vh; overflow: hidden; }

/* ═══ Sidebar ═══ */
.sidebar {
  width: 220px; height: 100vh;
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 60%, #0f172a 100%);
  display: flex; flex-direction: column; flex-shrink: 0;
  border-right: 1px solid rgba(255,255,255,0.04);
  overflow-y: auto;
}
.sidebar::-webkit-scrollbar { width: 0; }

/* Logo */
.sidebar-logo {
  display: flex; align-items: center; gap: 12px;
  padding: 22px 18px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.logo-icon-wrap {
  width: 36px; height: 36px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(99,102,241,0.4);
}
.logo-svg { width: 22px; height: 22px; color: #fff; }
.logo-text-area { display: flex; flex-direction: column; }
.logo-text { font-size: 17px; font-weight: 700; color: #f1f5f9; letter-spacing: 0.5px; line-height: 1.2; }
.logo-sub { font-size: 10px; color: #64748b; font-weight: 500; }

/* Nav */
.sidebar-nav { flex: 1; padding: 12px 10px; display: flex; flex-direction: column; gap: 4px; }

.nav-section { margin-bottom: 6px; }
.nav-label {
  font-size: 10px; font-weight: 600; color: #475569; text-transform: uppercase;
  letter-spacing: 1px; padding: 8px 14px 6px;
}

.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 14px; border-radius: 8px;
  color: #94a3b8; text-decoration: none;
  font-size: 13px; font-weight: 500;
  transition: all 0.15s ease;
  position: relative;
  margin: 1px 0;
}
.nav-item:hover { background: rgba(255,255,255,0.05); color: #cbd5e1; }

/* Active state — left border + gradient background + icon color */
.nav-active {
  background: rgba(99,102,241,0.12) !important;
  color: #a5b4fc !important;
  font-weight: 600 !important;
}
.nav-active::before {
  content: '';
  position: absolute; left: -10px; top: 50%; transform: translateY(-50%);
  width: 3px; height: 20px;
  background: linear-gradient(180deg, #6366f1, #a855f7);
  border-radius: 0 4px 4px 0;
}

.nav-icon { width: 20px; height: 20px; flex-shrink: 0; transition: color 0.15s; }
.nav-active .nav-icon { color: #818cf8; }

/* Footer */
.sidebar-footer {
  padding: 14px 18px;
  border-top: 1px solid rgba(255,255,255,0.06);
  display: flex; align-items: center; gap: 8px;
}
.version-badge {
  font-size: 10px; font-weight: 700; color: #818cf8;
  background: rgba(99,102,241,0.15); padding: 2px 8px; border-radius: 4px;
  letter-spacing: 0.5px;
}
.footer-divider { flex: 1; height: 1px; background: rgba(255,255,255,0.06); }
.footer-text { font-size: 10px; color: #475569; white-space: nowrap; }

/* Main */
.main-content { flex: 1; overflow: auto; padding: 20px 24px; background: #f0f2f5; }
</style>

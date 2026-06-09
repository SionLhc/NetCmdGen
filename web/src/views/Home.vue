<template>
  <div class="home-page">
    <section class="hero">
      <div class="hero-badge">🚀 开源网络运维工具 · MIT License</div>
      <h1 class="hero-title">画拓扑、勾参数<br>一键生成多厂商命令</h1>
      <p class="hero-desc">
        拖拽设备画拓扑 → 勾选配置特性 → 自动输出华为/H3C/锐捷/迈普/RouterOS/Cisco/TP-LINK/Juniper 可执行脚本。
        支持 <strong>8 大厂商</strong>、<strong>30 套模板</strong>、<strong>38 个工具</strong>、<strong>3.6k 命令速查</strong>，完全免费。
      </p>
      <div class="hero-actions">
        <router-link to="/topology" class="hero-btn primary">
          <svg class="btn-icon" viewBox="0 0 28 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="6" r="3"/><circle cx="19" cy="4" r="3"/><circle cx="13" cy="14" r="3"/><line x1="8" y1="9" x2="12" y2="11"/><line x1="16" y1="7" x2="12" y2="11"/></svg>
          开始画拓扑
        </router-link>
        <router-link to="/diagnostics" class="hero-btn accent">
          <svg class="btn-icon" viewBox="0 0 28 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 5v5l4.5 2.5"/></svg>
          网络诊断
        </router-link>
        <router-link to="/generate" class="hero-btn outline">
          <svg class="btn-icon" viewBox="0 0 28 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 16 9 10 3 4"/><line x1="14" y1="17" x2="24" y2="17"/></svg>
          直接生成命令
        </router-link>
      </div>
    </section>

    <section class="features">
      <h2 class="section-title">核心能力</h2>
      <div class="feature-grid">
        <div class="feature-card" v-for="f in features" :key="f.title">
          <div class="feature-icon" :style="{ background: f.bg }">{{ f.emoji }}</div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <section class="vendors">
      <h2 class="section-title">支持厂商</h2>
      <div class="vendor-row">
        <span class="vendor-chip" v-for="v in vendors" :key="v.code" :style="{ color: v.color, background: v.bg }">{{ v.name }}</span>
      </div>
      <p class="vendor-note">命令引擎完全开源，社区可贡献新厂商模板</p>
    </section>

    <section class="stats">
      <div class="stat-item"><span class="stat-num">8</span><span class="stat-label">厂商支持</span></div>
      <div class="stat-divider"></div>
      <div class="stat-item"><span class="stat-num">30</span><span class="stat-label">预设模板</span></div>
      <div class="stat-divider"></div>
      <div class="stat-item"><span class="stat-num">38</span><span class="stat-label">网络工具</span></div>
      <div class="stat-divider"></div>
      <div class="stat-item"><span class="stat-num">3.6k</span><span class="stat-label">命令速查</span></div>
    </section>

    <footer class="footer">网络运维工具箱 · MIT License · 社区共建</footer>
  </div>
</template>

<script setup lang="ts">
const features = [
  { emoji:'🗺',title:'拓扑画图',desc:'拖拽22种设备、连线画拓扑，分组容器/MiniMap/撤销重做/导出PNG',bg:'linear-gradient(135deg,#dbeafe,#bfdbfe)' },
  { emoji:'⚡',title:'多厂商命令',desc:'华为/H3C/锐捷/迈普/RouterOS/Cisco/TP-LINK/Juniper 一键生成',bg:'linear-gradient(135deg,#d1fae5,#a7f3d0)' },
  { emoji:'📡',title:'网络诊断看板',desc:'Ping实时流+Traceroute逐跳追踪，ECharts延迟波形图与丢包率可视化',bg:'linear-gradient(135deg,#fce7f3,#fbcfe8)' },
  { emoji:'🛠',title:'网络工具集',desc:'子网/IPv6/带宽/光纤/正则/VLAN批量/DNS等 38合1',bg:'linear-gradient(135deg,#e0e7ff,#c7d2fe)' },
  { emoji:'📋',title:'配置模板库',desc:'30套预设场景：园区核心/接入/路由器/防火墙/RouterOS开局模板',bg:'linear-gradient(135deg,#fef3c7,#fde68a)' },
  { emoji:'📖',title:'命令速查',desc:'8厂商 3600+条命令，按版本过滤(VRP V5/V8/V300,Comware V5/V7)',bg:'linear-gradient(135deg,#f3e8ff,#e9d5ff)' },
]
const vendors = [
  { code:'huawei',name:'华为 Huawei',color:'#dc2626',bg:'#fef2f2' },
  { code:'h3c',name:'华三 H3C',color:'#2563eb',bg:'#eff6ff' },
  { code:'ruijie',name:'锐捷 Ruijie',color:'#059669',bg:'#ecfdf5' },
  { code:'maipu',name:'迈普 Maipu',color:'#d97706',bg:'#fffbeb' },
  { code:'routeros',name:'RouterOS',color:'#e11d48',bg:'#fff1f2' },
  { code:'cisco',name:'Cisco',color:'#0369a1',bg:'#f0f9ff' },
  { code:'tplink',name:'TP-LINK',color:'#15803d',bg:'#f0fdf4' },
  { code:'juniper',name:'Juniper',color:'#4d7c0f',bg:'#f7fee7' },
]
</script>

<style scoped>
.home-page { max-width: 960px; margin: 0 auto; }
.hero { text-align: center; padding: 48px 24px 40px; }
.hero-badge { display: inline-block; padding: 5px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; background: #eef2ff; color: #6366f1; margin-bottom: 20px; }
.hero-title { font-size: 42px; font-weight: 800; color: #0f172a; line-height: 1.25; margin-bottom: 16px; letter-spacing: -0.5px; }
.hero-desc { font-size: 16px; color: #64748b; line-height: 1.7; max-width: 620px; margin: 0 auto 32px; }
.hero-actions { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }
.hero-btn { display: inline-flex; align-items: center; gap: 8px; padding: 12px 28px; border-radius: 10px; font-size: 15px; font-weight: 600; text-decoration: none; transition: all .2s; }
.btn-icon { width: 22px; height: 16px; flex-shrink: 0; }
.hero-btn.primary { background: linear-gradient(135deg,#6366f1,#4f46e5); color: #fff; box-shadow: 0 4px 16px rgba(99,102,241,.3); }
.hero-btn.primary:hover { box-shadow: 0 6px 24px rgba(99,102,241,.45); transform: translateY(-1px); }
.hero-btn.accent { background: linear-gradient(135deg,#f59e0b,#d97706); color: #fff; box-shadow: 0 4px 12px rgba(245,158,11,.3); }
.hero-btn.accent:hover { box-shadow: 0 6px 20px rgba(245,158,11,.4); transform: translateY(-1px); }
.hero-btn.outline { border: 2px solid #e2e8f0; color: #334155; background: #fff; }
.hero-btn.outline:hover { border-color: #6366f1; color: #6366f1; }
.section-title { text-align: center; font-size: 22px; font-weight: 700; color: #0f172a; margin: 16px 0 20px; }
.features { padding: 24px 0; }
.feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.feature-card { background: #fff; border-radius: 14px; padding: 28px 22px; border: 1px solid #f1f5f9; transition: all .2s; }
.feature-card:hover { box-shadow: 0 8px 24px rgba(0,0,0,.06); border-color: #e2e8f0; transform: translateY(-2px); }
.feature-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 14px; }
.feature-card h3 { font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.feature-card p { font-size: 13px; color: #64748b; line-height: 1.6; }
.vendors { padding: 32px 0 16px; }
.vendor-row { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.vendor-chip { padding: 8px 22px; border-radius: 8px; font-size: 14px; font-weight: 600; }
.vendor-note { text-align: center; font-size: 12px; color: #94a3b8; margin-top: 14px; }
.stats { display: flex; gap: 0; justify-content: center; align-items: center; padding: 28px 0; margin: 24px 0; background: #fff; border-radius: 14px; border: 1px solid #f1f5f9; }
.stat-item { text-align: center; padding: 0 32px; }
.stat-num { display: block; font-size: 32px; font-weight: 800; color: #6366f1; }
.stat-label { display: block; font-size: 13px; color: #94a3b8; margin-top: 4px; }
.stat-divider { width: 1px; height: 40px; background: #e2e8f0; }
.footer { text-align: center; padding: 24px 0 40px; color: #94a3b8; font-size: 13px; }
@media (max-width: 700px) {
  .feature-grid { grid-template-columns: 1fr; }
  .hero-title { font-size: 28px; }
  .stats { flex-direction: column; gap: 14px; }
  .stat-divider { width: 60px; height: 1px; }
}
</style>

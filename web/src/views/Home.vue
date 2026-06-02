<template>
  <div class="home-page">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-badge">🚀 开源网络运维工具</div>
      <h1 class="hero-title">画拓扑、勾参数<br>一键生成多厂商命令</h1>
      <p class="hero-desc">
        告别手敲命令行。拖拽设备画拓扑 → 勾选配置特性 → 自动输出华为/H3C/思科/锐捷可执行脚本。
        支持 4 大厂商、6 大特性、15+ 配置模板，<strong>完全免费开源</strong>。
      </p>
      <div class="hero-actions">
        <router-link to="/topology" class="hero-btn primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><line x1="12" y1="7" x2="7" y2="16"/><line x1="12" y1="7" x2="17" y2="16"/></svg>
          开始画拓扑
        </router-link>
        <router-link to="/generate" class="hero-btn outline">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
          直接生成命令
        </router-link>
      </div>
    </section>

    <!-- 功能卡片 -->
    <section class="features">
      <h2 class="section-title">核心能力</h2>
      <div class="feature-grid">
        <div class="feature-card" v-for="f in featureList" :key="f.title">
          <div class="feature-icon" :style="{ background: f.bg }">{{ f.emoji }}</div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <!-- 厂商支持 -->
    <section class="vendors">
      <h2 class="section-title">支持厂商</h2>
      <div class="vendor-row">
        <span class="vendor-chip" v-for="v in vendorList" :key="v.code" :style="{ color: v.color, background: v.bg }">
          {{ v.name }}
        </span>
      </div>
    </section>

    <!-- 底部 CTA -->
    <section class="cta">
      <h2>开始使用 NetCmdGen</h2>
      <p>完全免费 · MIT 开源 · 社区驱动</p>
      <router-link to="/topology" class="hero-btn primary">立即体验</router-link>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <span>NetCmdGen v0.2.0 · MIT License · 社区共建</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
const featureList = [
  { emoji: '🗺', title: '拓扑画图',  desc: '拖拽设备、连线画拓扑，自动识别层次关系、推荐配置特性', bg: 'linear-gradient(135deg,#dbeafe,#bfdbfe)' },
  { emoji: '⚡', title: '多厂商命令', desc: '华为 / H3C / 锐捷 / 迈普 一键生成，含中文注释、风险提示', bg: 'linear-gradient(135deg,#d1fae5,#a7f3d0)' },
  { emoji: '📋', title: '配置模板库', desc: '15 套预设场景模板：园区核心/接入/路由器/防火墙/Voice VLAN 等', bg: 'linear-gradient(135deg,#fef3c7,#fde68a)' },
  { emoji: '🔗', title: '拓扑项目', desc: '拓扑导出→项目生成，保留原布局+连线，多设备批量统一配置', bg: 'linear-gradient(135deg,#e0e7ff,#c7d2fe)' },
  { emoji: '🛠', title: '网络工具集', desc: '子网计算 / Ping / Trace / 端口扫描 / DNS / MAC / 编码转换 9 合 1', bg: 'linear-gradient(135deg,#fce7f3,#fbcfe8)' },
  { emoji: '📖', title: '命令速查', desc: '4 厂商 2500+ 条网络命令，按特性分类检索，即查即用', bg: 'linear-gradient(135deg,#f3e8ff,#e9d5ff)' },
]

const vendorList = [
  { code: 'huawei', name: '华为', color: '#dc2626', bg: '#fef2f2' },
  { code: 'h3c',    name: 'H3C',  color: '#2563eb', bg: '#eff6ff' },
  { code: 'ruijie', name: '锐捷', color: '#059669', bg: '#ecfdf5' },
  { code: 'maipu',  name: '迈普', color: '#d97706', bg: '#fffbeb' },
]
</script>

<style scoped>
.home-page { max-width: 960px; margin: 0 auto; }

/* Hero */
.hero { text-align: center; padding: 48px 24px 40px; }
.hero-badge { display: inline-block; padding: 5px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; background: #eef2ff; color: #6366f1; margin-bottom: 20px; }
.hero-title { font-size: 42px; font-weight: 800; color: #0f172a; line-height: 1.25; margin-bottom: 16px; letter-spacing: -0.5px; }
.hero-desc { font-size: 16px; color: #64748b; line-height: 1.7; max-width: 620px; margin: 0 auto 32px; }
.hero-actions { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }
.hero-btn { display: inline-flex; align-items: center; gap: 8px; padding: 12px 28px; border-radius: 10px; font-size: 15px; font-weight: 600; text-decoration: none; transition: all .2s; }
.hero-btn svg { width: 20px; height: 20px; }
.hero-btn.primary { background: linear-gradient(135deg,#6366f1,#4f46e5); color: #fff; box-shadow: 0 4px 16px rgba(99,102,241,.3); }
.hero-btn.primary:hover { box-shadow: 0 6px 24px rgba(99,102,241,.45); transform: translateY(-1px); }
.hero-btn.outline { border: 2px solid #e2e8f0; color: #334155; background: #fff; }
.hero-btn.outline:hover { border-color: #6366f1; color: #6366f1; }

/* Sections */
.section-title { text-align: center; font-size: 24px; font-weight: 700; color: #0f172a; margin: 16px 0 24px; }

/* Features */
.features { padding: 24px 0; }
.feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.feature-card { background: #fff; border-radius: 14px; padding: 28px 22px; border: 1px solid #f1f5f9; transition: all .2s; }
.feature-card:hover { box-shadow: 0 8px 24px rgba(0,0,0,.06); border-color: #e2e8f0; transform: translateY(-2px); }
.feature-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; margin-bottom: 14px; }
.feature-card h3 { font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.feature-card p  { font-size: 13px; color: #64748b; line-height: 1.6; }

/* Vendors */
.vendors { padding: 32px 0 24px; }
.vendor-row { display: flex; gap: 12px; justify-content: center; }
.vendor-chip { padding: 8px 22px; border-radius: 8px; font-size: 15px; font-weight: 600; }

/* CTA */
.cta { text-align: center; padding: 48px 24px; margin: 32px 0; background: linear-gradient(135deg,#eef2ff,#e0e7ff); border-radius: 20px; }
.cta h2 { font-size: 28px; font-weight: 800; color: #1e293b; margin-bottom: 8px; }
.cta p  { color: #64748b; margin-bottom: 20px; }

/* Footer */
.footer { text-align: center; padding: 24px 0 40px; color: #94a3b8; font-size: 13px; }

@media (max-width: 700px) {
  .feature-grid { grid-template-columns: 1fr; }
  .hero-title { font-size: 30px; }
}
</style>

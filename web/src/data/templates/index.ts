/**
 * 配置模板加载器
 * 读取 JSON 模板文件，按场景返回预设配置
 */
import campusCore from './campus-core-switch.json'
import campusAccess from './campus-access-switch.json'
import exitRouter from './exit-router.json'
import firewallBasic from './firewall-basic.json'
import aggVrrp from './agg-switch-vrrp.json'
import accessVoice from './access-switch-voice.json'
import coreH3c from './core-switch-h3c.json'
import routerDualWan from './router-dual-wan.json'
import routerPppoe from './router-pppoe.json'
import fwTrustDmz from './firewall-trust-dmz.json'
import fwNat from './firewall-nat.json'
import coreRuijie from './core-switch-ruijie.json'
import aggH3c from './agg-switch-h3c.json'
import accessH3c from './access-switch-h3c.json'
import routerOspf from './router-ospf-multi-area.json'
// 新增模板
import accessRuijie from './access-switch-ruijie.json'
import aggRuijie from './agg-switch-ruijie.json'
import routerH3c from './router-h3c.json'
import routerH3cDW from './router-h3c-dualwan.json'
import routerRuijie from './router-ruijie.json'
import coreMaipu from './core-switch-maipu.json'
import accessMaipu from './access-switch-maipu.json'
import routerMaipu from './router-maipu.json'
import fwMaipu from './firewall-maipu.json'
import fwRuijie from './firewall-ruijie.json'
import coreDCSpine from './core-switch-dc-spine.json'
import aggL2 from './agg-switch-l2.json'
import rosV6Basic from './routeros-v6-basic.json'
import rosV7Ospf from './routeros-v7-ospf.json'

export interface TemplateDef {
    id: string
    scene: string
    name: string
    desc: string
    vendor: string
    config: Record<string, any>
}

const templates: TemplateDef[] = [
    /* ─── 华为 (14套) ─── */
    { id: 'campus-core',              ...campusCore } as TemplateDef,
    { id: 'campus-access',            ...campusAccess } as TemplateDef,
    { id: 'exit-router',              ...exitRouter } as TemplateDef,
    { id: 'firewall-basic',           ...firewallBasic } as TemplateDef,
    { id: 'agg-switch-vrrp',          ...aggVrrp } as TemplateDef,
    { id: 'access-switch-voice',      ...accessVoice } as TemplateDef,
    { id: 'router-dual-wan',          ...routerDualWan } as TemplateDef,
    { id: 'router-pppoe',             ...routerPppoe } as TemplateDef,
    { id: 'firewall-trust-dmz',       ...fwTrustDmz } as TemplateDef,
    { id: 'firewall-nat',             ...fwNat } as TemplateDef,
    { id: 'router-ospf-multi-area',   ...routerOspf } as TemplateDef,
    { id: 'core-dc-spine',            ...coreDCSpine } as TemplateDef,
    { id: 'agg-switch-l2',            ...aggL2 } as TemplateDef,
    /* ─── H3C (6套) ─── */
    { id: 'core-switch-h3c',          ...coreH3c } as TemplateDef,
    { id: 'agg-switch-h3c',           ...aggH3c } as TemplateDef,
    { id: 'access-switch-h3c',        ...accessH3c } as TemplateDef,
    { id: 'router-h3c',               ...routerH3c } as TemplateDef,
    { id: 'router-h3c-dualwan',       ...routerH3cDW } as TemplateDef,
    /* ─── 锐捷 (6套) ─── */
    { id: 'core-switch-ruijie',       ...coreRuijie } as TemplateDef,
    { id: 'access-switch-ruijie',     ...accessRuijie } as TemplateDef,
    { id: 'agg-switch-ruijie',        ...aggRuijie } as TemplateDef,
    { id: 'router-ruijie',            ...routerRuijie } as TemplateDef,
    { id: 'firewall-ruijie',          ...fwRuijie } as TemplateDef,
    /* ─── 迈普 (4套) ─── */
    { id: 'core-switch-maipu',        ...coreMaipu } as TemplateDef,
    { id: 'access-switch-maipu',      ...accessMaipu } as TemplateDef,
    { id: 'router-maipu',             ...routerMaipu } as TemplateDef,
    { id: 'firewall-maipu',           ...fwMaipu } as TemplateDef,
    /* ─── RouterOS (2套) ─── */
    { id: 'routeros-v6-basic',        ...rosV6Basic } as TemplateDef,
    { id: 'routeros-v7-ospf',         ...rosV7Ospf } as TemplateDef,
]

/** 获取全部模板列表 */
export function getAllTemplates(): TemplateDef[] {
    return templates
}

/** 按 ID 获取模板 */
export function getTemplateById(id: string): TemplateDef | undefined {
    return templates.find(t => t.id === id)
}

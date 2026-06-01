/**
 * 配置模板加载器
 * 读取 JSON 模板文件，按场景返回预设配置
 */
import campusCore from './campus-core-switch.json'
import campusAccess from './campus-access-switch.json'
import exitRouter from './exit-router.json'
import firewallBasic from './firewall-basic.json'

export interface TemplateDef {
    id: string
    scene: string
    name: string
    desc: string
    vendor: string
    config: Record<string, any>
}

const templates: TemplateDef[] = [
    { id: 'campus-core', ...campusCore } as TemplateDef,
    { id: 'campus-access', ...campusAccess } as TemplateDef,
    { id: 'exit-router', ...exitRouter } as TemplateDef,
    { id: 'firewall-basic', ...firewallBasic } as TemplateDef,
]

/** 获取全部模板列表 */
export function getAllTemplates(): TemplateDef[] {
    return templates
}

/** 按 ID 获取模板 */
export function getTemplateById(id: string): TemplateDef | undefined {
    return templates.find(t => t.id === id)
}

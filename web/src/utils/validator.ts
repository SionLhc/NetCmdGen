/**
 * 前端参数校验工具
 * 提供 VLAN ID 范围、IP 格式、端口名格式、子网冲突等实时校验
 */
import { ElMessage } from 'element-plus'

/** 校验结果类型 */
export interface ValidationResult {
    valid: boolean
    message: string
}

/** 单个字段的校验问题 */
export interface ValidationIssue {
    field: string      // 字段路径，如 'basic.hostname'
    message: string    // 错误提示
    severity: 'error' | 'warning'  // 严重程度
}

// ═══════════════════════════════════════════════
// 基础校验函数
// ═══════════════════════════════════════════════

/** 校验 VLAN ID 范围 (1-4094) */
export function validateVlanId(id: number): ValidationResult {
    if (!Number.isInteger(id)) {
        return { valid: false, message: 'VLAN ID 必须是整数' }
    }
    if (id < 1 || id > 4094) {
        return { valid: false, message: `VLAN ID ${id} 超出范围，允许值: 1-4094` }
    }
    return { valid: true, message: '有效' }
}

/** 校验 VLAN ID 列表，检测重复和范围 */
export function validateVlanIds(ids: number[]): ValidationResult {
    if (ids.length === 0) {
        return { valid: true, message: '无VLAN配置' }
    }

    // 检查重复
    const seen = new Set<number>()
    const duplicates: number[] = []
    for (const id of ids) {
        if (seen.has(id)) {
            duplicates.push(id)
        }
        seen.add(id)
    }
    if (duplicates.length > 0) {
        return { valid: false, message: `重复的 VLAN ID: ${duplicates.join(', ')}` }
    }

    // 检查范围
    for (const id of ids) {
        const result = validateVlanId(id)
        if (!result.valid) return result
    }

    return { valid: true, message: '有效' }
}

/** 校验 IP 地址格式 (xxx.xxx.xxx.xxx, 每段 0-255) */
export function validateIpAddress(ip: string): ValidationResult {
    if (!ip || ip.trim() === '') {
        return { valid: false, message: 'IP 地址不能为空' }
    }
    const pattern = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/
    const match = ip.trim().match(pattern)
    if (!match) {
        return { valid: false, message: 'IP 地址格式不正确，例: 192.168.1.1' }
    }
    for (let i = 1; i <= 4; i++) {
        const octet = parseInt(match[i], 10)
        if (octet < 0 || octet > 255) {
            return { valid: false, message: `IP 地址第 ${i} 段超出范围 (0-255)` }
        }
    }
    return { valid: true, message: '有效' }
}

/** 校验子网掩码 */
export function validateSubnetMask(mask: string): ValidationResult {
    if (!mask || mask.trim() === '') {
        return { valid: false, message: '子网掩码不能为空' }
    }
    const validMasks = [
        '255.255.255.255', '255.255.255.254', '255.255.255.252',
        '255.255.255.248', '255.255.255.240', '255.255.255.224',
        '255.255.255.192', '255.255.255.128', '255.255.255.0',
        '255.255.254.0', '255.255.252.0', '255.255.248.0',
        '255.255.240.0', '255.255.224.0', '255.255.192.0',
        '255.255.128.0', '255.255.0.0', '255.254.0.0',
        '255.252.0.0', '255.240.0.0', '255.224.0.0',
        '255.192.0.0', '255.128.0.0', '255.0.0.0',
    ]
    if (!validMasks.includes(mask.trim())) {
        return { valid: false, message: '子网掩码格式不正确或不是有效的连续掩码' }
    }
    return { valid: true, message: '有效' }
}

/** 校验 CIDR 前缀 */
export function validateCidrPrefix(prefix: number): ValidationResult {
    if (!Number.isInteger(prefix)) {
        return { valid: false, message: 'CIDR 前缀必须是整数' }
    }
    if (prefix < 0 || prefix > 32) {
        return { valid: false, message: 'CIDR 前缀范围: 0-32' }
    }
    return { valid: true, message: '有效' }
}

/** 端口名格式校验（华为/H3C/锐捷/思科通用） */
export function validatePortName(name: string): ValidationResult {
    if (!name || name.trim() === '') {
        return { valid: false, message: '端口名不能为空' }
    }
    // 支持多种厂商端口名格式
    const patterns = [
        /^GigabitEthernet\d+\/\d+\/\d+$/i,       // GigabitEthernet0/0/1
        /^XGigabitEthernet\d+\/\d+\/\d+$/i,       // XGigabitEthernet0/0/1
        /^Ethernet\d+\/\d+\/\d+$/i,                // Ethernet0/0/1
        /^Ten-GigabitEthernet\d+\/\d+\/\d+$/i,     // Ten-GigabitEthernet1/0/1
        /^Eth-Trunk\d+$/i,                         // Eth-Trunk1
        /^Vlanif\d+$/i,                            // Vlanif10
        /^LoopBack\d+$/i,                          // LoopBack0
        /^GE\d+\/\d+\/\d+$/i,                      // GE0/0/1
        /^XGE\d+\/\d+\/\d+$/i,                     // XGE0/0/1
    ]
    for (const pattern of patterns) {
        if (pattern.test(name.trim())) {
            return { valid: true, message: '有效' }
        }
    }
    return { valid: false, message: `端口名格式不正确，例: GigabitEthernet0/0/1, Eth-Trunk1` }
}

/** 校验主机名 */
export function validateHostname(name: string): ValidationResult {
    if (!name || name.trim() === '') {
        return { valid: false, message: '主机名不能为空' }
    }
    if (name.length > 64) {
        return { valid: false, message: '主机名不能超过 64 个字符' }
    }
    if (!/^[a-zA-Z][a-zA-Z0-9\-]*$/.test(name)) {
        return { valid: false, message: '主机名必须以字母开头，只能包含字母、数字和连字符' }
    }
    return { valid: true, message: '有效' }
}

/** 校验端口号范围 */
export function validatePortNumber(port: number): ValidationResult {
    if (!Number.isInteger(port)) {
        return { valid: false, message: '端口号必须是整数' }
    }
    if (port < 1 || port > 65535) {
        return { valid: false, message: '端口号范围: 1-65535' }
    }
    return { valid: true, message: '有效' }
}

// ═══════════════════════════════════════════════
// 高级校验：子网冲突检测
// ═══════════════════════════════════════════════

interface Subnet {
    ip: string      // 如 '192.168.1.0'
    prefix: number  // 如 24
    label: string   // 描述，如 'VLAN10'
}

/** 将 IP 字符串转换为 32 位整数 */
function ipToInt(ip: string): number {
    const parts = ip.split('.').map(Number)
    return ((parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]) >>> 0
}

/** 将 32 位整数转换为 IP 字符串 */
function intToIp(num: number): string {
    return [
        (num >> 24) & 0xff,
        (num >> 16) & 0xff,
        (num >> 8) & 0xff,
        num & 0xff,
    ].join('.')
}

/** 检测子网之间是否存在重叠冲突 */
export function detectSubnetConflicts(subnets: Subnet[]): ValidationIssue[] {
    const issues: ValidationIssue[] = []

    // 按 IP 排序
    const sorted = [...subnets].sort((a, b) => ipToInt(a.ip) - ipToInt(b.ip))

    for (let i = 0; i < sorted.length; i++) {
        for (let j = i + 1; j < sorted.length; j++) {
            const subnetA = sorted[i]
            const subnetB = sorted[j]

            const startA = ipToInt(subnetA.ip)
            const endA = startA + (1 << (32 - subnetA.prefix)) - 1
            const startB = ipToInt(subnetB.ip)
            const endB = startB + (1 << (32 - subnetB.prefix)) - 1

            // 检查重叠
            if (startA <= endB && startB <= endA) {
                // 完全相同不算冲突
                if (startA === startB && endA === endB) {
                    issues.push({
                        field: `subnet.${subnetA.label}`,
                        message: `子网 ${subnetA.label}(${subnetA.ip}/${subnetA.prefix}) 与 ${subnetB.label}(${subnetB.ip}/${subnetB.prefix}) 完全相同`,
                        severity: 'warning',
                    })
                } else {
                    issues.push({
                        field: `subnet.${subnetA.label}`,
                        message: `子网 ${subnetA.label}(${subnetA.ip}/${subnetA.prefix}) 与 ${subnetB.label}(${subnetB.ip}/${subnetB.prefix}) 存在重叠`,
                        severity: 'error',
                    })
                }
            }
        }
    }

    return issues
}

// ═══════════════════════════════════════════════
// 表单完整性校验（生成前预检）
// ═══════════════════════════════════════════════

/**
 * 生成命令前的预检查
 * @returns 校验问题列表
 */
export function validateBeforeGenerate(configs: Record<string, any>): ValidationIssue[] {
    const issues: ValidationIssue[] = []

    // 1. 主机名校验
    const hostname = configs.basic?.hostname
    if (hostname) {
        const result = validateHostname(hostname)
        if (!result.valid) {
            issues.push({ field: 'basic.hostname', message: result.message, severity: 'error' })
        }
    }

    // 2. 管理 IP 校验
    const mgmtIp = configs.basic?.mgmt_ip
    if (mgmtIp) {
        const result = validateIpAddress(mgmtIp)
        if (!result.valid) {
            issues.push({ field: 'basic.mgmt_ip', message: result.message, severity: 'error' })
        }
    }

    // 3. SSH 端口校验
    const sshPort = configs.basic?.ssh_port
    if (sshPort && configs.basic?.enable_ssh) {
        const result = validatePortNumber(sshPort)
        if (!result.valid) {
            issues.push({ field: 'basic.ssh_port', message: result.message, severity: 'error' })
        }
    }

    // 4. VLAN 校验
    const vlans = configs.vlan?.vlans as Array<{ id: number; name?: string }> | undefined
    if (vlans && vlans.length > 0) {
        // 检查 VLAN ID 范围和重复
        const ids = vlans.map(v => v.id)
        const result = validateVlanIds(ids)
        if (!result.valid) {
            issues.push({ field: 'vlan.vlans', message: result.message, severity: 'error' })
        }

        // 检查 VLANIF IP 与子网掩码
        const vlanifs = configs.vlan?.vlanifs as Array<{ vlan_id: number; ip_address: string; mask: string }> | undefined
        if (vlanifs && vlanifs.length > 0) {
            for (const vif of vlanifs) {
                const ipResult = validateIpAddress(vif.ip_address)
                if (!ipResult.valid) {
                    issues.push({
                        field: `vlan.vlanif.${vif.vlan_id}`,
                        message: `VLANIF ${vif.vlan_id}: ${ipResult.message}`,
                        severity: 'error',
                    })
                }
                const maskResult = validateSubnetMask(vif.mask)
                if (!maskResult.valid) {
                    issues.push({
                        field: `vlan.vlanif.${vif.vlan_id}`,
                        message: `VLANIF ${vif.vlan_id} 子网掩码: ${maskResult.message}`,
                        severity: 'error',
                    })
                }
            }
        }
    }

    // 5. 端口名校验
    const interfaces = configs.interface
    if (interfaces) {
        // Eth-Trunk 成员端口
        const trunks = interfaces.eth_trunks as Array<{
            trunk_id: number; member_ports: string[]
        }> | undefined
        if (trunks) {
            for (const trunk of trunks) {
                if (trunk.member_ports) {
                    for (const port of trunk.member_ports) {
                        const result = validatePortName(port)
                        if (!result.valid) {
                            issues.push({
                                field: `interface.eth_trunk.${trunk.trunk_id}`,
                                message: `Eth-Trunk ${trunk.trunk_id} 成员端口 "${port}": ${result.message}`,
                                severity: 'error',
                            })
                        }
                    }
                }
            }
        }
    }

    // 6. 安全 ACL 规则号校验
    const security = configs.security
    if (security?.acls) {
        for (const acl of security.acls) {
            if (acl.number !== undefined && (!Number.isInteger(acl.number) || acl.number < 2000 || acl.number > 3999)) {
                issues.push({
                    field: 'security.acl',
                    message: `ACL 编号 ${acl.number} 超出范围 (基本ACL: 2000-2999, 高级ACL: 3000-3999)`,
                    severity: 'error',
                })
            }
        }
    }

    // 7. 端口安全接口名
    if (security?.port_security) {
        for (const ps of security.port_security) {
            if (ps.interface) {
                const result = validatePortName(ps.interface)
                if (!result.valid) {
                    issues.push({
                        field: 'security.port_security',
                        message: `端口安全接口 "${ps.interface}": ${result.message}`,
                        severity: 'error',
                    })
                }
            }
        }
    }

    return issues
}

/**
 * 弹出校验结果提示
 * @returns 是否通过校验（无错误）
 */
export function showValidationResult(issues: ValidationIssue[]): boolean {
    const errors = issues.filter(i => i.severity === 'error')
    const warnings = issues.filter(i => i.severity === 'warning')

    if (warnings.length > 0) {
        console.warn('[校验警告]', warnings.map(w => w.message).join('; '))
    }

    if (errors.length > 0) {
        const firstError = errors[0]
        ElMessage.error(`参数校验失败: ${firstError.message}`)
        console.error('[校验错误]', errors.map(e => `${e.field}: ${e.message}`).join('\n  '))
        return false
    }

    return true
}

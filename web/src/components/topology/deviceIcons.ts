/**
 * 网络设备图标定义
 * 按四大类别分组：网络设备、终端设备、云/运营商、安全设备
 */
export interface DeviceIcon {
    type: string
    name: string
    color: string
    iconUrl: string
}

/** 设备分组 */
export interface DeviceGroup {
    id: string
    title: string
    devices: DeviceIcon[]
}

/** 所有设备图标定义 */
export const deviceIcons: Record<string, DeviceIcon> = {
    // ── 网络设备 ────────────────────────────────────────
    'core-switch': {
        type: 'core-switch',
        name: '核心交换机',
        color: '#409eff',
        iconUrl: '/icons/core-switch.svg',
    },
    'agg-switch': {
        type: 'agg-switch',
        name: '汇聚交换机',
        color: '#e6a23c',
        iconUrl: '/icons/agg-switch.svg',
    },
    'access-switch': {
        type: 'access-switch',
        name: '接入交换机',
        color: '#67c23a',
        iconUrl: '/icons/access-switch.svg',
    },
    'router': {
        type: 'router',
        name: '路由器',
        color: '#f56c6c',
        iconUrl: '/icons/router.svg',
    },
    'wireless-ac': {
        type: 'wireless-ac',
        name: 'AC 控制器',
        color: '#7c3aed',
        iconUrl: '/icons/wireless-ac.svg',
    },
    'wireless-ap': {
        type: 'wireless-ap',
        name: '无线 AP',
        color: '#4a90d9',
        iconUrl: '/icons/wireless-ap.svg',
    },
    'antenna': {
        type: 'antenna',
        name: '天线',
        color: '#f59e0b',
        iconUrl: '/icons/antenna.svg',
    },
    'optical-transceiver': {
        type: 'optical-transceiver',
        name: '光端机',
        color: '#6366f1',
        iconUrl: '/icons/optical-transceiver.svg',
    },

    // ── 终端设备 ────────────────────────────────────────
    'server': {
        type: 'server',
        name: '服务器',
        color: '#606266',
        iconUrl: '/icons/server.svg',
    },
    'nas': {
        type: 'nas',
        name: 'NAS 存储',
        color: '#475569',
        iconUrl: '/icons/nas.svg',
    },
    'storage': {
        type: 'storage',
        name: '存储设备',
        color: '#7c3aed',
        iconUrl: '/icons/storage.svg',
    },
    'pc': {
        type: 'pc',
        name: '终端 PC',
        color: '#5a6275',
        iconUrl: '/icons/pc.svg',
    },
    'laptop': {
        type: 'laptop',
        name: '笔记本',
        color: '#6366f1',
        iconUrl: '/icons/laptop.svg',
    },
    'ip-phone': {
        type: 'ip-phone',
        name: 'IP 电话',
        color: '#0284c7',
        iconUrl: '/icons/ip-phone.svg',
    },
    'printer': {
        type: 'printer',
        name: '打印机',
        color: '#6b7280',
        iconUrl: '/icons/printer.svg',
    },
    'camera-monitor': {
        type: 'camera-monitor',
        name: '监控摄像头',
        color: '#334155',
        iconUrl: '/icons/camera-monitor.svg',
    },

    // ── 云 / 运营商 ─────────────────────────────────────
    'cloud': {
        type: 'cloud',
        name: '云服务',
        color: '#4a90d9',
        iconUrl: '/icons/cloud.svg',
    },
    'internet': {
        type: 'internet',
        name: '互联网',
        color: '#3b82f6',
        iconUrl: '/icons/internet.svg',
    },

    // ── 安全设备 ────────────────────────────────────────
    'routeros': {
        type: 'routeros',
        name: 'RouterOS (MikroTik)',
        color: '#e2492f',
        iconUrl: '/icons/routeros.svg',
    },
    'firewall': {
        type: 'firewall',
        name: '防火墙',
        color: '#f97316',
        iconUrl: '/icons/firewall.svg',
    },
    'behavior-management': {
        type: 'behavior-management',
        name: '行为管理',
        color: '#f97316',
        iconUrl: '/icons/behavior-management.svg',
    },
    'ids-ips': {
        type: 'ids-ips',
        name: 'IDS/IPS',
        color: '#059669',
        iconUrl: '/icons/ids-ips.svg',
    },
    'data-diode': {
        type: 'data-diode',
        name: '网闸',
        color: '#dc2626',
        iconUrl: '/icons/data-diode.svg',
    },
}

/** 分组定义 */
export const deviceGroups: DeviceGroup[] = [
    {
        id: 'network',
        title: '网络设备',
        devices: ['core-switch', 'agg-switch', 'access-switch', 'router', 'routeros',
                   'wireless-ac', 'wireless-ap', 'antenna', 'optical-transceiver']
            .map(t => deviceIcons[t]),
    },
    {
        id: 'terminal',
        title: '终端设备',
        devices: ['server', 'nas', 'storage', 'pc', 'laptop',
                   'ip-phone', 'printer', 'camera-monitor']
            .map(t => deviceIcons[t]),
    },
    {
        id: 'cloud',
        title: '云 / 运营商',
        devices: ['cloud', 'internet'].map(t => deviceIcons[t]),
    },
    {
        id: 'security',
        title: '安全设备',
        devices: ['firewall', 'behavior-management', 'ids-ips', 'data-diode']
            .map(t => deviceIcons[t]),
    },
]

/** 根据类型获取图标 */
export function getDeviceIcon(type: string): DeviceIcon | undefined {
    return deviceIcons[type]
}

/** 获取全部设备（扁平列表，兼容旧代码） */
export function getAllDeviceTypes(): DeviceIcon[] {
    return Object.values(deviceIcons)
}

/** 获取分组设备列表 */
export function getGroupedDevices(): DeviceGroup[] {
    return deviceGroups
}

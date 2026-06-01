/**
 * 网络设备图标定义（使用 public/icons 静态资源）
 */

export interface DeviceIcon {
  type: string
  name: string
  color: string
  iconUrl: string
}

export const deviceIcons: Record<string, DeviceIcon> = {
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
  'cloud': {
    type: 'cloud',
    name: '云/外网',
    color: '#4a90d9',
    iconUrl: '/icons/cloud.svg',
  },
  'firewall': {
    type: 'firewall',
    name: '防火墙',
    color: '#909399',
    iconUrl: '/icons/firewall.svg',
  },
  'server': {
    type: 'server',
    name: '服务器',
    color: '#606266',
    iconUrl: '/icons/server.svg',
  },
  'pc': {
    type: 'pc',
    name: '终端PC',
    color: '#5a6275',
    iconUrl: '/icons/pc.svg',
  },
}

export function getDeviceIcon(type: string): DeviceIcon | undefined {
  return deviceIcons[type]
}

export function getAllDeviceTypes() {
  return Object.values(deviceIcons)
}

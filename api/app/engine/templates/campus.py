"""
企业园区网配置模板
支持核心-汇聚-接入三层架构的配置生成
"""

from typing import Dict, Any, List


class CampusTemplate:
    """园区网配置模板生成器"""

    @staticmethod
    def generate_campus_core(params: Dict[str, Any]) -> str:
        """
        生成核心交换机配置
        
        Args:
            params: 配置参数
                - hostname: 主机名
                - mgmt_ip: 管理IP
                - vendor: 厂商 (huawei/h3c)
                - vlans: VLAN列表 [{id: 10, name: 'Office'}]
                - interfaces: 接口配置列表
                - routing: 路由配置 (OSPF)
                - stp: STP配置
        
        Returns:
            配置字符串
        """
        vendor = params.get('vendor', 'huawei')
        lines = []

        # 头部注释
        lines.append("#")
        lines.append(f"# 核心交换机配置 - {params.get('hostname', 'SW-CORE')}")
        lines.append(f"# 管理IP: {params.get('mgmt_ip', '192.168.1.1')}")
        lines.append("#")
        lines.append("")

        # 基础配置
        if vendor == 'huawei':
            lines.append(f"sysname {params.get('hostname', 'SW-CORE-01')}")
            lines.append("#")
            lines.append("# SSH配置")
            lines.append("#")
            lines.append("ssh server enable")
            lines.append("ssh server port 22")
            lines.append("ssh server version 2")
        elif vendor == 'h3c':
            lines.append(f"sysname {params.get('hostname', 'SW-CORE-01')}")
            lines.append("#")
            lines.append("# SSH配置")
            lines.append("#")
            lines.append("ssh server enable")
            lines.append("ssh server port 22")

        lines.append("")

        # VLAN配置
        vlans = params.get('vlans', [])
        if vlans:
            vlan_ids = ' '.join([str(v['id']) for v in vlans])
            if vendor == 'huawei':
                lines.append("#")
                lines.append("# VLAN配置")
                lines.append("#")
                lines.append(f"vlan batch {vlan_ids}")
            elif vendor == 'h3c':
                lines.append("#")
                lines.append("# VLAN配置")
                lines.append("#")
                for vlan in vlans:
                    lines.append(f"vlan {vlan['id']}")
                    if vlan.get('name'):
                        lines.append(f" name {vlan['name']}")
            
            lines.append("")

        # 接口配置
        interfaces = params.get('interfaces', [])
        if interfaces:
            lines.append("#")
            lines.append("# 接口配置")
            lines.append("#")
            for iface in interfaces:
                lines.append(f"interface {iface['interface']}")
                if iface.get('description'):
                    lines.append(f" description \"{iface['description']}\"")
                
                if iface['linkType'] == 'trunk':
                    lines.append(" port link-type trunk")
                    if iface.get('allowedVlans'):
                        vlan_list = ' '.join([str(v) for v in iface['allowedVlans']])
                        if vendor == 'huawei':
                            lines.append(f" port trunk allow-pass vlan {vlan_list}")
                        elif vendor == 'h3c':
                            lines.append(f" port link-type trunk")
                            lines.append(f" port trunk permit vlan {vlan_list}")
                elif iface['linkType'] == 'access':
                    lines.append(" port link-type access")
                    if iface.get('vlanId'):
                        if vendor == 'huawei':
                            lines.append(f" port default vlan {iface['vlanId']}")
                        elif vendor == 'h3c':
                            lines.append(f" port access vlan {iface['vlanId']}")
                
                lines.append(" quit")
                lines.append("#")
            
            lines.append("")

        # OSPF配置
        routing = params.get('routing', {})
        if routing.get('type') == 'ospf' and routing.get('ospf'):
            ospf = routing['ospf']
            lines.append("#")
            lines.append("# OSPF配置")
            lines.append("#")
            
            if vendor == 'huawei':
                lines.append(f"ospf {ospf['processId']} router-id {ospf['routerId']}")
                for net in ospf.get('networks', []):
                    lines.append(f" area {net['area']}")
                    lines.append(f"  network {net['network']} {net['wildcard']}")
                lines.append(" quit")
            elif vendor == 'h3c':
                lines.append(f"ospf {ospf['processId']}")
                lines.append(f" router-id {ospf['routerId']}")
                for net in ospf.get('networks', []):
                    lines.append(f" area {net['area']}")
                    lines.append(f"  network {net['network']} {net['wildcard']}")
            
            lines.append("")

        # STP配置
        stp = params.get('stp', {})
        if stp:
            lines.append("#")
            lines.append("# STP配置")
            lines.append("#")
            lines.append("stp enable")
            
            if vendor == 'huawei':
                lines.append(f"stp mode {stp.get('mode', 'mstp')}")
                lines.append(f"stp priority {stp.get('priority', 4096)}")
            elif vendor == 'h3c':
                lines.append(f"stp mode {stp.get('mode', 'mstp')}")
                lines.append(f"stp priority {stp.get('priority', 4096)}")
            
            lines.append("")

        # 管理IP配置
        if params.get('mgmt_ip'):
            lines.append("#")
            lines.append("# 管理接口配置")
            lines.append("#")
            if vendor == 'huawei':
                lines.append("interface Vlanif1")
                lines.append(f" ip address {params['mgmt_ip']} 24")
                lines.append(" quit")
            elif vendor == 'h3c':
                lines.append("interface Vlan-interface1")
                lines.append(f" ip address {params['mgmt_ip']} 255.255.255.0")
                lines.append(" quit")
            
            lines.append("")

        return '\n'.join(lines)

    @staticmethod
    def generate_campus_access(params: Dict[str, Any]) -> str:
        """
        生成接入交换机配置
        
        Args:
            params: 配置参数
        
        Returns:
            配置字符串
        """
        vendor = params.get('vendor', 'huawei')
        lines = []

        # 头部注释
        lines.append("#")
        lines.append(f"# 接入交换机配置 - {params.get('hostname', 'SW-ACCESS')}")
        lines.append(f"# 管理IP: {params.get('mgmt_ip', '192.168.1.2')}")
        lines.append("#")
        lines.append("")

        # 基础配置
        if vendor == 'huawei':
            lines.append(f"sysname {params.get('hostname', 'SW-ACCESS-01')}")
            lines.append("#")
            lines.append("# SSH配置")
            lines.append("#")
            lines.append("ssh server enable")
            lines.append("ssh server port 22")
        elif vendor == 'h3c':
            lines.append(f"sysname {params.get('hostname', 'SW-ACCESS-01')}")
            lines.append("#")
            lines.append("# SSH配置")
            lines.append("#")
            lines.append("ssh server enable")
            lines.append("ssh server port 22")
        
        lines.append("")

        # VLAN配置
        vlans = params.get('vlans', [])
        if vlans:
            vlan_ids = ' '.join([str(v['id']) for v in vlans])
            if vendor == 'huawei':
                lines.append("#")
                lines.append("# VLAN配置")
                lines.append("#")
                lines.append(f"vlan batch {vlan_ids}")
            elif vendor == 'h3c':
                lines.append("#")
                lines.append("# VLAN配置")
                lines.append("#")
                for vlan in vlans:
                    lines.append(f"vlan {vlan['id']}")
                    if vlan.get('name'):
                        lines.append(f" name {vlan['name']}")
            
            lines.append("")

        # 接口配置
        interfaces = params.get('interfaces', [])
        if interfaces:
            lines.append("#")
            lines.append("# 接口配置")
            lines.append("#")
            for iface in interfaces:
                lines.append(f"interface {iface['interface']}")
                if iface.get('description'):
                    lines.append(f" description \"{iface['description']}\"")
                
                if iface['linkType'] == 'trunk':
                    lines.append(" port link-type trunk")
                    if iface.get('allowedVlans'):
                        vlan_list = ' '.join([str(v) for v in iface['allowedVlans']])
                        if vendor == 'huawei':
                            lines.append(f" port trunk allow-pass vlan {vlan_list}")
                        elif vendor == 'h3c':
                            lines.append(f" port trunk permit vlan {vlan_list}")
                elif iface['linkType'] == 'access':
                    lines.append(" port link-type access")
                    if iface.get('vlanId'):
                        if vendor == 'huawei':
                            lines.append(f" port default vlan {iface['vlanId']}")
                        elif vendor == 'h3c':
                            lines.append(f" port access vlan {iface['vlanId']}")
                
                lines.append(" quit")
                lines.append("#")
            
            lines.append("")

        # 静态路由（默认路由指向核心）
        routing = params.get('routing', {})
        if routing.get('type') == 'static' and routing.get('routes'):
            lines.append("#")
            lines.append("# 静态路由配置")
            lines.append("#")
            for route in routing['routes']:
                if vendor == 'huawei':
                    lines.append(f"ip route-static {route['dest']} {route['mask']} {route['nexthop']}")
                elif vendor == 'h3c':
                    lines.append(f"ip route-static {route['dest']} {route['mask']} {route['nexthop']}")
            
            lines.append("")

        # STP配置
        stp = params.get('stp', {})
        if stp:
            lines.append("#")
            lines.append("# STP配置")
            lines.append("#")
            lines.append("stp enable")
            if vendor == 'huawei':
                lines.append(f"stp mode {stp.get('mode', 'mstp')}")
                lines.append(f"stp priority {stp.get('priority', 32768)}")
            elif vendor == 'h3c':
                lines.append(f"stp mode {stp.get('mode', 'mstp')}")
                lines.append(f"stp priority {stp.get('priority', 32768)}")
            
            lines.append("")

        # 管理IP配置
        if params.get('mgmt_ip'):
            lines.append("#")
            lines.append("# 管理接口配置")
            lines.append("#")
            if vendor == 'huawei':
                lines.append("interface Vlanif1")
                lines.append(f" ip address {params['mgmt_ip']} 24")
                lines.append(" quit")
            elif vendor == 'h3c':
                lines.append("interface Vlan-interface1")
                lines.append(f" ip address {params['mgmt_ip']} 255.255.255.0")
                lines.append(" quit")
            
            lines.append("")

        return '\n'.join(lines)

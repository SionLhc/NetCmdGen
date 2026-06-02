#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MikroTik RouterOS 命令手册

包含 V6/V7 两代命令，V7 新增的路由引擎命令单独标注。
"""

ROUTEROS_COMMANDS = {
    "基础配置": {
        "系统管理": {
            "设置设备名称": {
                "command": "/system identity set name=<name>",
                "description": "设置设备主机名",
                "example": "/system identity set name=ROS-Core",
                "versions": ["all"]
            },
            "查看系统资源": {
                "command": "/system resource print",
                "description": "查看CPU、内存、存储使用情况",
                "example": "/system resource print",
                "versions": ["all"]
            },
            "查看系统版本": {
                "command": "/system resource print\n/system routerboard print",
                "description": "查看RouterOS版本和硬件信息",
                "example": "/system resource print\n/system routerboard print",
                "versions": ["all"]
            },
            "系统重启": {
                "command": "/system reboot",
                "description": "重启RouterOS设备",
                "example": "/system reboot",
                "versions": ["all"]
            },
            "系统关机": {
                "command": "/system shutdown",
                "description": "安全关闭RouterOS设备",
                "example": "/system shutdown",
                "versions": ["all"]
            },
            "备份配置": {
                "command": "/export file=<filename>",
                "description": "导出当前配置到文件",
                "example": "/export file=backup-2026",
                "versions": ["all"]
            },
            "导入配置": {
                "command": "/import file=<filename>",
                "description": "从文件导入配置",
                "example": "/import file=backup-2026.rsc",
                "versions": ["all"]
            },
            "查看运行日志": {
                "command": "/log print",
                "description": "查看系统日志",
                "example": "/log print where topics~error",
                "versions": ["all"]
            },
            "系统时间/NTP": {
                "command": "/system ntp client set enabled=yes primary-ntp=<ip>",
                "description": "设置NTP时间同步",
                "example": "/system ntp client set enabled=yes primary-ntp=119.28.183.184",
                "versions": ["all"]
            },
            "配置DNS": {
                "command": "/ip dns set servers=<ip1>,<ip2> allow-remote-requests=yes",
                "description": "配置DNS服务器",
                "example": "/ip dns set servers=8.8.8.8,114.114.114.114",
                "versions": ["all"]
            },
            "开启DNS缓存": {
                "command": "/ip dns set allow-remote-requests=yes cache-size=2048",
                "description": "启用DNS缓存服务器",
                "example": "/ip dns set allow-remote-requests=yes cache-size=2048KiB",
                "versions": ["all"]
            }
        },
        "用户管理": {
            "创建用户": {
                "command": "/user add name=<user> password=<pw> group=<group>",
                "description": "创建本地用户(权限组: full/read/write)",
                "example": "/user add name=admin password=Admin@123 group=full",
                "versions": ["all"]
            },
            "修改密码": {
                "command": "/user set <user> password=<new-pw>",
                "description": "修改用户密码",
                "example": "/user set admin password=NewPass@456",
                "versions": ["all"]
            },
            "删除用户": {
                "command": "/user remove <user>",
                "description": "删除用户",
                "example": "/user remove testuser",
                "versions": ["all"]
            },
            "查看在线用户": {
                "command": "/user active print",
                "description": "查看当前在线用户",
                "example": "/user active print",
                "versions": ["all"]
            },
            "用户组管理": {
                "command": "/user group add name=<group> policy=<policies>",
                "description": "创建用户组并分配权限策略",
                "example": "/user group add name=netops policy=ssh,telnet,read,write,api",
                "versions": ["all"]
            }
        },
        "SSH/远程管理": {
            "启用SSH": {
                "command": "/ip service set ssh port=<port> disabled=no",
                "description": "启用SSH服务",
                "example": "/ip service set ssh port=22 disabled=no",
                "versions": ["all"]
            },
            "禁用Telnet": {
                "command": "/ip service set telnet disabled=yes",
                "description": "关闭不安全的Telnet",
                "example": "/ip service set telnet disabled=yes",
                "versions": ["all"]
            },
            "禁用Web管理": {
                "command": "/ip service set www disabled=yes www-ssl disabled=no",
                "description": "关闭HTTP，保留HTTPS Web管理",
                "example": "/ip service set www disabled=yes www-ssl disabled=no",
                "versions": ["all"]
            },
            "SSH端口转发": {
                "command": "/ip service set ssh port=<port> address=<ip-range>",
                "description": "限制SSH访问来源IP",
                "example": "/ip service set ssh address=192.168.1.0/24",
                "versions": ["all"]
            },
            "生成SSH密钥": {
                "command": "/ip ssh regenerate-host-key",
                "description": "重新生成SSH主机密钥",
                "example": "/ip ssh regenerate-host-key",
                "versions": ["all"]
            },
            "配置WinBox": {
                "command": "/ip service set winbox port=<port> address=<ip-range>",
                "description": "配置WinBox管理工具访问",
                "example": "/ip service set winbox address=192.168.1.0/24",
                "versions": ["all"]
            }
        }
    },
    "接口与IP": {
        "以太网接口": {
            "查看接口列表": {
                "command": "/interface print",
                "description": "查看所有接口",
                "example": "/interface print",
                "versions": ["all"]
            },
            "接口改名": {
                "command": "/interface set <old-name> name=<new-name>",
                "description": "重命名接口",
                "example": "/interface set ether1 name=WAN1",
                "versions": ["all"]
            },
            "启用/禁用接口": {
                "command": "/interface enable <name>\n/interface disable <name>",
                "description": "启用或禁用接口",
                "example": "/interface enable ether2",
                "versions": ["all"]
            },
            "接口速率": {
                "command": "/interface ethernet set <name> speed=<10M|100M|1G|10G>",
                "description": "设置接口速率和双工",
                "example": "/interface ethernet set ether2 speed=1Gbps auto-negotiation=no",
                "versions": ["all"]
            },
            "接口MAC地址": {
                "command": "/interface ethernet set <name> mac-address=<mac>",
                "description": "修改接口MAC地址",
                "example": "/interface ethernet set ether2 mac-address=00:11:22:33:44:55",
                "versions": ["all"]
            },
            "查看接口流量": {
                "command": "/interface monitor-traffic <name>",
                "description": "实时监控接口流量",
                "example": "/interface monitor-traffic ether1",
                "versions": ["all"]
            }
        },
        "IP地址": {
            "添加IP地址": {
                "command": "/ip address add address=<ip>/<mask> interface=<interface>",
                "description": "为接口添加IP地址",
                "example": "/ip address add address=192.168.1.1/24 interface=ether2",
                "versions": ["all"]
            },
            "查看IP地址": {
                "command": "/ip address print",
                "description": "查看所有IP地址配置",
                "example": "/ip address print",
                "versions": ["all"]
            },
            "删除IP地址": {
                "command": "/ip address remove [find interface=<name>]",
                "description": "删除接口的IP地址",
                "example": "/ip address remove [find interface=ether2]",
                "versions": ["all"]
            },
            "添加从IP": {
                "command": "/ip address add address=<ip>/<mask> interface=<interface>",
                "description": "接口可添加多个IP",
                "example": "/ip address add address=10.10.10.1/24 interface=ether2",
                "versions": ["all"]
            }
        },
        "ARP表": {
            "查看ARP表": {
                "command": "/ip arp print",
                "description": "查看ARP缓存表",
                "example": "/ip arp print",
                "versions": ["all"]
            },
            "添加静态ARP": {
                "command": "/ip arp add address=<ip> mac-address=<mac> interface=<interface>",
                "description": "添加静态ARP条目",
                "example": "/ip arp add address=192.168.1.100 mac-address=AA:BB:CC:DD:EE:FF interface=bridge1",
                "versions": ["all"]
            }
        },
        "MikroTik邻居发现": {
            "启用邻居发现": {
                "command": "/ip neighbor discovery-settings set discover-interface-list=all",
                "description": "启用MNDP/CDP/LLDP邻居发现",
                "example": "/ip neighbor discovery-settings set discover-interface-list=all",
                "versions": ["all"]
            },
            "查看邻居": {
                "command": "/ip neighbor print",
                "description": "查看发现的邻居设备",
                "example": "/ip neighbor print detail",
                "versions": ["all"]
            }
        }
    },
    "桥接与VLAN": {
        "Bridge配置": {
            "创建桥接": {
                "command": "/interface bridge add name=<bridge-name>",
                "description": "创建桥接接口",
                "example": "/interface bridge add name=bridge1",
                "versions": ["all"]
            },
            "添加桥接端口": {
                "command": "/interface bridge port add interface=<port> bridge=<bridge>",
                "description": "将物理接口加入桥接",
                "example": "/interface bridge port add interface=ether2 bridge=bridge1",
                "versions": ["all"]
            },
            "查看桥接状态": {
                "command": "/interface bridge print\n/interface bridge port print",
                "description": "查看桥接和端口状态",
                "example": "/interface bridge port print",
                "versions": ["all"]
            },
            "STP/RSTP": {
                "command": "/interface bridge set <bridge> protocol-mode=<rstp|mstp|none>",
                "description": "设置生成树协议",
                "example": "/interface bridge set bridge1 protocol-mode=rstp",
                "versions": ["all"]
            },
            "设置Bridge优先级": {
                "command": "/interface bridge set <bridge> priority=<0-65535>",
                "description": "设置STP桥优先级",
                "example": "/interface bridge set bridge1 priority=4096",
                "versions": ["all"]
            },
            "VLAN过滤(V7)": {
                "command": "/interface bridge vlan add bridge=<bridge> vlan-ids=<vid> tagged=<ports>",
                "description": "V7 Bridge VLAN filtering（V7 推荐方式）",
                "example": "/interface bridge vlan add bridge=bridge1 vlan-ids=10 tagged=bridge1,ether1",
                "versions": ["v7"]
            },
            "启用VLAN过滤(V7)": {
                "command": "/interface bridge set <bridge> vlan-filtering=yes",
                "description": "V7 启用Bridge VLAN过滤",
                "example": "/interface bridge set bridge1 vlan-filtering=yes",
                "versions": ["v7"]
            }
        },
        "VLAN接口": {
            "创建VLAN": {
                "command": "/interface vlan add name=<name> vlan-id=<vid> interface=<trunk>",
                "description": "创建VLAN接口",
                "example": "/interface vlan add name=VLAN10 vlan-id=10 interface=ether1",
                "versions": ["all"]
            },
            "查看VLAN": {
                "command": "/interface vlan print",
                "description": "查看所有VLAN接口",
                "example": "/interface vlan print",
                "versions": ["all"]
            }
        }
    },
    "路由配置": {
        "静态路由": {
            "添加静态路由": {
                "command": "/ip route add dst-address=<dest>&#47;<prefix> gateway=<gw>",
                "description": "添加静态路由（使用&#47;分隔前缀长度）",
                "example": "/ip route add dst-address=0.0.0.0/0 gateway=192.168.1.254",
                "versions": ["all"]
            },
            "添加路由距离": {
                "command": "/ip route add dst-address=<net>/<prefix> gateway=<gw> distance=<1-255>",
                "description": "指定路由管理距离",
                "example": "/ip route add dst-address=10.0.0.0/8 gateway=192.168.2.1 distance=10",
                "versions": ["all"]
            },
            "查看路由表": {
                "command": "/ip route print",
                "description": "查看路由表",
                "example": "/ip route print detail",
                "versions": ["all"]
            },
            "删除路由": {
                "command": "/ip route remove [find dst-address=<net>/<prefix>]",
                "description": "删除指定路由",
                "example": "/ip route remove [find dst-address=0.0.0.0/0]",
                "versions": ["all"]
            },
            "查看路由表(V7)": {
                "command": "/routing route print",
                "description": "V7 统一路由查看（替代 /ip route）",
                "example": "/routing route print",
                "versions": ["v7"]
            }
        },
        "OSPF (V6)": {
            "配置OSPF实例(V6)": {
                "command": "/routing ospf instance set default router-id=<rid>",
                "description": "V6 设置OSPF路由器ID",
                "example": "/routing ospf instance set default router-id=1.1.1.1",
                "versions": ["v6"]
            },
            "添加OSPF网络(V6)": {
                "command": "/routing ospf network add network=<net> area=<area>",
                "description": "V6 添加OSPF网络到区域",
                "example": "/routing ospf network add network=192.168.1.0/24 area=backbone",
                "versions": ["v6"]
            },
            "查看OSPF邻居(V6)": {
                "command": "/routing ospf neighbor print",
                "description": "V6 查看OSPF邻居状态",
                "example": "/routing ospf neighbor print",
                "versions": ["v6"]
            }
        },
        "OSPF (V7)": {
            "创建OSPF实例(V7)": {
                "command": "/routing ospf instance add name=default router-id=<rid>",
                "description": "V7 创建OSPF实例（V7语法变更）",
                "example": "/routing ospf instance add name=default router-id=1.1.1.1",
                "versions": ["v7"]
            },
            "添加OSPF区域(V7)": {
                "command": "/routing ospf area add name=<area-name> area-id=<id> instance=default",
                "description": "V7 添加OSPF区域",
                "example": "/routing ospf area add name=backbone area-id=0.0.0.0 instance=default",
                "versions": ["v7"]
            },
            "添加OSPF网络(V7)": {
                "command": "/routing ospf interface-template add network=<net> area=<area>",
                "description": "V7 添加OSPF接口模板",
                "example": "/routing ospf interface-template add network=192.168.1.0/24 area=backbone",
                "versions": ["v7"]
            },
            "查看OSPF邻居(V7)": {
                "command": "/routing ospf neighbor print",
                "description": "V7 查看OSPF邻居",
                "example": "/routing ospf neighbor print",
                "versions": ["v7"]
            }
        }
    },
    "防火墙与NAT": {
        "防火墙规则": {
            "查看防火墙规则": {
                "command": "/ip firewall filter print",
                "description": "查看所有防火墙过滤规则",
                "example": "/ip firewall filter print",
                "versions": ["all"]
            },
            "添加规则(Input链)": {
                "command": "/ip firewall filter add chain=input action=<action> protocol=<proto> dst-port=<port>",
                "description": "添加input防火墙规则",
                "example": "/ip firewall filter add chain=input action=accept protocol=tcp dst-port=22",
                "versions": ["all"]
            },
            "添加规则(Forward链)": {
                "command": "/ip firewall filter add chain=forward action=<action> protocol=<proto>",
                "description": "添加forward防火墙规则",
                "example": "/ip firewall filter add chain=forward action=drop protocol=udp dst-port=445",
                "versions": ["all"]
            },
            "DDoS防护": {
                "command": "/ip firewall filter add chain=input action=drop connection-limit=<n>,32 protocol=tcp dst-port=80",
                "description": "限制连接数防DDoS",
                "example": "/ip firewall filter add chain=input protocol=tcp dst-port=80 connection-limit=50,32 action=drop",
                "versions": ["all"]
            },
            "地址列表": {
                "command": "/ip firewall address-list add address=<ip> list=<list-name>",
                "description": "创建地址列表(白名单/黑名单)",
                "example": "/ip firewall address-list add address=192.168.1.0/24 list=LAN",
                "versions": ["all"]
            }
        },
        "NAT": {
            "源NAT (Masquerade)": {
                "command": "/ip firewall nat add chain=srcnat out-interface=<wan> action=masquerade",
                "description": "SNAT伪装上网（最常用）",
                "example": "/ip firewall nat add chain=srcnat out-interface=ether1 action=masquerade",
                "versions": ["all"]
            },
            "目的NAT (端口映射)": {
                "command": "/ip firewall nat add chain=dstnat dst-port=<port> protocol=tcp action=dst-nat to-addresses=<ip> to-ports=<port>",
                "description": "DNAT端口映射到内网",
                "example": "/ip firewall nat add chain=dstnat dst-port=80 protocol=tcp action=dst-nat to-addresses=192.168.1.100 to-ports=80",
                "versions": ["all"]
            },
            "查看NAT规则": {
                "command": "/ip firewall nat print",
                "description": "查看所有NAT规则",
                "example": "/ip firewall nat print",
                "versions": ["all"]
            },
            "NAT回流(Hairpin)": {
                "command": "/ip firewall nat add chain=srcnat src-address=<lan-net> dst-address=<lan-net> protocol=tcp dst-port=<port> action=masquerade",
                "description": "内网用户通过公网IP访问内部服务器（NAT回流）",
                "example": "/ip firewall nat add chain=srcnat src-address=192.168.1.0/24 dst-address=192.168.1.100 protocol=tcp dst-port=80 action=masquerade",
                "versions": ["all"]
            }
        },
        "Mangle": {
            "标记连接": {
                "command": "/ip firewall mangle add chain=prerouting src-address=<ip> action=mark-connection new-connection-mark=<mark>",
                "description": "标记连接用于策略路由",
                "example": "/ip firewall mangle add chain=prerouting src-address=192.168.1.0/24 action=mark-connection new-connection-mark=LAN1-conn",
                "versions": ["all"]
            },
            "标记路由": {
                "command": "/ip firewall mangle add chain=prerouting connection-mark=<conn-mark> action=mark-routing new-routing-mark=<mark>",
                "description": "标记路由实现多线分流",
                "example": "/ip firewall mangle add chain=prerouting connection-mark=LAN1-conn action=mark-routing new-routing-mark=ISP1",
                "versions": ["all"]
            }
        }
    },
    "DHCP服务": {
        "DHCP服务器": {
            "创建地址池": {
                "command": "/ip pool add name=<pool> ranges=<start>-<end>",
                "description": "创建DHCP地址池",
                "example": "/ip pool add name=LAN-Pool ranges=192.168.1.100-192.168.1.200",
                "versions": ["all"]
            },
            "配置DHCP网络": {
                "command": "/ip dhcp-server network add address=<net>/<prefix> gateway=<gw> dns-server=<dns>",
                "description": "配置DHCP网络参数",
                "example": "/ip dhcp-server network add address=192.168.1.0/24 gateway=192.168.1.1 dns-server=8.8.8.8",
                "versions": ["all"]
            },
            "启用DHCP服务器": {
                "command": "/ip dhcp-server add name=<name> interface=<interface> address-pool=<pool> disabled=no",
                "description": "创建并启用DHCP服务器",
                "example": "/ip dhcp-server add name=LAN interface=bridge1 address-pool=LAN-Pool disabled=no",
                "versions": ["all"]
            },
            "查看DHCP租约": {
                "command": "/ip dhcp-server lease print",
                "description": "查看DHCP租约列表",
                "example": "/ip dhcp-server lease print",
                "versions": ["all"]
            },
            "静态绑定": {
                "command": "/ip dhcp-server lease add address=<ip> mac-address=<mac>",
                "description": "MAC-IP静态绑定",
                "example": "/ip dhcp-server lease add address=192.168.1.50 mac-address=AA:BB:CC:DD:EE:FF",
                "versions": ["all"]
            }
        }
    },
    "管理与监控": {
        "SNMP": {
            "启用SNMP": {
                "command": "/snmp set enabled=yes\n/snmp community add name=<community>",
                "description": "启用SNMP并设置共同体",
                "example": "/snmp set enabled=yes\n/snmp community add name=public",
                "versions": ["all"]
            },
            "设置SNMP位置": {
                "command": "/snmp set contact=<contact> location=<location>",
                "description": "设置SNMP联系人和位置",
                "example": "/snmp set contact=admin@company.com location=Server-Room",
                "versions": ["all"]
            }
        },
        "NetFlow/Traffic-Flow": {
            "启用NetFlow": {
                "command": "/ip traffic-flow set enabled=yes interfaces=<interface>\n/ip traffic-flow target add dst-address=<collector> port=2055 version=9",
                "description": "启用NetFlow流量分析",
                "example": "/ip traffic-flow set enabled=yes\n/ip traffic-flow target add dst-address=192.168.1.200 port=2055 version=9",
                "versions": ["all"]
            }
        },
        "脚本调度": {
            "添加脚本": {
                "command": "/system script add name=<name> source=<script-code>",
                "description": "创建系统脚本",
                "example": "/system script add name=backup source={/export file=auto-backup}",
                "versions": ["all"]
            },
            "定时任务": {
                "command": "/system scheduler add name=<name> interval=<time> on-event=<script-name>",
                "description": "创建定时任务",
                "example": "/system scheduler add name=daily-backup interval=24h on-event=backup",
                "versions": ["all"]
            }
        },
        "带宽测试": {
            "带宽测试服务端": {
                "command": "/tool bandwidth-server set enabled=yes",
                "description": "启用带宽测试服务器",
                "example": "/tool bandwidth-server set enabled=yes authenticate=no",
                "versions": ["all"]
            },
            "Ping工具": {
                "command": "/ping <address> count=<n>",
                "description": "Ping测试",
                "example": "/ping 8.8.8.8 count=5",
                "versions": ["all"]
            },
            "Traceroute": {
                "command": "/tool trace <address>",
                "description": "路由追踪",
                "example": "/tool trace 8.8.8.8",
                "versions": ["all"]
            }
        }
    },
    "V7新特性": {
        "WireGuard VPN": {
            "创建WireGuard接口": {
                "command": "/interface wireguard add name=<name> listen-port=<port> private-key=<key>",
                "description": "V7 创建WireGuard接口",
                "example": "/interface wireguard add name=wg1 listen-port=13231",
                "versions": ["v7"]
            },
            "添加WireGuard Peer": {
                "command": "/interface wireguard peers add interface=<wg> public-key=<key> endpoint-address=<ip> endpoint-port=<port> allowed-address=<net>/<prefix>",
                "description": "V7 添加WireGuard对端",
                "example": "/interface wireguard peers add interface=wg1 public-key=xxx endpoint-address=203.0.113.1 endpoint-port=13231 allowed-address=10.0.0.0/8",
                "versions": ["v7"]
            }
        },
        "Container容器": {
            "启用容器": {
                "command": "/container config set registry-url=https://registry-1.docker.io tmpdir=disk1/pull",
                "description": "V7 配置容器运行时",
                "example": "/container config set registry-url=https://registry-1.docker.io",
                "versions": ["v7"]
            },
            "运行容器": {
                "command": "/container add remote-image=<image> interface=<veth> root-dir=<dir>",
                "description": "V7 运行Docker容器",
                "example": "/container add remote-image=nginx:alpine interface=veth1 root-dir=disk1/nginx start-on-boot=yes",
                "versions": ["v7"]
            }
        },
        "BGP (V7)": {
            "配置BGP实例(V7)": {
                "command": "/routing bgp connection add name=<name> as=<asn> router-id=<rid> local.address=<ip> remote.address=<ip>",
                "description": "V7 BGP连接配置",
                "example": "/routing bgp connection add name=ISP1 as=65001 router-id=1.1.1.1 local.address=10.0.0.1 remote.address=10.0.0.2",
                "versions": ["v7"]
            }
        }
    }
}

"""思科 Cisco IOS 命令速查库。"""
from typing import List, Dict, Optional

CISCO_MANUAL: List[Dict[str, str]] = [
    # ── 基础系统 ──
    {"category": "基础系统", "name": "进入特权模式", "command": "enable", "description": "进入特权 EXEC 模式", "example": "Router> enable"},
    {"category": "基础系统", "name": "进入全局配置", "command": "configure terminal", "description": "进入全局配置模式", "example": "Router# configure terminal"},
    {"category": "基础系统", "name": "设置主机名", "command": "hostname <name>", "description": "设置设备主机名", "example": "Router(config)# hostname SW-01"},
    {"category": "基础系统", "name": "设置 Enable 密码", "command": "enable secret <password>", "description": "设置加密的特权模式密码（推荐用 secret 而非 password）", "example": "Router(config)# enable secret cisco123"},
    {"category": "基础系统", "name": "设置 Banner 登录提示", "command": "banner motd #<text>#", "description": "设置登录前显示的 MOTD 横幅", "example": "Router(config)# banner motd #Unauthorized access prohibited!#"},
    {"category": "基础系统", "name": "保存配置", "command": "write memory / copy running-config startup-config", "description": "将当前运行配置保存到启动配置", "example": "Router# write memory"},
    {"category": "基础系统", "name": "查看运行配置", "command": "show running-config", "description": "查看当前运行的完整配置", "example": "Router# show running-config"},
    {"category": "基础系统", "name": "查看启动配置", "command": "show startup-config", "description": "查看下次启动时加载的配置", "example": "Router# show startup-config"},
    {"category": "基础系统", "name": "查看版本信息", "command": "show version", "description": "查看 IOS 版本/硬件信息/运行时间", "example": "Router# show version"},
    {"category": "基础系统", "name": "重启设备", "command": "reload", "description": "重启设备（会提示确认）", "example": "Router# reload"},
    {"category": "基础系统", "name": "创建本地用户", "command": "username <name> privilege <level> secret <password>", "description": "创建本地用户（AAA 认证使用）", "example": "Router(config)# username admin privilege 15 secret admin123"},

    # ── SSH / 远程管理 ──
    {"category": "远程管理", "name": "配置 SSH", "command": "ip domain-name <domain>\ncrypto key generate rsa\nip ssh version 2\nline vty 0 4\n login local\n transport input ssh", "description": "完整 SSH 配置流程（域名+密钥+VTY线路）", "example": "Router(config)# ip domain-name local\nRouter(config)# crypto key generate rsa modulus 2048"},
    {"category": "远程管理", "name": "Telnet 配置", "command": "line vty 0 4\n login local\n transport input telnet", "description": "开启 Telnet（不推荐，建议用SSH）", "example": "Router(config)# line vty 0 4"},
    {"category": "远程管理", "name": "NTP 时间同步", "command": "ntp server <ip>", "description": "配置 NTP 服务器", "example": "Router(config)# ntp server 202.120.2.101"},
    {"category": "远程管理", "name": "SNMP 配置", "command": "snmp-server community <string> RO/RW", "description": "配置 SNMP 读写团体字", "example": "Router(config)# snmp-server community public RO"},

    # ── VLAN ──
    {"category": "VLAN", "name": "创建 VLAN", "command": "vlan <vlan-id>\n name <vlan-name>", "description": "创建 VLAN 并命名", "example": "Switch(config)# vlan 10\nSwitch(config-vlan)# name SALES"},
    {"category": "VLAN", "name": "Access 端口", "command": "interface <port>\n switchport mode access\n switchport access vlan <vlan-id>", "description": "将端口设置为 Access 模式并划入 VLAN", "example": "Switch(config-if)# switchport mode access\nSwitch(config-if)# switchport access vlan 10"},
    {"category": "VLAN", "name": "Trunk 端口", "command": "interface <port>\n switchport mode trunk\n switchport trunk allowed vlan <vlans>", "description": "设置 Trunk 端口并指定允许 VLAN", "example": "Switch(config-if)# switchport trunk allowed vlan 10,20,30"},
    {"category": "VLAN", "name": "Native VLAN", "command": "switchport trunk native vlan <vlan-id>", "description": "设置 Trunk 的 Native VLAN", "example": "Switch(config-if)# switchport trunk native vlan 99"},
    {"category": "VLAN", "name": "SVI 接口", "command": "interface vlan <vlan-id>\n ip address <ip> <mask>\n no shutdown", "description": "创建 VLAN 虚接口（SVI）用于三层路由", "example": "Switch(config)# interface vlan 10\nSwitch(config-if)# ip address 192.168.10.1 255.255.255.0"},
    {"category": "VLAN", "name": "查看 VLAN 信息", "command": "show vlan brief", "description": "查看所有 VLAN 和端口分配", "example": "Switch# show vlan brief"},

    # ── 路由 ──
    {"category": "路由", "name": "静态路由", "command": "ip route <dest-network> <mask> <next-hop>", "description": "添加静态路由", "example": "Router(config)# ip route 192.168.2.0 255.255.255.0 10.0.0.1"},
    {"category": "路由", "name": "默认路由", "command": "ip route 0.0.0.0 0.0.0.0 <next-hop>", "description": "添加默认路由（出公网）", "example": "Router(config)# ip route 0.0.0.0 0.0.0.0 1.2.3.1"},
    {"category": "路由", "name": "OSPF 配置", "command": "router ospf <process-id>\n network <net> <wildcard> area <area>", "description": "启用 OSPF 并宣告网络", "example": "Router(config)# router ospf 1\nRouter(config-router)# network 10.0.0.0 0.0.0.255 area 0"},
    {"category": "路由", "name": "EIGRP 配置", "command": "router eigrp <as-number>\n network <net> <wildcard>\n no auto-summary", "description": "思科私有协议 EIGRP 配置", "example": "Router(config)# router eigrp 100\nRouter(config-router)# network 10.0.0.0 0.0.0.255"},
    {"category": "路由", "name": "BGP 配置", "command": "router bgp <as-number>\n neighbor <ip> remote-as <as>", "description": "BGP 邻居配置", "example": "Router(config)# router bgp 65001\nRouter(config-router)# neighbor 1.1.1.1 remote-as 65002"},
    {"category": "路由", "name": "查看路由表", "command": "show ip route", "description": "查看 IP 路由表", "example": "Router# show ip route"},
    {"category": "路由", "name": "查看 OSPF 邻居", "command": "show ip ospf neighbor", "description": "查看 OSPF 邻居状态", "example": "Router# show ip ospf neighbor"},

    # ── 安全 ──
    {"category": "安全", "name": "ACL 访问列表", "command": "access-list <number> <permit|deny> <protocol> <src> <wildcard> <dst> <wildcard>", "description": "标准/扩展 ACL（Cisco 使用反掩码）", "example": "Router(config)# access-list 100 permit ip 192.168.1.0 0.0.0.255 any"},
    {"category": "安全", "name": "端口安全", "command": "switchport port-security\n switchport port-security maximum <n>\n switchport port-security violation <action>", "description": "端口安全：限制MAC数量+违规动作", "example": "Switch(config-if)# switchport port-security\nSwitch(config-if)# switchport port-security maximum 1"},
    {"category": "安全", "name": "STP 生成树", "command": "spanning-tree mode <mode>\n spanning-tree vlan <id> priority <value>", "description": "STP 模式（pvst/rapid-pvst/mst）和优先级", "example": "Switch(config)# spanning-tree mode rapid-pvst"},
    {"category": "安全", "name": "BPDU Guard", "command": "spanning-tree portfast bpduguard default", "description": "全局启用 BPDU Guard（配合 PortFast）", "example": "Switch(config)# spanning-tree portfast bpduguard default"},
    {"category": "安全", "name": "DHCP Snooping", "command": "ip dhcp snooping\n ip dhcp snooping vlan <vlans>", "description": "DHCP 监听防伪造 DHCP 服务器", "example": "Switch(config)# ip dhcp snooping vlan 10,20"},

    # ── 接口 / EtherChannel ──
    {"category": "接口", "name": "EtherChannel LACP", "command": "interface range <ports>\n channel-group <id> mode active", "description": "LACP 动态链路聚合", "example": "Switch(config)# interface range g0/1-2\nSwitch(config-if-range)# channel-group 1 mode active"},
    {"category": "接口", "name": "EtherChannel PAgP", "command": "channel-group <id> mode desirable", "description": "PAgP 动态链路聚合（思科私有）", "example": "Switch(config-if-range)# channel-group 1 mode desirable"},
    {"category": "接口", "name": "LLDP 配置", "command": "lldp run", "description": "全局启用 LLDP", "example": "Switch(config)# lldp run"},
    {"category": "接口", "name": "PoE 供电", "command": "power inline auto", "description": "端口启用 PoE 供电", "example": "Switch(config-if)# power inline auto"},
    {"category": "接口", "name": "接口描述", "command": "description <text>", "description": "为接口添加描述信息", "example": "Switch(config-if)# description Uplink to Core"},
    {"category": "接口", "name": "查看接口状态", "command": "show interfaces status", "description": "查看所有接口状态", "example": "Switch# show interfaces status"},
    {"category": "接口", "name": "查看 EtherChannel", "command": "show etherchannel summary", "description": "查看聚合端口组状态", "example": "Switch# show etherchannel summary"},

    # ── DHCP ──
    {"category": "DHCP", "name": "DHCP 地址池", "command": "ip dhcp pool <name>\n network <net> <mask>\n default-router <gw>\n dns-server <dns>", "description": "创建 DHCP 地址池", "example": "Router(config)# ip dhcp pool LAN\nRouter(dhcp-config)# network 192.168.1.0 255.255.255.0"},
    {"category": "DHCP", "name": "DHCP 排除地址", "command": "ip dhcp excluded-address <low> <high>", "description": "排除 DHCP 地址范围", "example": "Router(config)# ip dhcp excluded-address 192.168.1.1 192.168.1.10"},

    # ── NAT ──
    {"category": "NAT", "name": "PAT 端口复用", "command": "ip nat inside source list <acl> interface <wan-if> overload", "description": "PAT（多对一 NAT）上网配置", "example": "Router(config)# ip nat inside source list 1 interface g0/0 overload"},
    {"category": "NAT", "name": "静态端口映射", "command": "ip nat inside source static <proto> <ip> <port> interface <wan-if> <ext-port>", "description": "端口映射（DNAT）", "example": "Router(config)# ip nat inside source static tcp 192.168.1.10 80 interface g0/0 80"},
    {"category": "NAT", "name": "NAT 内外接口标记", "command": "interface <wan-if>\n ip nat outside\ninterface <lan-if>\n ip nat inside", "description": "标记 NAT 内外接口", "example": "Router(config-if)# ip nat outside"},

    # ── 排错 ──
    {"category": "排错", "name": "Ping 测试", "command": "ping <ip>", "description": "测试网络连通性", "example": "Router# ping 8.8.8.8"},
    {"category": "排错", "name": "Traceroute", "command": "traceroute <ip>", "description": "路由追踪", "example": "Router# traceroute 8.8.8.8"},
    {"category": "排错", "name": "查看接口详情", "command": "show interface <port>", "description": "查看端口详细统计（错误/丢包/速率）", "example": "Switch# show interface g0/1"},
    {"category": "排错", "name": "查看 MAC 地址表", "command": "show mac address-table", "description": "查看 MAC 地址表", "example": "Switch# show mac address-table"},
    {"category": "排错", "name": "查看日志", "command": "show logging", "description": "查看系统日志缓冲区", "example": "Router# show logging"},
    {"category": "排错", "name": "查看 ARP 表", "command": "show ip arp", "description": "查看 ARP 缓存表", "example": "Router# show ip arp"},
]

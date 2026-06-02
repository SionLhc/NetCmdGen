"""MikroTik RouterOS 版本配置映射。

定义 RouterOS V6 / V7 两个版本的关键命令差异。
"""

from enum import Enum


class RouterOSVersion(str, Enum):
    V6 = "v6"   # RouterOS V6（2013-2024，主力版本）
    V7 = "v7"   # RouterOS V7（2021+，新一代路由引擎）


VERSION_COMMANDS = {
    RouterOSVersion.V6: {
        # ─── 系统管理 ───
        "hostname": "/system identity set name={hostname}",
        "ntp_client": "/system ntp client set enabled=yes primary-ntp={ip}",
        "dns_server": "/ip dns set servers={ip} allow-remote-requests=yes",
        # ─── SSH ───
        "ssh_enable": "/ip service set ssh port={port} disabled=no",
        "ssh_key": "/ip ssh regenerate-host-key",
        # ─── 接口 ───
        "ip_address": "/ip address add address={ip}/{mask} interface={interface}",
        "bridge_create": "/interface bridge add name={name}",
        "bridge_port": "/interface bridge port add interface={port} bridge={bridge}",
        # ─── VLAN ───
        "vlan_create": "/interface vlan add name=VLAN{vid} vlan-id={vid} interface={trunk}",
        # ─── 路由 ───
        "static_route": "/ip route add dst-address={dest}/{prefix} gateway={gw}",
        "ospf_instance": "/routing ospf instance set default router-id={rid} distribute-default=never",
        "ospf_network": "/routing ospf network add network={net} area={area}",
        "ospf_area": "/routing ospf area set backbone area-id=0.0.0.0",
        # ─── 防火墙/NAT ───
        "nat_masquerade": "/ip firewall nat add chain=srcnat out-interface={wan} action=masquerade",
        "filter_rule": "/ip firewall filter add chain={chain} action={action} protocol={proto} dst-port={port}",
        # ─── DHCP ───
        "dhcp_server": "/ip dhcp-server setup",
        "dhcp_pool": "/ip pool add name={name} ranges={range}",
        # ─── 用户 ───
        "user_create": "/user add name={user} password={pw} group=full",
    },
    RouterOSVersion.V7: {
        # ─── 系统管理（V7 支持更多服务） ───
        "hostname": "/system identity set name={hostname}",
        "ntp_client": "/system ntp client servers add address={ip}",
        "dns_server": "/ip dns set servers={ip} allow-remote-requests=yes",
        # ─── SSH ───
        "ssh_enable": "/ip service set ssh port={port} disabled=no",
        "ssh_key": "/ip ssh regenerate-host-key",
        # ─── 接口 ───
        "ip_address": "/ip address add address={ip}/{mask} interface={interface}",
        "bridge_create": "/interface bridge add name={name}",
        "bridge_port": "/interface bridge port add interface={port} bridge={bridge}",
        # ─── VLAN（V7 支持 bridge vlan-filtering） ───
        "vlan_create": "/interface vlan add name=VLAN{vid} vlan-id={vid} interface={trunk}",
        # ─── 路由（V7 重写了路由引擎） ───
        "static_route": "/ip route add dst-address={dest}/{prefix} gateway={gw}",
        # V7 OSPF 语法变化
        "ospf_instance": "/routing ospf instance add name=default router-id={rid}\n/routing ospf area add name=backbone area-id=0.0.0.0 instance=default",
        "ospf_network": "/routing ospf interface-template add network={net} area=backbone",
        # ─── 防火墙/NAT ───
        "nat_masquerade": "/ip firewall nat add chain=srcnat out-interface={wan} action=masquerade",
        "filter_rule": "/ip firewall filter add chain={chain} action={action} protocol={proto} dst-port={port}",
        # ─── DHCP ───
        "dhcp_server": "/ip dhcp-server setup",
        "dhcp_pool": "/ip pool add name={name} ranges={range}",
        # ─── 用户 ───
        "user_create": "/user add name={user} password={pw} group=full",
        # ─── V7 新特性 ───
        "wireguard_enable": "/interface wireguard add name=wg1 listen-port=13231",
        "container_enable": "/container config set registry-url=https://registry-1.docker.io tmpdir=disk1/pull",
    },
}


def get_cmd(version: RouterOSVersion, key: str, **kwargs) -> str:
    """根据 RouterOS 版本获取命令片段。"""
    cmds = VERSION_COMMANDS.get(version, VERSION_COMMANDS[RouterOSVersion.V6])
    template = cmds.get(key, VERSION_COMMANDS[RouterOSVersion.V6].get(key, ""))
    if not template:
        return ""
    if kwargs:
        return template.format(**kwargs)
    return template

"""华为 VRP 系统版本配置映射。

定义 V5 / V8 / V300 三个版本的关键命令差异。
其他厂商暂无需区分版本（H3C Comware 版本差异小、锐捷/迈普版本线简单）。
"""

from enum import Enum


class VrpVersion(str, Enum):
    """华为 VRP 系统版本"""
    V5 = "v5"      # VRP V5（2008-2015，如 S5700/S6700 老款）
    V8 = "v8"      # VRP V8/V200（2016+，如 S5720/S6730/CE6800）
    V300 = "v300"  # VRP V300（2020+，如 CloudEngine S/新一代 S 系列）


# ─── 版本差异化命令映射 ──────────────────────────────

VERSION_COMMANDS = {
    VrpVersion.V5: {
        "sysname": "sysname {hostname}",
        "super_password": "super password simple {pw}",
        "ssh_enable": "stelnet server enable\nssh server compatible-huawei-version enable",
        "ssh_start": "stelnet server enable\nssh server port {port}\nssh server timeout 60\nssh server max-auth-times 5\nssh server rekey-interval 60\nssh server compatible-huawei-version enable\nssh version 2",
        "local_user": "local-user {user} password simple {pw}\nlocal-user {user} privilege level {level}\nlocal-user {user} service-type terminal ssh telnet",
        "clock_timezone": "clock timezone UTC+8 add 08:00:00",
        "ntp_server": "ntp-service unicast-server {ip}",
        "snmp_agent": "snmp-agent\nsnmp-agent sys-info version {ver}",
        "snmp_community": "snmp-agent community {type} {name}",
        "acl_prefix": "acl number {num}",
        "config_end": "return",
        "ssh_user": "ssh user {user}\nssh user {user} authentication-type password\nssh user {user} service-type stelnet",
        "user_interface": "user-interface vty 0 4\n authentication-mode aaa\n protocol inbound ssh",
    },
    VrpVersion.V8: {
        "sysname": "sysname {hostname}",
        "super_password": "super password simple {pw}",
        "ssh_enable": "stelnet server enable",
        "ssh_start": "stelnet server enable\nssh server port {port}\nssh server timeout 60\nssh server max-auth-times 5\nssh version 2\nundo ssh server compatible-ssh1x",
        "local_user": "local-user {user} password irreversible-cipher {pw}\nlocal-user {user} privilege level {level}\nlocal-user {user} service-type terminal ssh",
        "clock_timezone": "clock timezone Beijing add 08:00:00",
        "ntp_server": "ntp unicast-server {ip}",
        "snmp_agent": "snmp-agent\nsnmp-agent sys-info version {ver}",
        "snmp_community": "snmp-agent community {type} {name}",
        "acl_prefix": "acl {num}",
        "config_end": "return",
        "ssh_user": "ssh user {user}\nssh user {user} authentication-type password\nssh user {user} service-type stelnet",
        "user_interface": "user-interface vty 0 4\n authentication-mode aaa\n protocol inbound ssh",
    },
    VrpVersion.V300: {
        "sysname": "sysname {hostname}",
        "super_password": "set super password {pw}",
        "ssh_enable": "ssh server enable",
        "ssh_start": "ssh server enable\nssh server port {port}\nssh server timeout 60\nssh server max-auth-times 5\nssh version 2",
        "local_user": "local-user {user} password irreversible-cipher {pw}\nlocal-user {user} privilege level {level}\nlocal-user {user} service-type terminal ssh",
        "clock_timezone": "clock timezone Beijing add 08:00:00",
        "ntp_server": "ntp unicast-server {ip}",
        "snmp_agent": "snmp-agent\nsnmp-agent sys-info version {ver}",
        "snmp_community": "snmp-agent community {type} {name}",
        "acl_prefix": "acl {num}",
        "config_end": "",  # V300 不需要 return
        "ssh_user": "ssh user {user}\nssh user {user} authentication-type password\nssh user {user} service-type stelnet",
        "user_interface": "user-interface vty 0 4\n authentication-mode aaa\n protocol inbound ssh",
    },
}


def get_cmd(version: VrpVersion, key: str, **kwargs) -> str:
    """根据系统版本获取对应的命令片段，支持 .format(**kwargs) 参数填充。

    示例:
        get_cmd(VrpVersion.V8, "local_user", user="admin", pw="Test@123", level=15)
        → "local-user admin password irreversible-cipher Test@123\n..."
    """
    cmds = VERSION_COMMANDS.get(version, VERSION_COMMANDS[VrpVersion.V5])
    template = cmds.get(key, VERSION_COMMANDS[VrpVersion.V5].get(key, ""))
    if not template:
        return ""
    if kwargs:
        return template.format(**kwargs)
    return template

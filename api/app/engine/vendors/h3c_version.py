"""华三 Comware 系统版本配置映射。

定义 Comware V5 / V7 两个版本的关键命令差异。
"""

from enum import Enum


class ComwareVersion(str, Enum):
    """华三 Comware 系统版本"""
    V5 = "v5"  # Comware V5（2008-2015，如 S5500/S5800）
    V7 = "v7"  # Comware V7（2016+，如 S6800/S6850/S12500）


VERSION_COMMANDS = {
    ComwareVersion.V5: {
        "acl_basic": "acl number {num}",
        "acl_advanced": "acl number {num}",
        "ssh_enable": "ssh server enable",
        "ssh_compat": "ssh server compatible-ssh1-{ver} disable",
        "local_user_pwd": "local-user {user}\n password simple {pw}\n service-type ssh\n authorization-attribute level {level}\n quit",
        "super_pwd": "super password simple {pw}",
    },
    ComwareVersion.V7: {
        "acl_basic": "acl basic {num}",
        "acl_advanced": "acl advanced {num}",
        "ssh_enable": "ssh server enable",
        "ssh_compat": "",
        "local_user_pwd": "local-user {user}\n password simple {pw}\n service-type ssh\n authorization-attribute level {level}\n quit",
        "super_pwd": "super password simple {pw}",
    },
}


def get_cmd(version: ComwareVersion, key: str, **kwargs) -> str:
    """根据 Comware 版本获取对应的命令片段。"""
    cmds = VERSION_COMMANDS.get(version, VERSION_COMMANDS[ComwareVersion.V5])
    template = cmds.get(key, VERSION_COMMANDS[ComwareVersion.V5].get(key, ""))
    if not template:
        return ""
    if kwargs:
        return template.format(**kwargs)
    return template

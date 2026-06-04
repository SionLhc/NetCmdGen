"""配置安全审计 — 检测生成的命令中的危险配置"""
from __future__ import annotations

from fastapi import APIRouter, Body

router = APIRouter(prefix="/audit", tags=["audit"])

# 危险配置规则库
AUDIT_RULES = [
    {"id": "no-password", "level": "critical", "pattern": r"(enable password|super password) (?!\w{6,})",
     "msg": "密码为空或过短（建议至少6位）"},
    {"id": "telnet-enabled", "level": "warning", "pattern": r"(?i)telnet server enable",
     "msg": "启用了 Telnet（明文传输），建议使用 SSH"},
    {"id": "http-enabled", "level": "warning", "pattern": r"(?i)(ip http server|http server enable)",
     "msg": "启用了 HTTP 管理（明文），建议使用 HTTPS"},
    {"id": "snmp-public", "level": "warning", "pattern": r"(?i)snmp-agent community read public",
     "msg": "SNMP 团体字使用默认 'public'，存在信息泄露风险"},
    {"id": "snmp-private", "level": "warning", "pattern": r"(?i)snmp-agent community write private",
     "msg": "SNMP 写团体字使用默认 'private'"},
    {"id": "no-logging", "level": "info", "pattern": r"(?i)(logging console|logging buffered)",
     "msg": "日志配置已启用 ✅", "positive": True},
    {"id": "vlan1-untagged", "level": "warning", "pattern": r"(?i)vlan\s+1\b",
     "msg": "使用了 VLAN 1（默认 VLAN），建议使用业务 VLAN"},
    {"id": "no-ntp", "level": "info", "pattern": r"(?i)ntp-service (server|unicast-server)",
     "msg": "NTP 时间同步已配置 ✅", "positive": True},
    {"id": "no-stp", "level": "warning", "pattern": r"(?i)stp disable",
     "msg": "STP 已禁用，存在环路风险"},
    {"id": "weak-encryption", "level": "warning", "pattern": r"(?i)(md5|des)\b.*(?=.*auth|.*encrypt)",
     "msg": "使用了弱加密算法 MD5/DES，建议升级到 SHA/AES"},
    {"id": "any-any-acl", "level": "critical", "pattern": r"(?i)permit\s+ip\s+any\s+any",
     "msg": "存在 any-to-any 放行规则，安全风险极高"},
    {"id": "no-banner", "level": "info", "pattern": r"(?i)banner\s+(motd|login)",
     "msg": "登录 Banner 已配置 ✅", "positive": True},
    {"id": "no-aaa", "level": "critical", "pattern": r"(?i)(aaa|authentication-mode)\s+none",
     "msg": "认证配置为 none，未启用 AAA 认证"},
    {"id": "no-backup", "level": "info", "pattern": r"(?i)(tftp|ftp|scp)\s+.*startup",
     "msg": "配置文件备份已配置 ✅", "positive": True},
]


@router.post("/check", summary="配置安全审计")
def audit_config(config: dict = Body(..., example={"commands": "system-view\nstelnet server enable\nsnmp-agent community read public\n"})):
    """输入配置命令文本 → 返回风险清单 + 评分"""
    commands = config.get("commands", "")
    if not commands:
        return {"score": 100, "issues": [], "summary": "空配置"}

    issues = []
    critical = 0
    warnings = 0

    for rule in AUDIT_RULES:
        import re
        match = re.search(rule["pattern"], commands, re.IGNORECASE | re.MULTILINE)
        is_positive = rule.get("positive", False)

        if match:
            if not is_positive:
                issues.append({
                    "id": rule["id"],
                    "level": rule["level"],
                    "message": rule["msg"],
                    "line": match.group(0)[:80],
                })
                if rule["level"] == "critical":
                    critical += 1
                elif rule["level"] == "warning":
                    warnings += 1
        elif is_positive:
            # 正面的最佳实践未被检测到
            issues.append({
                "id": rule["id"],
                "level": "info",
                "message": rule["msg"].replace("已配置 ✅", "未配置，建议添加"),
                "line": "-",
            })

    # 评分：100 - critical*25 - warning*10
    score = max(0, 100 - critical * 25 - warnings * 10)

    return {
        "score": score,
        "critical": critical,
        "warnings": warnings,
        "issues": issues,
        "summary": f"安全评分 {score}/100，{critical} 严重 + {warnings} 警告"
    }

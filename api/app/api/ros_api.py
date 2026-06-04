"""RouterOS 原生 API 客户端 (端口 8728/8729)，基于 librouteros"""

import ssl
from librouteros import connect as ros_connect, async_connect
from librouteros.login import plain, token

# 连接池缓存：key = (host, port, username) → api 实例
_connections: dict = {}


def _make_key(host: str, port: int, username: str) -> str:
    return f"{host}:{port}:{username}"


def get_api(host: str, port: int, username: str, password: str,
            use_ssl: bool = False) -> object:
    """获取或创建 RouterOS API 连接（同步，带缓存复用）"""
    key = _make_key(host, port, username)
    cached = _connections.get(key)
    if cached:
        try:
            # 尝试 ping 检测连接是否存活
            cached.path("system", "resource")
            return cached
        except Exception:
            # 连接已断，移除缓存后重新连接
            _connections.pop(key, None)

    # 创建新连接
    try:
        if use_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            api = ros_connect(
                host=host, username=username, password=password,
                port=port, ssl_wrapper=ctx.wrap_socket,
                login_method=plain, encoding='UTF-8',
            )
        else:
            api = ros_connect(
                host=host, username=username, password=password,
                port=port, login_method=plain, encoding='UTF-8',
            )
    except (ConnectionRefusedError, OSError) as e:
        raise ConnectionError(
            f"无法连接 {host}:{port}，请在 RouterOS 执行 /ip service enable api 启用 API 服务"
        ) from e
    _connections[key] = api
    return api


def close_connection(host: str, port: int, username: str):
    """关闭指定连接"""
    key = _make_key(host, port, username)
    api = _connections.pop(key, None)
    if api:
        try:
            api.close()
        except Exception:
            pass


def api_select(host: str, port: int, username: str, password: str,
               path: str, use_ssl: bool = False) -> list[dict]:
    """
    查询 RouterOS 菜单数据（等效于 REST GET）
    :param path: 菜单路径，如 "ip/address", "interface"
    :return: 每条记录转为 dict 的列表
    """
    api = get_api(host, port, username, password, use_ssl)
    parts = [p for p in path.split("/") if p]
    ros_path = api.path(*parts)
    results = []
    for item in ros_path:
        results.append(dict(item))
    return results


def api_add(host: str, port: int, username: str, password: str,
            path: str, data: dict, use_ssl: bool = False) -> str:
    """
    创建记录（等效于 REST PUT）
    :return: 新记录的 .id
    """
    api = get_api(host, port, username, password, use_ssl)
    parts = [p for p in path.split("/") if p]
    ros_path = api.path(*parts)
    return ros_path.add(**data)


def api_update(host: str, port: int, username: str, password: str,
               path: str, record_id: str, data: dict,
               use_ssl: bool = False) -> None:
    """
    更新记录（等效于 REST PATCH）
    :param record_id: RouterOS .id，如 "*B" 或 "*1"
    :param data: 要更新的字段
    """
    api = get_api(host, port, username, password, use_ssl)
    parts = [p for p in path.split("/") if p]
    ros_path = api.path(*parts)
    params = dict(data)
    params[".id"] = record_id
    ros_path.update(**params)


def api_delete(host: str, port: int, username: str, password: str,
               path: str, record_id: str, use_ssl: bool = False) -> None:
    """
    删除记录（等效于 REST DELETE）
    :param record_id: RouterOS .id
    """
    api = get_api(host, port, username, password, use_ssl)
    parts = [p for p in path.split("/") if p]
    ros_path = api.path(*parts)
    ros_path.remove(record_id)


def api_get_system(host: str, port: int, username: str, password: str,
                   use_ssl: bool = False) -> dict:
    """获取系统信息（CPU/内存/版本等）"""
    api = get_api(host, port, username, password, use_ssl)
    resources = list(api.path("system", "resource"))
    identity = list(api.path("system", "identity"))
    r = resources[0] if resources else {}
    i = identity[0] if identity else {}
    return {
        "success": True,
        "version": str(r.get("version", "")),
        "cpu_load": str(r.get("cpu-load", "")),
        "uptime": str(r.get("uptime", "")),
        "free_memory": str(r.get("free-memory", "")),
        "total_memory": str(r.get("total-memory", "")),
        "identity": str(i.get("name", "")),
    }

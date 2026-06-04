"""RouterOS 原生 API 客户端 (端口 8728/8729)，基于 librouteros"""

import ssl
from librouteros import connect as ros_connect, async_connect
from librouteros.login import plain, token

# 连接池缓存：key = (host, port, username) → api 实例
_connections: dict = {}


def _make_key(host: str, port: int, username: str) -> str:
    return f"{host}:{port}:{username}"


def _create_conn(host: str, port: int, username: str, password: str,
                 use_ssl: bool = False) -> object:
    """创建新的 API 连接（每次新建，保证线程安全/多请求隔离）"""
    try:
        if use_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ros_connect(
                host=host, username=username, password=password,
                port=port, ssl_wrapper=ctx.wrap_socket,
                login_method=plain, encoding='UTF-8',
            )
        else:
            return ros_connect(
                host=host, username=username, password=password,
                port=port, login_method=plain, encoding='UTF-8',
            )
    except (ConnectionRefusedError, OSError) as e:
        raise ConnectionError(
            f"无法连接 {host}:{port}，请在 RouterOS 执行 "
            f"/ip service enable api 启用 API 服务"
        ) from e


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
    每次新建连接，避免缓存连接在多请求间失效
    """
    api = _create_conn(host, port, username, password, use_ssl)
    try:
        parts = [p for p in path.split("/") if p]
        ros_path = api.path(*parts)
        results = []
        for item in ros_path:
            results.append(dict(item))
        return results
    finally:
        try:
            api.close()
        except Exception:
            pass


def api_add(host: str, port: int, username: str, password: str,
            path: str, data: dict, use_ssl: bool = False) -> str:
    """创建记录（等效于 REST PUT），每次新建连接"""
    api = _create_conn(host, port, username, password, use_ssl)
    try:
        parts = [p for p in path.split("/") if p]
        ros_path = api.path(*parts)
        return ros_path.add(**data)
    finally:
        try: api.close()
        except: pass


def api_update(host: str, port: int, username: str, password: str,
               path: str, record_id: str, data: dict,
               use_ssl: bool = False) -> None:
    """更新记录（等效于 REST PATCH），每次新建连接"""
    api = _create_conn(host, port, username, password, use_ssl)
    try:
        parts = [p for p in path.split("/") if p]
        ros_path = api.path(*parts)
        params = dict(data)
        params[".id"] = record_id
        ros_path.update(**params)
    finally:
        try: api.close()
        except: pass


def api_delete(host: str, port: int, username: str, password: str,
               path: str, record_id: str, use_ssl: bool = False) -> None:
    """删除记录（等效于 REST DELETE），每次新建连接"""
    api = _create_conn(host, port, username, password, use_ssl)
    try:
        parts = [p for p in path.split("/") if p]
        ros_path = api.path(*parts)
        ros_path.remove(record_id)
    finally:
        try: api.close()
        except: pass


def api_get_system(host: str, port: int, username: str, password: str,
                   use_ssl: bool = False) -> dict:
    """获取系统信息，每次新建连接"""
    api = _create_conn(host, port, username, password, use_ssl)
    try:
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
    finally:
        try: api.close()
        except: pass

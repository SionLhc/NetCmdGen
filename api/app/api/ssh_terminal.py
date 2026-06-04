"""SSH 终端 WebSocket — 网页端直连设备"""
from __future__ import annotations

import asyncio
import json
import socket
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import paramiko

router = APIRouter(tags=["ssh-terminal"])


class SSHSession:
    """管理单个 SSH 连接的参数和 channel"""

    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client: Optional[paramiko.SSHClient] = None
        self.channel: Optional[paramiko.channel.Channel] = None

    def connect(self) -> str | None:
        """建立 SSH 连接，返回错误消息或 None"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                self.host, port=self.port,
                username=self.username, password=self.password,
                timeout=10, allow_agent=False, look_for_keys=False,
            )
            self.channel = self.client.invoke_shell(
                term='xterm-256color', width=120, height=40,
            )
            self.channel.settimeout(0.1)
            return None
        except paramiko.AuthenticationException:
            return '认证失败: 用户名或密码错误'
        except socket.timeout:
            return '连接超时: 请检查 IP 和端口'
        except Exception as e:
            return f'连接失败: {e}'

    def close(self):
        if self.channel:
            try:
                self.channel.close()
            except Exception:
                pass
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass


@router.websocket("/ws")
async def ssh_websocket(
    ws: WebSocket,
    host: str = Query(...),
    port: int = Query(default=22),
    username: str = Query(...),
    password: str = Query(...),
):
    """WebSocket SSH 终端 — 双向实时传输"""
    await ws.accept()

    session = SSHSession(host, port, username, password)
    err = session.connect()
    if err:
        await ws.send_text(json.dumps({"type": "error", "message": err}))
        await ws.close()
        return

    await ws.send_text(json.dumps({"type": "connected"}))

    # 后台任务：从 SSH channel 读取数据 → 推送到 WebSocket
    async def read_ssh():
        while session.channel and not session.channel.closed:
            try:
                if session.channel.recv_ready():
                    data = session.channel.recv(4096)
                    if data:
                        await ws.send_bytes(data)
                else:
                    await asyncio.sleep(0.05)
            except Exception:
                break

    # 前台循环：从 WebSocket 读取 → 写入 SSH channel
    read_task = asyncio.ensure_future(read_ssh())
    try:
        while True:
            data = await ws.receive()
            if data['type'] == 'websocket.disconnect':
                break
            if 'bytes' in data and session.channel and not session.channel.closed:
                session.channel.send(data['bytes'])
            elif 'text' in data:
                msg = json.loads(data['text'])
                if msg.get('type') == 'resize':
                    rows = msg.get('rows', 24)
                    cols = msg.get('cols', 80)
                    if session.channel:
                        session.channel.resize_pty(width=cols, height=rows)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        read_task.cancel()
        try:
            await read_task
        except asyncio.CancelledError:
            pass
        session.close()

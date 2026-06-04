"""多人协作拓扑 — WebSocket 实时同步"""
from __future__ import annotations

import asyncio
import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(prefix="/collab", tags=["collaboration"])

# 房间管理：room_id → {client_id: WebSocket}
rooms: Dict[str, Dict[str, WebSocket]] = {}


class CollabMessage(BaseModel):
    """协作消息"""
    type: str = "update"  # update / join / leave
    room_id: str = ""
    client_id: str = ""
    data: dict | None = None


async def _broadcast(room_id: str, message: dict, exclude_client: str = ""):
    """向房间内所有其他客户端广播消息"""
    if room_id not in rooms:
        return
    stale = []
    for cid, ws in rooms[room_id].items():
        if cid == exclude_client:
            continue
        try:
            await ws.send_json(message)
        except Exception:
            stale.append(cid)
    # 清理断开的连接
    for cid in stale:
        rooms[room_id].pop(cid, None)


@router.websocket("/ws/{room_id}")
async def collab_websocket(ws: WebSocket, room_id: str):
    """WebSocket 协作端点"""
    await ws.accept()
    client_id = str(id(ws))[-8:]

    # 加入房间
    if room_id not in rooms:
        rooms[room_id] = {}
    rooms[room_id][client_id] = ws

    # 通知其他人新成员加入
    await _broadcast(room_id, {
        "type": "join",
        "client_id": client_id,
        "online": len(rooms[room_id]),
    }, exclude_client=client_id)

    # 告诉新成员当前在线数
    await ws.send_json({
        "type": "joined",
        "client_id": client_id,
        "online": len(rooms[room_id]),
    })

    try:
        while True:
            # 接收协作消息
            data = await ws.receive_json()
            msg_type = data.get("type", "update")

            if msg_type == "update":
                # 广播拓扑更新给其他人
                await _broadcast(room_id, {
                    "type": "update",
                    "client_id": client_id,
                    "data": data.get("data"),
                    "online": len(rooms[room_id]),
                }, exclude_client=client_id)
            elif msg_type == "cursor":
                # 广播光标位置
                await _broadcast(room_id, {
                    "type": "cursor",
                    "client_id": client_id,
                    "data": data.get("data"),
                }, exclude_client=client_id)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        # 离开房间
        if room_id in rooms:
            rooms[room_id].pop(client_id, None)
            if not rooms[room_id]:
                del rooms[room_id]
            else:
                await _broadcast(room_id, {
                    "type": "leave",
                    "client_id": client_id,
                    "online": len(rooms[room_id]),
                })

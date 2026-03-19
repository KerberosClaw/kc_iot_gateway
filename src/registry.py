"""
Device Registry — in-memory 設備狀態管理
"""

import time
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("registry")


@dataclass
class DeviceState:
    """單一設備的即時狀態"""
    device_id: str
    name: str
    protocol: str
    plugin_name: str
    fields: dict[str, Any] = field(default_factory=dict)
    last_update: float = 0.0
    online: bool = False
    config: dict = field(default_factory=dict)


class DeviceRegistry:
    """設備註冊表，管理所有設備的最新狀態"""

    def __init__(self):
        self._devices: dict[str, DeviceState] = {}
        self._listeners: list = []

    def register(self, device_id: str, name: str, protocol: str,
                 plugin_name: str, config: dict) -> None:
        self._devices[device_id] = DeviceState(
            device_id=device_id,
            name=name,
            protocol=protocol,
            plugin_name=plugin_name,
            config=config,
        )
        log.info(f"Registered device: {device_id} ({protocol})")

    def update(self, device_id: str, data: dict) -> None:
        if device_id not in self._devices:
            log.warning(f"Unknown device: {device_id}")
            return
        state = self._devices[device_id]
        state.fields.update(data)
        state.last_update = time.time()
        state.online = True
        # 通知所有 listener
        for listener in self._listeners:
            asyncio.get_event_loop().call_soon(
                asyncio.ensure_future, listener(device_id, data)
            )

    def get(self, device_id: str) -> DeviceState | None:
        return self._devices.get(device_id)

    def get_all(self) -> list[DeviceState]:
        return list(self._devices.values())

    def get_plugin_name(self, device_id: str) -> str | None:
        state = self._devices.get(device_id)
        return state.plugin_name if state else None

    def is_online(self, device_id: str, timeout: float = 300) -> bool:
        state = self._devices.get(device_id)
        if not state or state.last_update == 0:
            return False
        return (time.time() - state.last_update) < timeout

    def add_listener(self, callback) -> None:
        self._listeners.append(callback)

    def to_dict(self, device_id: str) -> dict | None:
        state = self.get(device_id)
        if not state:
            return None
        return {
            "device_id": state.device_id,
            "name": state.name,
            "protocol": state.protocol,
            "fields": state.fields,
            "online": self.is_online(device_id),
            "last_update": state.last_update,
        }

    def all_to_dict(self) -> list[dict]:
        return [self.to_dict(d.device_id) for d in self._devices.values()]

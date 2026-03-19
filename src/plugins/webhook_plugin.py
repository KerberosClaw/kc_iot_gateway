"""
Webhook Plugin — 接收設備主動 POST 的數據，YAML 配置式 payload 解析
"""

import logging
from typing import Callable

from jsonpath_ng import parse as jsonpath_parse

from ..plugin_base import DevicePlugin

log = logging.getLogger("plugin.webhook")

# FastAPI app 由 gateway 注入
_app = None
_plugin_instance = None


def set_app(app):
    global _app
    _app = app


class WebhookPlugin(DevicePlugin):
    name = "webhook"
    protocol = "webhook"

    def __init__(self):
        self._config: dict = {}
        self._devices: dict[str, dict] = {}
        self._callback: Callable | None = None
        self._last_values: dict[str, dict] = {}

    async def connect(self, config: dict) -> bool:
        self._config = config
        for dev in config.get("devices", []):
            self._devices[dev["id"]] = dev
        log.info(f"Webhook plugin configured: {len(self._devices)} devices")
        return True

    async def read(self, device_id: str, params: dict | None = None) -> dict:
        return self._last_values.get(device_id, {})

    async def write(self, device_id: str, params: dict) -> dict:
        # Webhook 設備通常不支援下行控制
        return {"status": "error", "message": "Webhook devices are read-only"}

    async def start_listening(self, callback: Callable) -> None:
        self._callback = callback
        global _plugin_instance
        _plugin_instance = self

        if _app:
            listen_path = self._config.get("listen_path", "/webhook")
            self._register_route(listen_path)
            log.info(f"Webhook endpoint registered: {listen_path}")

    async def stop_listening(self) -> None:
        pass

    def _register_route(self, path: str) -> None:
        from fastapi import Request

        @_app.post(path)
        async def webhook_receiver(request: Request):
            payload = await request.json()
            device_id = self._identify_device(payload)
            if not device_id:
                return {"status": "error", "message": "Unknown device"}

            data = self._extract_fields(device_id, payload)
            self._last_values[device_id] = data

            if self._callback:
                await self._callback(device_id, data)

            return {"status": "ok", "device": device_id, "received": data}

    def _identify_device(self, payload: dict) -> str | None:
        for dev_id, dev_cfg in self._devices.items():
            identity = dev_cfg.get("identity", {})
            field_path = identity.get("field", "")
            expected = identity.get("value", "")

            try:
                expr = jsonpath_parse(field_path)
                matches = expr.find(payload)
                if matches and str(matches[0].value) == str(expected):
                    return dev_id
            except Exception:
                continue

        return None

    def _extract_fields(self, device_id: str, payload: dict) -> dict:
        dev = self._devices.get(device_id, {})
        fields_def = dev.get("fields", {})
        result = {}

        for field_name, field_cfg in fields_def.items():
            path = field_cfg.get("path", f"$.{field_name}")
            try:
                expr = jsonpath_parse(path)
                matches = expr.find(payload)
                if matches:
                    value = matches[0].value
                    dtype = field_cfg.get("type", "string")
                    if dtype == "float":
                        value = float(value)
                    elif dtype == "int":
                        value = int(value)
                    elif dtype == "bool":
                        value = bool(value)
                    result[field_name] = value
            except Exception:
                pass

        return result

    def get_devices_config(self) -> list[dict]:
        """回傳 webhook 設備清單，供 Dashboard Webhook Simulator 使用"""
        result = []
        for dev_id, dev_cfg in self._devices.items():
            result.append({
                "id": dev_id,
                "name": dev_cfg.get("name", dev_id),
                "identity": dev_cfg.get("identity", {}),
                "fields": dev_cfg.get("fields", {}),
            })
        return result

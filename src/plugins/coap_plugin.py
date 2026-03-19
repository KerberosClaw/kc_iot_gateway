"""
CoAP Plugin — GET/PUT CoAP resources
"""

import asyncio
import logging
from typing import Callable

from ..plugin_base import DevicePlugin

log = logging.getLogger("plugin.coap")

# aiocoap import — optional, graceful fallback
try:
    import aiocoap
    COAP_AVAILABLE = True
except ImportError:
    COAP_AVAILABLE = False
    log.warning("aiocoap not installed, CoAP plugin disabled")


class CoapPlugin(DevicePlugin):
    name = "coap"
    protocol = "coap"

    def __init__(self):
        self._devices: dict[str, dict] = {}
        self._last_values: dict[str, dict] = {}
        self._callback: Callable | None = None
        self._poll_task: asyncio.Task | None = None

    async def connect(self, config: dict) -> bool:
        if not COAP_AVAILABLE:
            log.warning("CoAP plugin skipped: aiocoap not available")
            return False

        for dev in config.get("devices", []):
            self._devices[dev["id"]] = dev

        log.info(f"CoAP plugin configured: {len(self._devices)} devices")
        return True

    async def read(self, device_id: str, params: dict | None = None) -> dict:
        if not COAP_AVAILABLE:
            return {}

        dev = self._devices.get(device_id)
        if not dev:
            raise ValueError(f"Device {device_id} not found")

        host = dev.get("host", "localhost")
        result = {}
        protocol = await aiocoap.Context.create_client_context()

        try:
            for res_name, res_cfg in dev.get("resources", {}).items():
                path = res_cfg.get("path", f"/{res_name}")
                uri = f"coap://{host}{path}"

                request = aiocoap.Message(code=aiocoap.GET, uri=uri)
                try:
                    response = await asyncio.wait_for(
                        protocol.request(request).response, timeout=5
                    )
                    value = response.payload.decode()
                    dtype = res_cfg.get("type", "string")
                    if dtype == "int":
                        value = int(value)
                    elif dtype == "float":
                        value = float(value)
                    elif dtype == "bool":
                        value = value.lower() in ("true", "1", "on")
                    result[res_name] = value
                except Exception as e:
                    log.error(f"CoAP GET error ({uri}): {e}")
        finally:
            await protocol.shutdown()

        self._last_values[device_id] = result
        return result

    async def write(self, device_id: str, params: dict) -> dict:
        if not COAP_AVAILABLE:
            return {"status": "error", "message": "CoAP not available"}

        dev = self._devices.get(device_id)
        if not dev:
            raise ValueError(f"Device {device_id} not found")

        host = dev.get("host", "localhost")
        written = {}
        protocol = await aiocoap.Context.create_client_context()

        try:
            for res_name, value in params.items():
                res_cfg = dev.get("resources", {}).get(res_name)
                if not res_cfg or res_cfg.get("access", "ro") != "rw":
                    continue

                path = res_cfg.get("path", f"/{res_name}")
                uri = f"coap://{host}{path}"

                request = aiocoap.Message(
                    code=aiocoap.PUT, uri=uri,
                    payload=str(value).encode()
                )
                try:
                    await asyncio.wait_for(
                        protocol.request(request).response, timeout=5
                    )
                    written[res_name] = value
                except Exception as e:
                    log.error(f"CoAP PUT error ({uri}): {e}")
        finally:
            await protocol.shutdown()

        return {"status": "ok", "written": written}

    async def start_listening(self, callback: Callable) -> None:
        if not COAP_AVAILABLE:
            return
        self._callback = callback
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop_listening(self) -> None:
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

    async def _poll_loop(self) -> None:
        while True:
            try:
                for device_id in self._devices:
                    data = await self.read(device_id)
                    if data and self._callback:
                        await self._callback(device_id, data)
                await asyncio.sleep(3)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.error(f"CoAP poll error: {e}")
                await asyncio.sleep(5)

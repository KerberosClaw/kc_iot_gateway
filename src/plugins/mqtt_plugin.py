"""
MQTT Plugin — subscribe MQTT topics，解析 JSON payload
"""

import json
import asyncio
import logging
from typing import Callable

import aiomqtt
from jsonpath_ng import parse as jsonpath_parse

from ..plugin_base import DevicePlugin

log = logging.getLogger("plugin.mqtt")


class MqttPlugin(DevicePlugin):
    name = "mqtt"
    protocol = "mqtt"

    def __init__(self):
        self._config: dict = {}
        self._devices: dict[str, dict] = {}  # device_id -> device config
        self._topic_map: dict[str, str] = {}  # topic -> device_id
        self._client: aiomqtt.Client | None = None
        self._callback: Callable | None = None
        self._listen_task: asyncio.Task | None = None
        self._last_values: dict[str, dict] = {}  # device_id -> last data

    async def connect(self, config: dict) -> bool:
        self._config = config
        broker = config.get("broker", "localhost")
        port = config.get("port", 1883)

        # 處理 broker 格式 "host:port"
        if ":" in str(broker) and not isinstance(port, int):
            parts = broker.rsplit(":", 1)
            broker = parts[0]
            port = int(parts[1])
        elif ":" in str(broker):
            parts = str(broker).rsplit(":", 1)
            try:
                port = int(parts[1])
                broker = parts[0]
            except ValueError:
                pass

        self._config["_broker"] = broker
        self._config["_port"] = int(port)

        for dev in config.get("devices", []):
            dev_id = dev["id"]
            self._devices[dev_id] = dev
            topic = dev.get("topic", "")
            if topic:
                self._topic_map[topic] = dev_id

        log.info(f"MQTT plugin configured: {broker}:{port}, {len(self._devices)} devices")
        return True

    async def read(self, device_id: str, params: dict | None = None) -> dict:
        return self._last_values.get(device_id, {})

    async def write(self, device_id: str, params: dict) -> dict:
        dev = self._devices.get(device_id)
        if not dev:
            raise ValueError(f"Device {device_id} not found in MQTT plugin")

        cmd_topic = dev.get("cmd_topic", f"{dev.get('topic', '')}/cmd")
        broker = self._config["_broker"]
        port = self._config["_port"]

        async with aiomqtt.Client(broker, port) as client:
            await client.publish(cmd_topic, json.dumps(params))

        return {"status": "ok", "written": params}

    async def start_listening(self, callback: Callable) -> None:
        self._callback = callback
        self._listen_task = asyncio.create_task(self._listen_loop())

    async def stop_listening(self) -> None:
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

    async def _listen_loop(self) -> None:
        broker = self._config["_broker"]
        port = self._config["_port"]
        topics = list(self._topic_map.keys())

        while True:
            try:
                async with aiomqtt.Client(broker, port) as client:
                    for topic in topics:
                        await client.subscribe(topic)
                    log.info(f"MQTT subscribed to {len(topics)} topics")

                    async for msg in client.messages:
                        topic = str(msg.topic)
                        device_id = self._topic_map.get(topic)
                        if not device_id:
                            continue

                        try:
                            payload = json.loads(msg.payload.decode())
                            data = self._extract_fields(device_id, payload)
                            self._last_values[device_id] = data
                            if self._callback:
                                await self._callback(device_id, data)
                        except Exception as e:
                            log.error(f"MQTT parse error ({topic}): {e}")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.error(f"MQTT connection error: {e}, reconnecting in 5s...")
                await asyncio.sleep(5)

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
                    dtype = field_cfg.get("type", "float")
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

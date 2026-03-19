"""
Gateway Core — 啟動、Plugin 載入、Event Bus、主程式
"""

import os
import asyncio
import logging
import importlib
import pkgutil
from pathlib import Path

import yaml
import uvicorn
from dotenv import load_dotenv

from . import db
from .registry import DeviceRegistry
from .rules import RuleEngine
from .actions.dispatcher import ActionDispatcher
from .actions import device_write
from .plugin_base import DevicePlugin

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("gateway")


class Gateway:
    def __init__(self):
        self.registry = DeviceRegistry()
        self.dispatcher = ActionDispatcher()
        self.rule_engine = RuleEngine(self.dispatcher)
        self.plugins: dict[str, DevicePlugin] = {}
        self._ws_clients: list = []

    async def start(self, devices_path: str = "devices.yaml",
                    rules_path: str = "rules.yaml"):
        # 1. 初始化 DB
        await db.init_db()

        # 2. 載入設備描述檔
        devices_cfg = self._load_yaml(devices_path)
        if not devices_cfg or "plugins" not in devices_cfg:
            log.error(f"Invalid devices config: {devices_path}")
            return

        # 3. 載入 plugins
        plugin_classes = self._discover_plugins()
        for plugin_name, plugin_cfg in devices_cfg["plugins"].items():
            protocol = plugin_cfg.get("protocol", "")
            plugin_cls = plugin_classes.get(protocol)
            if not plugin_cls:
                log.warning(f"No plugin for protocol: {protocol}")
                continue

            plugin = plugin_cls()
            connected = await plugin.connect(plugin_cfg)
            if not connected:
                log.warning(f"Plugin {protocol} failed to connect")
                continue

            self.plugins[plugin_name] = plugin

            # 註冊設備到 Registry
            for dev in plugin_cfg.get("devices", []):
                self.registry.register(
                    device_id=dev["id"],
                    name=dev.get("name", dev["id"]),
                    protocol=protocol,
                    plugin_name=plugin_name,
                    config=dev,
                )

            # 啟動 push 監聽
            await plugin.start_listening(self._on_device_data)

        # 4. 注入 gateway 到 device_write action
        device_write.set_gateway(self)

        # 5. 載入規則
        await self.rule_engine.load_from_yaml(rules_path)

        # 6. 註冊 registry listener（觸發規則引擎）
        self.registry.add_listener(self._on_device_data_for_rules)

        log.info(
            f"Gateway started: {len(self.plugins)} plugins, "
            f"{len(self.registry.get_all())} devices"
        )

    async def stop(self):
        for name, plugin in self.plugins.items():
            await plugin.stop_listening()
            await plugin.disconnect()
        log.info("Gateway stopped")

    async def read_device(self, device_id: str) -> dict:
        plugin = self._get_plugin_for_device(device_id)
        if not plugin:
            raise ValueError(f"Device {device_id} not found")
        data = await plugin.read(device_id)
        if data:
            self.registry.update(device_id, data)
        return data

    async def write_device(self, device_id: str, params: dict) -> dict:
        plugin = self._get_plugin_for_device(device_id)
        if not plugin:
            raise ValueError(f"Device {device_id} not found")
        return await plugin.write(device_id, params)

    async def _on_device_data(self, device_id: str, data: dict) -> None:
        """Push 模式的 callback — 更新 registry"""
        self.registry.update(device_id, data)

    async def _on_device_data_for_rules(self, device_id: str, data: dict) -> None:
        """Registry listener — 觸發規則引擎"""
        await self.rule_engine.evaluate(device_id, data)
        # 通知 WebSocket clients
        await self._notify_ws(device_id, data)

    async def _notify_ws(self, device_id: str, data: dict) -> None:
        import json
        message = json.dumps({
            "type": "device_update",
            "device_id": device_id,
            "data": data,
        })
        dead = []
        for ws in self._ws_clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._ws_clients.remove(ws)

    def add_ws_client(self, ws) -> None:
        self._ws_clients.append(ws)

    def remove_ws_client(self, ws) -> None:
        if ws in self._ws_clients:
            self._ws_clients.remove(ws)

    def _get_plugin_for_device(self, device_id: str) -> DevicePlugin | None:
        plugin_name = self.registry.get_plugin_name(device_id)
        if not plugin_name:
            return None
        return self.plugins.get(plugin_name)

    def _discover_plugins(self) -> dict[str, type]:
        """掃描 plugins 目錄，回傳 {protocol: PluginClass}"""
        result = {}
        plugins_pkg = importlib.import_module(".plugins", package="src")
        plugins_path = Path(plugins_pkg.__file__).parent

        for _, mod_name, _ in pkgutil.iter_modules([str(plugins_path)]):
            if mod_name.startswith("_"):
                continue
            module = importlib.import_module(f".plugins.{mod_name}", package="src")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and issubclass(attr, DevicePlugin)
                        and attr is not DevicePlugin):
                    result[attr.protocol] = attr
                    log.info(f"Discovered plugin: {attr.name} ({attr.protocol})")

        return result

    def _load_yaml(self, path: str) -> dict | None:
        p = Path(path)
        if not p.exists():
            return None
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


# --- 全域實例 ---
gateway = Gateway()


async def main():
    from .api import create_app

    app = create_app(gateway)

    # 注入 app 到 webhook plugin
    from .plugins.webhook_plugin import set_app
    set_app(app)

    await gateway.start()

    config = uvicorn.Config(
        app,
        host=os.getenv("GATEWAY_HOST", "0.0.0.0"),
        port=int(os.getenv("GATEWAY_PORT", "8000")),
        log_level="info",
    )
    server = uvicorn.Server(config)
    try:
        await server.serve()
    finally:
        await gateway.stop()


if __name__ == "__main__":
    asyncio.run(main())

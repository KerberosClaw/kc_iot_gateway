"""
REST API — FastAPI routes for devices, rules, alerts, dashboard
"""

import json
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from . import db

log = logging.getLogger("api")


def create_app(gateway) -> FastAPI:
    app = FastAPI(title="kc_iot_gateway", version="1.0.0")

    # --- Dashboard ---

    static_dir = Path(__file__).parent.parent / "static"
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        index_path = static_dir / "index.html"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return "<h1>kc_iot_gateway</h1><p>Dashboard not found. Place index.html in static/</p>"

    # --- WebSocket ---

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await ws.accept()
        gateway.add_ws_client(ws)
        try:
            # 先送一次全部設備狀態
            devices = gateway.registry.all_to_dict()
            await ws.send_text(json.dumps({"type": "init", "devices": devices}))
            # 保持連線
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            gateway.remove_ws_client(ws)

    # --- Device API ---

    @app.get("/api/devices")
    async def list_devices():
        return gateway.registry.all_to_dict()

    @app.get("/api/devices/{device_id}")
    async def get_device(device_id: str):
        result = gateway.registry.to_dict(device_id)
        if not result:
            raise HTTPException(404, f"Device {device_id} not found")
        return result

    @app.get("/api/devices/{device_id}/read")
    async def read_device(device_id: str):
        try:
            data = await gateway.read_device(device_id)
            return {"device": device_id, **data}
        except ValueError as e:
            raise HTTPException(404, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    @app.post("/api/devices/{device_id}/write")
    async def write_device(device_id: str, request: Request):
        try:
            params = await request.json()
            result = await gateway.write_device(device_id, params)
            return result
        except ValueError as e:
            raise HTTPException(404, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    @app.get("/api/devices/{device_id}/status")
    async def device_status(device_id: str):
        state = gateway.registry.get(device_id)
        if not state:
            raise HTTPException(404, f"Device {device_id} not found")
        return {
            "device_id": device_id,
            "online": gateway.registry.is_online(device_id),
            "last_update": state.last_update,
            "protocol": state.protocol,
        }

    # --- Rules API ---

    @app.get("/api/rules")
    async def list_rules():
        return await db.load_rules()

    @app.post("/api/rules")
    async def create_rule(request: Request):
        rule = await request.json()
        if not rule.get("name"):
            raise HTTPException(400, "Rule must have a 'name'")
        await db.upsert_rule(rule)
        await gateway.rule_engine.reload()
        return {"status": "ok", "rule": rule["name"]}

    @app.put("/api/rules/{rule_name}")
    async def update_rule(rule_name: str, request: Request):
        existing = await db.get_rule(rule_name)
        if not existing:
            raise HTTPException(404, f"Rule {rule_name} not found")
        updates = await request.json()
        existing.update(updates)
        existing["name"] = rule_name
        await db.upsert_rule(existing)
        await gateway.rule_engine.reload()
        return {"status": "ok", "rule": rule_name, "updated": True}

    @app.delete("/api/rules/{rule_name}")
    async def delete_rule(rule_name: str):
        deleted = await db.delete_rule(rule_name)
        if not deleted:
            raise HTTPException(404, f"Rule {rule_name} not found")
        await gateway.rule_engine.reload()
        return {"status": "ok", "rule": rule_name, "deleted": True}

    @app.patch("/api/rules/{rule_name}/toggle")
    async def toggle_rule(rule_name: str):
        result = await db.toggle_rule(rule_name)
        if not result:
            raise HTTPException(404, f"Rule {rule_name} not found")
        await gateway.rule_engine.reload()
        return {"status": "ok", "rule": rule_name, "active": result["active"]}

    # --- Alerts API ---

    @app.get("/api/alerts")
    async def list_alerts(severity: str | None = None, limit: int = 50):
        return await db.get_alerts(severity=severity, limit=limit)

    # --- Webhook Simulator config (for Dashboard) ---

    @app.get("/api/webhook-devices")
    async def webhook_devices():
        """回傳 webhook 設備配置，供 Dashboard Webhook Simulator 使用"""
        for name, plugin in gateway.plugins.items():
            if hasattr(plugin, "get_devices_config"):
                return plugin.get_devices_config()
        return []

    return app

"""REST API 測試"""

import pytest
from httpx import AsyncClient, ASGITransport

from src import db
from src.gateway import Gateway
from src.api import create_app


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    db.DB_PATH = str(tmp_path / "test.db")
    await db.init_db()
    yield


@pytest.fixture
async def client():
    gw = Gateway()
    app = create_app(gw)
    # 註冊一個假設備
    gw.registry.register("test_dev", "Test Device", "mock", "mock_plugin", {})
    gw.registry.update("test_dev", {"temperature": 25.0})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestDeviceAPI:
    async def test_list_devices(self, client):
        resp = await client.get("/api/devices")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["device_id"] == "test_dev"

    async def test_get_device(self, client):
        resp = await client.get("/api/devices/test_dev")
        assert resp.status_code == 200
        assert resp.json()["device_id"] == "test_dev"

    async def test_get_device_not_found(self, client):
        resp = await client.get("/api/devices/nonexistent")
        assert resp.status_code == 404

    async def test_device_status(self, client):
        resp = await client.get("/api/devices/test_dev/status")
        assert resp.status_code == 200
        assert resp.json()["online"] is True


class TestRulesAPI:
    async def test_create_and_list(self, client):
        resp = await client.post("/api/rules", json={
            "name": "test_rule",
            "device": "test_dev",
            "condition": {"field": "temp", "operator": ">", "threshold": 30},
            "actions": [{"type": "console"}],
        })
        assert resp.status_code == 200

        resp = await client.get("/api/rules")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_update_rule(self, client):
        await client.post("/api/rules", json={
            "name": "r1", "condition": {}, "actions": [],
        })
        resp = await client.put("/api/rules/r1", json={
            "description": "Updated",
        })
        assert resp.status_code == 200
        assert resp.json()["updated"] is True

    async def test_delete_rule(self, client):
        await client.post("/api/rules", json={
            "name": "r1", "condition": {}, "actions": [],
        })
        resp = await client.delete("/api/rules/r1")
        assert resp.status_code == 200

    async def test_toggle_rule(self, client):
        await client.post("/api/rules", json={
            "name": "r1", "condition": {}, "actions": [],
        })
        resp = await client.patch("/api/rules/r1/toggle")
        assert resp.status_code == 200
        assert resp.json()["active"] is False


class TestAlertsAPI:
    async def test_list_alerts(self, client):
        await db.add_alert("r1", "d1", "critical", "test", "42")
        resp = await client.get("/api/alerts")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_filter_alerts(self, client):
        await db.add_alert("r1", "d1", "critical", "msg1", "1")
        await db.add_alert("r2", "d2", "warning", "msg2", "2")
        resp = await client.get("/api/alerts?severity=critical")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

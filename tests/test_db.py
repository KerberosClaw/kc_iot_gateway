"""SQLite DB 單元測試"""

import os
import pytest
from src import db


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    db.DB_PATH = str(tmp_path / "test.db")
    await db.init_db()
    yield


class TestRulesCRUD:
    async def test_upsert_and_load(self):
        await db.upsert_rule({
            "name": "test_rule",
            "description": "Test",
            "device": "dev1",
            "condition": {"field": "temp", "operator": ">", "threshold": 30},
            "severity": "critical",
            "cooldown": 60,
            "actions": [{"type": "console"}],
        })
        rules = await db.load_rules()
        assert len(rules) == 1
        assert rules[0]["name"] == "test_rule"
        assert rules[0]["condition"]["threshold"] == 30

    async def test_get_rule(self):
        await db.upsert_rule({"name": "r1", "condition": {}, "actions": []})
        rule = await db.get_rule("r1")
        assert rule is not None
        assert rule["name"] == "r1"

    async def test_get_missing_rule(self):
        assert await db.get_rule("nonexistent") is None

    async def test_delete_rule(self):
        await db.upsert_rule({"name": "r1", "condition": {}, "actions": []})
        assert await db.delete_rule("r1")
        assert await db.get_rule("r1") is None

    async def test_delete_missing(self):
        assert not await db.delete_rule("nonexistent")

    async def test_toggle_rule(self):
        await db.upsert_rule({"name": "r1", "condition": {}, "actions": [], "active": True})
        result = await db.toggle_rule("r1")
        assert result["active"] is False
        result = await db.toggle_rule("r1")
        assert result["active"] is True


class TestAlerts:
    async def test_add_and_get(self):
        await db.add_alert("rule1", "dev1", "critical", "temp high", "42")
        alerts = await db.get_alerts()
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "critical"

    async def test_filter_by_severity(self):
        await db.add_alert("r1", "d1", "critical", "msg1", "1")
        await db.add_alert("r2", "d2", "warning", "msg2", "2")
        critical = await db.get_alerts(severity="critical")
        assert len(critical) == 1
        all_alerts = await db.get_alerts()
        assert len(all_alerts) == 2

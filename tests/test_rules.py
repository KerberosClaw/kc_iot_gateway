"""Rule Engine 單元測試"""

import pytest
from unittest.mock import AsyncMock
from src import db
from src.rules import RuleEngine
from src.actions.dispatcher import ActionDispatcher


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    db.DB_PATH = str(tmp_path / "test.db")
    await db.init_db()
    yield


@pytest.fixture
def engine():
    dispatcher = ActionDispatcher()
    return RuleEngine(dispatcher)


class TestRuleEngine:
    async def test_evaluate_triggers(self, engine):
        await db.upsert_rule({
            "name": "high_temp",
            "device": "dev1",
            "condition": {"field": "temperature", "operator": ">", "threshold": 30},
            "severity": "critical",
            "cooldown": 0,
            "actions": [{"type": "console", "message": "temp={value}"}],
            "active": True,
        })
        await engine.reload()

        await engine.evaluate("dev1", {"temperature": 35})
        alerts = await db.get_alerts()
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "critical"

    async def test_evaluate_no_trigger(self, engine):
        await db.upsert_rule({
            "name": "high_temp",
            "device": "dev1",
            "condition": {"field": "temperature", "operator": ">", "threshold": 30},
            "cooldown": 0,
            "actions": [{"type": "console"}],
            "active": True,
        })
        await engine.reload()

        await engine.evaluate("dev1", {"temperature": 25})
        alerts = await db.get_alerts()
        assert len(alerts) == 0

    async def test_wildcard_device(self, engine):
        await db.upsert_rule({
            "name": "all_temp",
            "device": "*",
            "condition": {"field": "temperature", "operator": ">", "threshold": 30},
            "cooldown": 0,
            "actions": [{"type": "console"}],
            "active": True,
        })
        await engine.reload()

        await engine.evaluate("any_device", {"temperature": 35})
        alerts = await db.get_alerts()
        assert len(alerts) == 1

    async def test_inactive_rule_skipped(self, engine):
        await db.upsert_rule({
            "name": "disabled",
            "device": "dev1",
            "condition": {"field": "temperature", "operator": ">", "threshold": 30},
            "cooldown": 0,
            "actions": [{"type": "console"}],
            "active": False,
        })
        await engine.reload()

        await engine.evaluate("dev1", {"temperature": 35})
        alerts = await db.get_alerts()
        assert len(alerts) == 0

    async def test_cooldown_prevents_duplicate(self, engine):
        await db.upsert_rule({
            "name": "temp_rule",
            "device": "dev1",
            "condition": {"field": "temperature", "operator": ">", "threshold": 30},
            "cooldown": 999,
            "actions": [{"type": "console"}],
            "active": True,
        })
        await engine.reload()

        await engine.evaluate("dev1", {"temperature": 35})
        await engine.evaluate("dev1", {"temperature": 36})
        alerts = await db.get_alerts()
        assert len(alerts) == 1  # second one blocked by cooldown

    async def test_device_mismatch_skipped(self, engine):
        await db.upsert_rule({
            "name": "dev1_only",
            "device": "dev1",
            "condition": {"field": "temperature", "operator": ">", "threshold": 30},
            "cooldown": 0,
            "actions": [{"type": "console"}],
            "active": True,
        })
        await engine.reload()

        await engine.evaluate("dev2", {"temperature": 35})
        alerts = await db.get_alerts()
        assert len(alerts) == 0

"""Cooldown Manager 單元測試"""

import time
from src.cooldown import CooldownManager


class TestCooldownManager:
    def test_first_fire(self):
        cm = CooldownManager()
        assert cm.can_fire("rule1", 60)

    def test_cooldown_blocks(self):
        cm = CooldownManager()
        cm.mark_fired("rule1")
        assert not cm.can_fire("rule1", 60)

    def test_cooldown_expires(self):
        cm = CooldownManager()
        cm._last_fired["rule1"] = time.time() - 61
        assert cm.can_fire("rule1", 60)

    def test_different_rules_independent(self):
        cm = CooldownManager()
        cm.mark_fired("rule1")
        assert cm.can_fire("rule2", 60)

    def test_reset(self):
        cm = CooldownManager()
        cm.mark_fired("rule1")
        cm.reset("rule1")
        assert cm.can_fire("rule1", 60)

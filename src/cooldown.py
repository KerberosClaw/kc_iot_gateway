"""
Cooldown Manager — 防止告警風暴
"""

import time


class CooldownManager:
    """追蹤每條規則的最後觸發時間，在 cooldown 時間內不重複觸發"""

    def __init__(self):
        self._last_fired: dict[str, float] = {}

    def can_fire(self, rule_name: str, cooldown_seconds: int) -> bool:
        last = self._last_fired.get(rule_name, 0)
        return (time.time() - last) >= cooldown_seconds

    def mark_fired(self, rule_name: str) -> None:
        self._last_fired[rule_name] = time.time()

    def reset(self, rule_name: str) -> None:
        self._last_fired.pop(rule_name, None)

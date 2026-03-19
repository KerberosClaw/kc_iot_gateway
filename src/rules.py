"""
Rule Engine — YAML 規則載入 + 條件評估 + 動作分發
"""

import logging
import operator
from pathlib import Path

import yaml

from . import db
from .cooldown import CooldownManager

log = logging.getLogger("rules")

OPERATORS = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


class RuleEngine:
    """規則引擎：評估設備數據，觸發告警動作"""

    def __init__(self, action_dispatcher):
        self._rules: list[dict] = []
        self._cooldown = CooldownManager()
        self._dispatcher = action_dispatcher

    async def load_from_yaml(self, path: str | Path) -> None:
        path = Path(path)
        if not path.exists():
            log.warning(f"Rules file not found: {path}")
            return

        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not raw or "rules" not in raw:
            log.warning(f"No rules found in {path}")
            return

        for rule in raw["rules"]:
            rule["active"] = rule.get("active", True)
            await db.upsert_rule(rule)

        await self.reload()
        log.info(f"Loaded {len(self._rules)} rules from {path}")

    async def reload(self) -> None:
        self._rules = await db.load_rules()

    async def evaluate(self, device_id: str, data: dict) -> None:
        for rule in self._rules:
            if not rule.get("active", True):
                continue

            # 檢查設備匹配
            rule_device = rule.get("device", "*")
            if rule_device != "*" and rule_device != device_id:
                continue

            condition = rule.get("condition", {})
            triggered = False

            # 條件類型：值比較
            if "field" in condition and "operator" in condition:
                field = condition["field"]
                if field not in data:
                    continue
                op_str = condition["operator"]
                threshold = condition["threshold"]
                op_func = OPERATORS.get(op_str)
                if op_func and op_func(data[field], threshold):
                    triggered = True

            if not triggered:
                continue

            # Cooldown 檢查
            cooldown = rule.get("cooldown", 300)
            if not self._cooldown.can_fire(rule["name"], cooldown):
                continue

            self._cooldown.mark_fired(rule["name"])

            # 取得觸發值
            field = condition.get("field", "")
            value = data.get(field, "")

            log.warning(
                f"Rule triggered: {rule['name']} "
                f"(device={device_id}, {field}={value})"
            )

            # 記錄告警
            message = f"{rule['name']}: {field}={value}"
            await db.add_alert(
                rule_name=rule["name"],
                device_id=device_id,
                severity=rule.get("severity", "info"),
                message=message,
                value=str(value),
            )

            # 執行動作
            context = {
                "device_id": device_id,
                "device_name": device_id,
                "field": field,
                "value": value,
                "severity": rule.get("severity", "info"),
                "rule_name": rule["name"],
            }

            for action in rule.get("actions", []):
                await self._dispatcher.dispatch(action, context)

    @property
    def rules(self) -> list[dict]:
        return self._rules

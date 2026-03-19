"""Console Action — 輸出到 stdout，開發偵錯用"""

import logging

log = logging.getLogger("action.console")


async def execute(action: dict, context: dict) -> None:
    message = action.get("message", "{rule_name}: {device_name} {field}={value}")
    formatted = message.format(**context)
    log.warning(f"[ALERT] {formatted}")

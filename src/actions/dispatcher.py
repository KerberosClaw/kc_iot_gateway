"""
Action Dispatcher — 根據 action type 分發到對應的 action 模組
"""

import logging
from . import console, telegram, webhook, device_write

log = logging.getLogger("dispatcher")

ACTION_MAP = {
    "console": console.execute,
    "telegram": telegram.execute,
    "webhook": webhook.execute,
    "device_write": device_write.execute,
}


class ActionDispatcher:
    async def dispatch(self, action: dict, context: dict) -> None:
        action_type = action.get("type", "console")
        handler = ACTION_MAP.get(action_type)
        if not handler:
            log.warning(f"Unknown action type: {action_type}")
            return
        try:
            await handler(action, context)
        except Exception as e:
            log.error(f"Action {action_type} failed: {e}")

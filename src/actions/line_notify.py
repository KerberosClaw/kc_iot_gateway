"""LINE Notify Action — 推送告警到 LINE"""

import os
import logging
import httpx

log = logging.getLogger("action.line_notify")

LINE_API = "https://notify-api.line.me/api/notify"


async def execute(action: dict, context: dict) -> None:
    token = os.getenv("LINE_NOTIFY_TOKEN")
    if not token:
        log.warning("LINE_NOTIFY_TOKEN not set, skipping")
        return

    message = action.get("message", "{rule_name}: {device_name} {field}={value}")
    formatted = message.format(**context)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                LINE_API,
                headers={"Authorization": f"Bearer {token}"},
                data={"message": formatted},
                timeout=10,
            )
            if resp.status_code == 200:
                log.info(f"LINE Notify sent: {formatted}")
            else:
                log.error(f"LINE Notify failed: {resp.status_code} {resp.text}")
    except Exception as e:
        log.error(f"LINE Notify error: {e}")

"""Telegram Bot Action — 推送告警到 Telegram"""

import os
import logging
import httpx

log = logging.getLogger("action.telegram")


async def execute(action: dict, context: dict) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        log.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set, skipping")
        return

    message = action.get("message", "{rule_name}: {device_name} {field}={value}")
    formatted = message.format(**context)

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={"chat_id": chat_id, "text": formatted},
                timeout=10,
            )
            if resp.status_code == 200:
                log.info(f"Telegram sent: {formatted}")
            else:
                log.error(f"Telegram failed: {resp.status_code} {resp.text}")
    except Exception as e:
        log.error(f"Telegram error: {e}")

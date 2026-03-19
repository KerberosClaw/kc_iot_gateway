"""Webhook Action — POST JSON 到指定 URL"""

import logging
import httpx

log = logging.getLogger("action.webhook")


async def execute(action: dict, context: dict) -> None:
    url = action.get("url")
    if not url:
        log.warning("Webhook action missing 'url'")
        return

    payload = {
        "rule": context.get("rule_name"),
        "device": context.get("device_id"),
        "severity": context.get("severity"),
        "field": context.get("field"),
        "value": context.get("value"),
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10)
            log.info(f"Webhook sent to {url}: {resp.status_code}")
    except Exception as e:
        log.error(f"Webhook error ({url}): {e}")

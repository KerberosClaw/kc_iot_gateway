"""Device Write Action — 跨設備聯動，觸發後控制另一台設備"""

import logging

log = logging.getLogger("action.device_write")

# gateway 會在啟動時注入
_gateway = None


def set_gateway(gateway):
    global _gateway
    _gateway = gateway


async def execute(action: dict, context: dict) -> None:
    target = action.get("target_device")
    params = action.get("params", {})
    if not target:
        log.warning("device_write action missing 'target_device'")
        return

    if not _gateway:
        log.error("Gateway not injected into device_write action")
        return

    try:
        result = await _gateway.write_device(target, params)
        log.info(f"Device write: {target} <- {params} => {result}")
    except Exception as e:
        log.error(f"Device write error ({target}): {e}")

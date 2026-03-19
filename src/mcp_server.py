"""
MCP Server — 讓 AI Agent 透過 MCP 協議操作所有設備
"""

import json
from fastmcp import FastMCP
from . import db

mcp = FastMCP("kc-iot-gateway")

# gateway 實例由 main 注入
_gateway = None


def set_gateway(gateway):
    global _gateway
    _gateway = gateway


@mcp.tool()
async def list_devices() -> str:
    """List all connected IoT devices with their protocol and status.
    列出所有已連接的 IoT 設備及其協議和狀態。"""
    devices = _gateway.registry.all_to_dict()
    return json.dumps(devices, indent=2, ensure_ascii=False)


@mcp.tool()
async def read_device(device: str, field: str = "") -> str:
    """Read data from a device. Optionally specify a field name.
    讀取設備數據，可指定欄位名稱。

    Args:
        device: Device ID (e.g. "factory_temp_01", "plc_01")
        field: Optional field name (e.g. "temperature"). If empty, returns all fields.
    """
    try:
        data = await _gateway.read_device(device)
        if field and field in data:
            result = {"device": device, field: data[field]}
        else:
            result = {"device": device, **data}
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def write_device(device: str, params: str) -> str:
    """Write/control a device. Params is a JSON string of key-value pairs.
    控制設備，params 為 JSON 格式的鍵值對。

    Args:
        device: Device ID (e.g. "plc_01")
        params: JSON string (e.g. '{"motor_speed": 1500}')
    """
    try:
        params_dict = json.loads(params)
        result = await _gateway.write_device(device, params_dict)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def device_status(device: str) -> str:
    """Check if a device is online.
    檢查設備是否在線。

    Args:
        device: Device ID
    """
    state = _gateway.registry.get(device)
    if not state:
        return json.dumps({"error": f"Device {device} not found"})

    result = {
        "device": device,
        "name": state.name,
        "protocol": state.protocol,
        "online": _gateway.registry.is_online(device),
        "last_update": state.last_update,
    }
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def list_rules() -> str:
    """List all alert rules.
    列出所有告警規則。"""
    rules = await db.load_rules()
    return json.dumps(rules, indent=2, ensure_ascii=False)


@mcp.tool()
async def list_alerts(severity: str = "", limit: int = 20) -> str:
    """Query recent alerts, optionally filtered by severity.
    查詢最近的告警，可依嚴重等級篩選。

    Args:
        severity: Filter by severity (critical/warning/info). Empty for all.
        limit: Number of alerts to return (default 20)
    """
    alerts = await db.get_alerts(
        severity=severity if severity else None,
        limit=limit,
    )
    return json.dumps(alerts, indent=2, ensure_ascii=False)

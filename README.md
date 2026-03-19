# "Read the factory temperature" — IoT Gateway

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple.svg)](https://modelcontextprotocol.io)

[正體中文](README_zh.md)

Plugin-based IoT gateway that unifies device communication across MQTT, Modbus TCP, CoAP, and Webhook behind a single REST API. Includes a YAML-driven rule engine for alerting, a real-time web dashboard, an MCP server for AI agent integration, and Docker Compose one-click deployment.

Inspired by a production IoT platform managing 28 device plugins across 6 protocols and 10+ brands.

---

## Features

- **Multi-protocol support** — MQTT, Modbus TCP, CoAP, Webhook — all through one API
- **Plugin architecture** — add a new protocol by dropping a single .py file, no core changes
- **YAML device profiles** — define devices, fields, and data types in one config file
- **Rule engine** — YAML-defined alert rules with cooldown, severity levels, and cross-device automation
- **Multi-channel alerts** — LINE Notify, Telegram, Webhook, and device-to-device control
- **Real-time dashboard** — WebSocket-powered web UI with live device data and alert history
- **Webhook simulator** — built-in web UI to test webhook devices without external tools
- **MCP server** — let AI agents read/write devices via natural language
- **AI agent skill** — CLI wrapper for OpenClaw and other LLM agents
- **Docker-ready** — `docker compose up -d` starts everything including simulators

---

## Quick Start

### Local Development

```bash
git clone https://github.com/KerberosClaw/kc_iot_gateway.git
cd kc_iot_gateway
uv sync

# Start simulators
uv run python simulators/modbus_simulator.py &

# Start gateway
uv run python -m src
# Dashboard: http://localhost:8000
```

### Docker Compose

```bash
docker compose up -d
open http://localhost:8000
```

This starts:
- Mosquitto MQTT broker (port 1883)
- MQTT sensor simulator
- Modbus PLC simulator (port 5020)
- Gateway + Dashboard (port 8000)

---

## Architecture

```
AI Agent (Claude / OpenClaw)
  ↕ MCP Protocol
MCP Server (FastMCP)
  ↕
REST API (FastAPI) + WebSocket + Dashboard
  ↕
┌─────────────────────────┐
│      Gateway Core       │
│  Registry + Event Bus   │
│  Rule Engine + Actions  │
├─────────┬───────────────┤
│ Plugins │   Actions     │
│ ┌─────┐ │ ┌───────────┐ │
│ │MQTT │ │ │LINE Notify│ │
│ │Modb.│ │ │Telegram   │ │
│ │CoAP │ │ │Webhook    │ │
│ │WebHk│ │ │DevWrite   │ │
│ └─────┘ │ └───────────┘ │
└─────────┴───────────────┘
      ↕           ↕
   Devices    Notifications
```

---

## Device Profile (YAML)

Define devices in `devices.yaml`:

```yaml
plugins:
  mqtt_sensor:
    protocol: mqtt
    broker: localhost:1883
    devices:
      - id: factory_temp_01
        name: "Factory temperature sensor"
        topic: factory/sensor/temp_01
        fields:
          temperature: { path: "$.temp", unit: "°C", type: float }
          humidity: { path: "$.hum", unit: "%RH", type: float }

  modbus_plc:
    protocol: modbus
    host: localhost
    port: 5020
    slave_id: 1
    devices:
      - id: plc_01
        name: "Production PLC"
        registers:
          motor_speed: { address: 4, type: uint16, unit: "RPM", access: rw }
          temperature: { address: 0, type: float32, unit: "°C", access: ro }

  webhook_devices:
    protocol: webhook
    listen_path: /webhook
    devices:
      - id: env_sensor_01
        name: "Environment sensor (Vendor A)"
        identity:
          field: "$.device_id"
          value: "ENV-001"
        fields:
          temperature: { path: "$.data.temp", unit: "°C", type: float }
```

---

## Alert Rules (YAML)

Define alert rules in `rules.yaml`:

```yaml
rules:
  - name: high_temperature
    device: factory_temp_01
    condition:
      field: temperature
      operator: ">"
      threshold: 40
    severity: critical
    cooldown: 300
    actions:
      - type: line_notify
        message: "[ALERT] {device_name} temp {value}°C"
      - type: telegram
        message: "🔥 {device_name} temperature {value}°C"

  - name: pump_auto_control
    device: plc_01
    condition:
      field: temperature
      operator: ">"
      threshold: 35
    actions:
      - type: device_write
        target_device: plc_01
        params: { pump_on: true }
```

Rules support:
- **Cooldown** — prevent alert storms
- **Cross-device automation** — trigger device control from sensor readings
- **Runtime modification** — update rules via REST API without restart

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devices` | List all devices |
| GET | `/api/devices/{id}/read` | Read device data |
| POST | `/api/devices/{id}/write` | Control device |
| GET | `/api/devices/{id}/status` | Device online status |
| GET | `/api/rules` | List alert rules |
| POST | `/api/rules` | Create rule |
| PUT | `/api/rules/{name}` | Update rule |
| DELETE | `/api/rules/{name}` | Delete rule |
| PATCH | `/api/rules/{name}/toggle` | Enable/disable rule |
| GET | `/api/alerts` | Alert history |

---

## MCP Server

AI agents can control all devices via MCP:

| Tool | Description |
|------|-------------|
| `list_devices` | List all devices with status |
| `read_device` | Read device data |
| `write_device` | Control a device |
| `device_status` | Check if device is online |
| `list_rules` | List alert rules |
| `list_alerts` | Query recent alerts |

---

## Project Structure

```
kc_iot_gateway/
├── src/
│   ├── gateway.py            # Core: startup, plugin loader, event bus
│   ├── plugin_base.py        # DevicePlugin ABC
│   ├── registry.py           # Device registry (in-memory state)
│   ├── api.py                # REST API (FastAPI)
│   ├── mcp_server.py         # MCP Server (FastMCP)
│   ├── rules.py              # Rule engine
│   ├── cooldown.py           # Cooldown manager
│   ├── db.py                 # SQLite (rules + alert history)
│   ├── plugins/
│   │   ├── mqtt_plugin.py
│   │   ├── modbus_plugin.py
│   │   ├── coap_plugin.py
│   │   └── webhook_plugin.py
│   └── actions/
│       ├── line_notify.py
│       ├── telegram.py
│       ├── webhook.py
│       ├── device_write.py
│       └── console.py
├── static/
│   └── index.html            # Dashboard + Webhook Simulator
├── simulators/
│   ├── mqtt_simulator.py
│   └── modbus_simulator.py
├── ai_agent_skill/           # AI agent CLI wrapper
├── tests/                    # Automated tests
├── docs/
│   └── DESIGN.md             # Design document
├── devices.yaml
├── rules.yaml
├── docker-compose.yml
└── Dockerfile
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY_HOST` | `0.0.0.0` | Gateway bind address |
| `GATEWAY_PORT` | `8000` | Gateway port |
| `MQTT_BROKER` | `localhost` | MQTT broker host |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `LINE_NOTIFY_TOKEN` | | LINE Notify token (optional) |
| `TELEGRAM_BOT_TOKEN` | | Telegram bot token (optional) |
| `TELEGRAM_CHAT_ID` | | Telegram chat ID (optional) |

---

## TODO

- [ ] Dashboard Phase 2: React + Tailwind + shadcn/ui + Recharts
- [ ] More notification channels (Email, Discord)
- [ ] AND/OR compound rule conditions
- [ ] Plugin hot-reload without restart

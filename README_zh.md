# 「讀取工廠溫度」— IoT Gateway

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple.svg)](https://modelcontextprotocol.io)

[English](README.md)

Plugin 架構的 IoT Gateway，將 MQTT、Modbus TCP、CoAP、Webhook 設備統一在一個 REST API 後面。內建 YAML 驅動的規則引擎、即時 Web Dashboard、MCP Server（AI Agent 整合）、Docker Compose 一鍵部署。

設計理念來自實際生產環境：管理 28 種設備插件、6 種協議、10+ 品牌的 IoT 平台。

---

## 功能

- **多協議支援** — MQTT、Modbus TCP、CoAP、Webhook，統一 API 存取
- **Plugin 架構** — 新增協議只要加一個 .py 檔，核心不動
- **YAML 設備描述檔** — 統一定義設備、欄位、資料型別
- **規則引擎** — YAML 定義告警規則，支援 cooldown、severity 分級、跨設備聯動
- **多通道告警** — Telegram、Webhook、設備控制聯動
- **即時 Dashboard** — WebSocket 驅動，即時顯示設備數據和告警
- **Webhook 模擬器** — Dashboard 內建 Web UI，不需要外部工具
- **MCP Server** — 讓 AI Agent 用自然語言操作設備
- **AI Agent Skill** — OpenClaw 等 LLM agent 的 CLI wrapper
- **Docker 一鍵啟動** — `docker compose up -d` 啟動所有服務和模擬器

---

## 快速開始

### 本地開發

```bash
git clone https://github.com/KerberosClaw/kc_iot_gateway.git
cd kc_iot_gateway
uv sync

# 啟動模擬器
uv run python simulators/modbus_simulator.py &

# 啟動 Gateway
uv run python -m src
# Dashboard: http://localhost:8000
```

### Docker Compose

```bash
docker compose up -d
open http://localhost:8000
```

啟動後包含：
- Mosquitto MQTT Broker（port 1883）
- MQTT 感測器模擬器
- Modbus PLC 模擬器（port 5020）
- Gateway + Dashboard（port 8000）

---

## 架構

```mermaid
graph TB
    Agent["AI Agent<br/>(Claude / OpenClaw)"] <-->|MCP| MCP["MCP Server"]
    MCP <--> Core
    Client["Dashboard / curl"] <-->|"REST API + WS"| Core

    subgraph Core["Gateway Core"]
        direction LR
        Registry["Device Registry"] --- EventBus["Event Bus"]
        EventBus --- RuleEngine["Rule Engine"]
    end

    subgraph Plugins["設備插件"]
        MQTT["MQTT"] --- Modbus["Modbus"]
        Modbus --- CoAP["CoAP"]
        CoAP --- Webhook["Webhook"]
    end

    subgraph Actions["告警動作"]
        TG["Telegram"] --- WH["Webhook"]
        WH --- DW["設備控制"]
    end

    Core <--> Plugins
    RuleEngine --> Actions
    Plugins <--> Devices["IoT 設備"]
    Actions --> Notify["通知"]
```

---

## 設備描述檔（YAML）

在 `devices.yaml` 定義設備：

```yaml
plugins:
  mqtt_sensor:
    protocol: mqtt
    broker: localhost:1883
    devices:
      - id: factory_temp_01
        name: "廠區溫度感測器"
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
        name: "產線 PLC"
        registers:
          motor_speed: { address: 4, type: uint16, unit: "RPM", access: rw }
          temperature: { address: 0, type: float32, unit: "°C", access: ro }

  webhook_devices:
    protocol: webhook
    listen_path: /webhook
    devices:
      - id: env_sensor_01
        name: "環境感測器（廠商 A）"
        identity:
          field: "$.device_id"
          value: "ENV-001"
        fields:
          temperature: { path: "$.data.temp", unit: "°C", type: float }
```

---

## 告警規則（YAML）

在 `rules.yaml` 定義告警規則：

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
      - type: telegram
        message: "[ALERT]{device_name} temperature {value}°C"

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

規則支援：
- **Cooldown** — 防止告警風暴
- **跨設備聯動** — 感測器觸發 → 自動控制另一台設備
- **即時修改** — 透過 REST API 修改規則，不需重啟

---

## REST API

| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/api/devices` | 列出所有設備 |
| GET | `/api/devices/{id}/read` | 讀取設備數據 |
| POST | `/api/devices/{id}/write` | 控制設備 |
| GET | `/api/devices/{id}/status` | 設備連線狀態 |
| GET | `/api/rules` | 列出告警規則 |
| POST | `/api/rules` | 新增規則 |
| PUT | `/api/rules/{name}` | 修改規則 |
| DELETE | `/api/rules/{name}` | 刪除規則 |
| PATCH | `/api/rules/{name}/toggle` | 啟用/停用規則 |
| GET | `/api/alerts` | 告警歷史 |

---

## MCP Server

AI Agent 透過 MCP 操作設備：

| Tool | 說明 |
|------|------|
| `list_devices` | 列出所有設備及狀態 |
| `read_device` | 讀取設備數據 |
| `write_device` | 控制設備 |
| `device_status` | 檢查設備是否在線 |
| `list_rules` | 列出告警規則 |
| `list_alerts` | 查詢最近告警 |

---

## 專案結構

```
kc_iot_gateway/
├── src/
│   ├── gateway.py            # Core：啟動、Plugin 載入、Event Bus
│   ├── plugin_base.py        # DevicePlugin ABC
│   ├── registry.py           # Device Registry（in-memory 設備狀態）
│   ├── api.py                # REST API（FastAPI）
│   ├── mcp_server.py         # MCP Server（FastMCP）
│   ├── rules.py              # Rule Engine
│   ├── cooldown.py           # Cooldown Manager
│   ├── db.py                 # SQLite（規則 + 告警歷史）
│   ├── plugins/
│   │   ├── mqtt_plugin.py
│   │   ├── modbus_plugin.py
│   │   ├── coap_plugin.py
│   │   └── webhook_plugin.py
│   └── actions/
│       ├── telegram.py
│       ├── webhook.py
│       ├── device_write.py
│       └── console.py
├── static/
│   └── index.html            # Dashboard + Webhook Simulator
├── simulators/
│   ├── mqtt_simulator.py
│   └── modbus_simulator.py
├── ai_agent_skill/           # AI Agent CLI wrapper
├── tests/                    # 自動化測試
├── docs/
│   └── DESIGN.md             # 設計文件
├── devices.yaml
├── rules.yaml
├── docker-compose.yml
└── Dockerfile
```

---

## 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `GATEWAY_HOST` | `0.0.0.0` | Gateway 綁定位址 |
| `GATEWAY_PORT` | `8000` | Gateway 埠號 |
| `MQTT_BROKER` | `localhost` | MQTT Broker 位址 |
| `MQTT_PORT` | `1883` | MQTT Broker 埠號 |
| `TELEGRAM_BOT_TOKEN` | | Telegram Bot token（選填） |
| `TELEGRAM_CHAT_ID` | | Telegram Chat ID（選填） |

---


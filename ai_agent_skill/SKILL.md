---
name: iot-gateway
description: "Read and control IoT devices across multiple protocols (MQTT, Modbus, CoAP, Webhook) via a unified gateway."
version: 1.0.0
---

# IoT Gateway Control

You have access to an IoT Gateway that manages devices across multiple protocols.

## Available Commands

- `iot list` — List all connected devices
- `iot status <device>` — Check if a device is online
- `iot read <device> [field]` — Read device data
- `iot write <device> <field> <value>` — Control a device
- `iot alerts [severity]` — View recent alerts
- `iot rules` — List alert rules

## Examples

```
iot list
iot status factory_temp_01
iot read factory_temp_01 temperature
iot read plc_01
iot write plc_01 motor_speed 1500
iot write plc_01 pump_on true
iot alerts critical
iot rules
```

## Notes

- Device and field names are defined in `devices.yaml`
- Read-only fields cannot be written to
- The gateway supports MQTT, Modbus TCP, CoAP, and Webhook protocols

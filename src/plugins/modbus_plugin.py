"""
Modbus TCP Plugin — read/write holding registers, input registers, coils
"""

import struct
import asyncio
import logging
from typing import Callable

from pymodbus.client import AsyncModbusTcpClient
from pymodbus import FramerType

from ..plugin_base import DevicePlugin

log = logging.getLogger("plugin.modbus")

TYPE_REG_COUNT = {"bool": 1, "uint16": 1, "int16": 1, "uint32": 2, "int32": 2, "float32": 2}


class ModbusPlugin(DevicePlugin):
    name = "modbus"
    protocol = "modbus"

    def __init__(self):
        self._config: dict = {}
        self._devices: dict[str, dict] = {}
        self._client: AsyncModbusTcpClient | None = None
        self._callback: Callable | None = None
        self._poll_task: asyncio.Task | None = None
        self._last_values: dict[str, dict] = {}

    async def connect(self, config: dict) -> bool:
        self._config = config
        host = config.get("host", "localhost")
        port = config.get("port", 502)

        for dev in config.get("devices", []):
            self._devices[dev["id"]] = dev

        self._client = AsyncModbusTcpClient(
            host=host, port=port, framer=FramerType.SOCKET, timeout=5
        )
        await self._client.connect()
        if not self._client.connected:
            log.error(f"Modbus connection failed: {host}:{port}")
            return False

        log.info(f"Modbus connected: {host}:{port}, {len(self._devices)} devices")
        return True

    async def read(self, device_id: str, params: dict | None = None) -> dict:
        dev = self._devices.get(device_id)
        if not dev:
            raise ValueError(f"Device {device_id} not found")

        slave_id = self._config.get("slave_id", 1)
        byte_order = self._config.get("byte_order", "big")
        result = {}

        for reg_name, reg_cfg in dev.get("registers", {}).items():
            address = reg_cfg["address"]
            data_type = reg_cfg.get("type", "uint16")
            fc = reg_cfg.get("fc", 3)
            count = TYPE_REG_COUNT.get(data_type, 1)

            try:
                if fc == 1:
                    rr = await self._client.read_coils(address, count=count, device_id=slave_id)
                    raw = rr.bits[:count]
                elif fc == 4:
                    rr = await self._client.read_input_registers(address, count=count, device_id=slave_id)
                    raw = rr.registers[:count]
                else:
                    rr = await self._client.read_holding_registers(address, count=count, device_id=slave_id)
                    raw = rr.registers[:count]

                if rr.isError():
                    continue

                result[reg_name] = self._convert_value(raw, data_type, byte_order)
            except Exception as e:
                log.error(f"Modbus read error ({device_id}.{reg_name}): {e}")

        self._last_values[device_id] = result
        return result

    async def write(self, device_id: str, params: dict) -> dict:
        dev = self._devices.get(device_id)
        if not dev:
            raise ValueError(f"Device {device_id} not found")

        slave_id = self._config.get("slave_id", 1)
        byte_order = self._config.get("byte_order", "big")
        written = {}

        for reg_name, value in params.items():
            reg_cfg = dev.get("registers", {}).get(reg_name)
            if not reg_cfg:
                continue
            if reg_cfg.get("access", "ro") != "rw":
                continue

            address = reg_cfg["address"]
            data_type = reg_cfg.get("type", "uint16")
            fc = reg_cfg.get("fc", 3)

            try:
                if fc == 1:
                    await self._client.write_coil(address, bool(value), device_id=slave_id)
                else:
                    regs = self._value_to_registers(value, data_type, byte_order)
                    if len(regs) == 1:
                        await self._client.write_register(address, regs[0], device_id=slave_id)
                    else:
                        await self._client.write_registers(address, regs, device_id=slave_id)
                written[reg_name] = value
            except Exception as e:
                log.error(f"Modbus write error ({device_id}.{reg_name}): {e}")

        return {"status": "ok", "written": written}

    async def start_listening(self, callback: Callable) -> None:
        self._callback = callback
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop_listening(self) -> None:
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

    async def disconnect(self) -> None:
        await self.stop_listening()
        if self._client:
            self._client.close()

    async def _poll_loop(self) -> None:
        while True:
            try:
                for device_id in self._devices:
                    data = await self.read(device_id)
                    if data and self._callback:
                        await self._callback(device_id, data)
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.error(f"Modbus poll error: {e}")
                await asyncio.sleep(5)

    def _convert_value(self, raw, data_type: str, byte_order: str = "big"):
        if data_type == "bool":
            return bool(raw[0])
        if data_type == "uint16":
            return raw[0]
        if data_type == "int16":
            v = raw[0]
            return v if v < 0x8000 else v - 0x10000

        if data_type in ("uint32", "int32", "float32"):
            high, low = raw[0], raw[1]
            if byte_order == "little":
                high, low = low, high
            raw_bytes = struct.pack(">HH", high, low)
            if data_type == "uint32":
                return struct.unpack(">I", raw_bytes)[0]
            elif data_type == "int32":
                return struct.unpack(">i", raw_bytes)[0]
            elif data_type == "float32":
                return round(struct.unpack(">f", raw_bytes)[0], 2)

        return raw[0]

    def _value_to_registers(self, value, data_type: str, byte_order: str = "big") -> list[int]:
        if data_type == "uint16":
            return [int(value) & 0xFFFF]
        if data_type == "int16":
            v = int(value)
            if v < 0:
                v += 0x10000
            return [v & 0xFFFF]
        if data_type in ("uint32", "int32", "float32"):
            if data_type == "uint32":
                raw_bytes = struct.pack(">I", int(value))
            elif data_type == "int32":
                raw_bytes = struct.pack(">i", int(value))
            else:
                raw_bytes = struct.pack(">f", float(value))
            high = int.from_bytes(raw_bytes[0:2], "big")
            low = int.from_bytes(raw_bytes[2:4], "big")
            if byte_order == "little":
                return [low, high]
            return [high, low]
        return [int(value)]

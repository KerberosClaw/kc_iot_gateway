"""
Modbus TCP 模擬器 — 溫度正弦波、濕度隨機、馬達/幫浦保持寫入值
"""

import asyncio
import math
import random
import struct
import time
import os
import logging

from pymodbus.datastore import (
    ModbusServerContext,
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
)
from pymodbus.server import StartAsyncTcpServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("modbus-simulator")

HOST = os.getenv("SIMULATOR_HOST", "0.0.0.0")
PORT = int(os.getenv("SIMULATOR_PORT", "5020"))
UPDATE_INTERVAL = 2


def float32_to_registers(value: float) -> list[int]:
    packed = struct.pack(">f", value)
    high = int.from_bytes(packed[0:2], "big")
    low = int.from_bytes(packed[2:4], "big")
    return [high, low]


def build_datastore() -> ModbusDeviceContext:
    hr_values = float32_to_registers(25.0) + float32_to_registers(50.0) + [0] + [0] * 10
    ir_values = [1000] + [0] * 9
    coil_values = [False, False] + [False] * 8
    di_values = [False] * 10

    return ModbusDeviceContext(
        di=ModbusSequentialDataBlock(0, di_values),
        co=ModbusSequentialDataBlock(0, coil_values),
        hr=ModbusSequentialDataBlock(0, hr_values),
        ir=ModbusSequentialDataBlock(0, ir_values),
    )


async def update_simulated_data(context: ModbusServerContext):
    start_time = time.time()
    while True:
        await asyncio.sleep(UPDATE_INTERVAL)
        elapsed = time.time() - start_time
        store = context[1]

        temp = 25.0 + 5.0 * math.sin(elapsed * 0.1)
        store.setValues(3, 0, float32_to_registers(temp))

        humidity = 50.0 + 10.0 * math.sin(elapsed * 0.07) + random.uniform(-2, 2)
        humidity = max(0.0, min(100.0, humidity))
        store.setValues(3, 2, float32_to_registers(humidity))

        log.info(f"Updated: temp={temp:.1f}°C, humidity={humidity:.1f}%RH")


async def run_server():
    store = build_datastore()
    context = ModbusServerContext(devices={1: store}, single=False)

    log.info(f"Modbus TCP Simulator on {HOST}:{PORT}")
    updater = asyncio.create_task(update_simulated_data(context))

    try:
        await StartAsyncTcpServer(context=context, address=(HOST, PORT))
    finally:
        updater.cancel()


if __name__ == "__main__":
    asyncio.run(run_server())

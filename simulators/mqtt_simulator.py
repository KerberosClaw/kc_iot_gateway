"""
MQTT 感測器模擬器 — 每 2 秒發布溫濕度 JSON
"""

import asyncio
import json
import math
import random
import time
import os
import logging

import aiomqtt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("mqtt-simulator")

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = "factory/sensor/temp_01"
INTERVAL = 2


async def run():
    start_time = time.time()

    while True:
        try:
            async with aiomqtt.Client(BROKER, PORT) as client:
                log.info(f"Connected to MQTT broker {BROKER}:{PORT}")
                while True:
                    elapsed = time.time() - start_time
                    temp = 25.0 + 5.0 * math.sin(elapsed * 0.1) + random.uniform(-0.5, 0.5)
                    hum = 50.0 + 10.0 * math.sin(elapsed * 0.07) + random.uniform(-2, 2)

                    payload = json.dumps({
                        "temp": round(temp, 2),
                        "hum": round(max(0, min(100, hum)), 2),
                    })

                    await client.publish(TOPIC, payload)
                    log.info(f"Published: {TOPIC} → {payload}")
                    await asyncio.sleep(INTERVAL)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.error(f"MQTT error: {e}, reconnecting in 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run())

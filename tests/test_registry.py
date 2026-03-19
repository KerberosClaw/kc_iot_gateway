"""Device Registry 單元測試"""

import time
import pytest
from src.registry import DeviceRegistry


class TestDeviceRegistry:
    def setup_method(self):
        self.reg = DeviceRegistry()
        self.reg.register("dev1", "Test Device", "mqtt", "mqtt_sensor", {})

    def test_register(self):
        assert self.reg.get("dev1") is not None
        assert self.reg.get("dev1").name == "Test Device"

    def test_update(self):
        self.reg.update("dev1", {"temp": 25.0})
        state = self.reg.get("dev1")
        assert state.fields["temp"] == 25.0
        assert state.last_update > 0

    def test_get_all(self):
        self.reg.register("dev2", "Second", "modbus", "modbus_plc", {})
        assert len(self.reg.get_all()) == 2

    def test_is_online(self):
        assert not self.reg.is_online("dev1")
        self.reg.update("dev1", {"temp": 25.0})
        assert self.reg.is_online("dev1")

    def test_is_online_timeout(self):
        self.reg.update("dev1", {"temp": 25.0})
        state = self.reg.get("dev1")
        state.last_update = time.time() - 400
        assert not self.reg.is_online("dev1")

    def test_to_dict(self):
        self.reg.update("dev1", {"temp": 25.0, "hum": 60.0})
        d = self.reg.to_dict("dev1")
        assert d["device_id"] == "dev1"
        assert d["protocol"] == "mqtt"
        assert d["fields"]["temp"] == 25.0

    def test_unknown_device(self):
        assert self.reg.get("nonexistent") is None
        assert self.reg.to_dict("nonexistent") is None

    def test_get_plugin_name(self):
        assert self.reg.get_plugin_name("dev1") == "mqtt_sensor"
        assert self.reg.get_plugin_name("nonexistent") is None

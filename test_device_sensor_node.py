import importlib
import sys
import types
import unittest
from unittest.mock import patch


class FakePin:
    IN = 0

    def __init__(self, pin_number, mode):
        self.pin_number = pin_number
        self.mode = mode

    def value(self):
        return 1


class FakeADC:
    ATTN_11DB = 3

    def __init__(self, pin):
        self.pin = pin
        self.attenuation = None

    def atten(self, attenuation):
        self.attenuation = attenuation

    def read(self):
        return 2048


class SidecarPhysicalNodeTests(unittest.TestCase):
    def setUp(self):
        fake_machine = types.SimpleNamespace(Pin=FakePin, ADC=FakeADC)
        with patch.dict(sys.modules, {"machine": fake_machine}):
            self.node_module = importlib.import_module("device_sensor_node")
        self.addCleanup(sys.modules.pop, "device_sensor_node", None)

    def test_samples_magnetic_and_optical_inputs(self):
        node = self.node_module.SidecarPhysicalNode()

        with patch.object(self.node_module.time, "time", return_value=1234):
            telemetry = node.sample_physical_telemetry()

        self.assertEqual(
            telemetry,
            {
                "timestamp": 1234,
                "power_relay_active": True,
                "status_light_intensity": 2048,
            },
        )
        self.assertEqual(node.mag_sensor.pin_number, 34)
        self.assertEqual(node.opt_sensor.pin.pin_number, 35)
        self.assertEqual(node.opt_sensor.attenuation, FakeADC.ATTN_11DB)

    def test_tap_handler_returns_sampled_telemetry(self):
        node = self.node_module.SidecarPhysicalNode()

        with patch.object(
            node, "sample_physical_telemetry", return_value={"timestamp": 1}
        ), patch("builtins.print"):
            telemetry = node.handle_nfc_tap_event()

        self.assertEqual(telemetry, {"timestamp": 1})


if __name__ == "__main__":
    unittest.main()

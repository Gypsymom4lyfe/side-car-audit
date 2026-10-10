"""MicroPython sensor-node scaffold for an ESP32-based sidecar."""

import machine
import time


class SidecarPhysicalNode:
    def __init__(self, magnetic_pin=34, optical_pin=35):
        self.mag_sensor = machine.Pin(magnetic_pin, machine.Pin.IN)
        self.opt_sensor = machine.ADC(machine.Pin(optical_pin))
        self.opt_sensor.atten(machine.ADC.ATTN_11DB)

    def sample_physical_telemetry(self):
        """Capture a snapshot of the magnetic and optical sensor inputs."""
        mag_state = self.mag_sensor.value()
        opt_level = self.opt_sensor.read()

        return {
            "timestamp": time.time(),
            "power_relay_active": bool(mag_state),
            "status_light_intensity": opt_level,
        }

    def handle_nfc_tap_event(self):
        """Sample telemetry when called by an NFC integration or test harness."""
        print("[*] Smart card NFC tap detected. Compiling physical audit state...")
        current_state = self.sample_physical_telemetry()
        print(f"[+] Physical telemetry logged: {current_state}")
        return current_state


if __name__ == "__main__":
    node = SidecarPhysicalNode()
    print("Sovereign Sidecar physical node online and listening passively.")

    for _ in range(2):
        time.sleep(1)
        node.handle_nfc_tap_event()

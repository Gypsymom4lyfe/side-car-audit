import json
import uuid

from receipt_logger import AuditReceiptLogger


class SidecarEngine:
    def __init__(self, baseline_config_path: str):
        self.logger = AuditReceiptLogger()
        self.baseline = self._load_baseline(baseline_config_path)

    def _load_baseline(self, path: str) -> dict:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"CRITICAL: Baseline configuration file '{path}' is missing. "
                "Silent fallback prohibited."
            ) from e

    def inspect_stream_packet(self, live_packet: dict):
        anomalies = []
        expected_schema = self.baseline.get("expected_schema", {})
        type_mapping = {
            "integer": int,
            "string": str,
            "float": float,
            "boolean": bool,
        }

        for key, expected_type_str in expected_schema.items():
            if key not in live_packet:
                anomalies.append(f"Missing mandatory baseline key: {key}")
                continue

            expected_type = type_mapping.get(expected_type_str)
            if expected_type and type(live_packet[key]) is not expected_type:
                anomalies.append(
                    f"Type mismatch for key '{key}': expected {expected_type_str}, "
                    f"got {type(live_packet[key]).__name__}"
                )

        value = live_packet.get("value")
        if value is not None:
            min_val, max_val = self.baseline.get("allowed_range", [0, 0])
            if not (min_val <= value <= max_val):
                anomalies.append(
                    f"Value drift detected: {value} outside allowed bounds [{min_val}, {max_val}]"
                )

        event_nonce = str(uuid.uuid4())

        if anomalies:
            receipt = self.logger.create_receipt(
                "DIVERGENCE_DETECTED",
                {"anomalies": anomalies, "packet": live_packet},
                nonce=event_nonce,
            )
            print(f"[!] DIVERGENCE CAUGHT. Receipt Hash: {receipt['current_receipt_hash']}")
            return False

        receipt = self.logger.create_receipt(
            "CLEAN",
            {"packet_id": live_packet.get("id", "unknown")},
            nonce=event_nonce,
        )
        print(f"[+] Stream verified clean. Receipt Hash: {receipt['current_receipt_hash']}")
        return True

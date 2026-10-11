import json

from receipt_logger import AuditReceiptLogger


class SidecarEngine:
    def __init__(self, baseline_config_path: str):
        self.logger = AuditReceiptLogger()
        self.baseline = self._load_baseline(baseline_config_path)

    def _load_baseline(self, path: str) -> dict:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"expected_schema": {"id": int, "status": str}, "allowed_range": [0, 100]}

    def inspect_stream_packet(self, live_packet: dict):
        anomalies = []
        for key in self.baseline.get("expected_schema", {}):
            if key not in live_packet:
                anomalies.append(f"Missing mandatory baseline key: {key}")

        value = live_packet.get("value")
        if value is not None:
            min_val, max_val = self.baseline.get("allowed_range", [0, 0])
            if not (min_val <= value <= max_val):
                anomalies.append(
                    f"Value drift detected: {value} outside allowed bounds [{min_val}, {max_val}]"
                )

        if anomalies:
            receipt = self.logger.create_receipt(
                "DIVERGENCE_DETECTED",
                {"anomalies": anomalies, "packet": live_packet},
            )
            print(f"[!] DIVERGENCE CAUGHT. Receipt Hash: {receipt['current_receipt_hash']}")
            return False

        receipt = self.logger.create_receipt(
            "CLEAN",
            {"packet_id": live_packet.get("id", "unknown")},
        )
        print(f"[+] Stream verified clean. Receipt Hash: {receipt['current_receipt_hash']}")
        return True

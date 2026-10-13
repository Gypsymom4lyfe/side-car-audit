import json
import math
import uuid

from receipt_logger import AuditReceiptLogger


class SidecarEngine:
    def __init__(self, baseline_config_path: str):
        self.baseline = self._load_baseline(baseline_config_path)
        self.logger = AuditReceiptLogger()

    def _load_baseline(self, path: str) -> dict:
        try:
            with open(path, "r") as f:
                baseline = json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"CRITICAL: Baseline configuration file '{path}' is missing. "
                "Silent fallback prohibited."
            ) from e
        self._validate_baseline(baseline)
        return baseline

    @staticmethod
    def _validate_baseline(baseline: dict):
        if not isinstance(baseline, dict):
            raise ValueError("Baseline configuration must be a JSON object.")

        expected_schema = baseline.get("expected_schema")
        if not isinstance(expected_schema, dict):
            raise ValueError("Baseline 'expected_schema' must be a JSON object.")

        supported_types = {"integer", "string", "float", "boolean"}
        for key, type_name in expected_schema.items():
            if not isinstance(key, str) or not key:
                raise ValueError("Baseline schema keys must be non-empty strings.")
            if not isinstance(type_name, str) or type_name not in supported_types:
                raise ValueError(
                    f"Unsupported baseline type {type_name!r} for key {key!r}."
                )

        allowed_range = baseline.get("allowed_range")
        if (
            not isinstance(allowed_range, list)
            or len(allowed_range) != 2
            or any(
                isinstance(bound, bool)
                or not isinstance(bound, (int, float))
                or (isinstance(bound, float) and not math.isfinite(bound))
                for bound in allowed_range
            )
        ):
            raise ValueError(
                "Baseline 'allowed_range' must contain two finite numeric bounds."
            )
        if allowed_range[0] > allowed_range[1]:
            raise ValueError(
                "Baseline 'allowed_range' lower bound must not exceed upper bound."
            )

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

        if "value" in live_packet:
            value = live_packet["value"]
            min_val, max_val = self.baseline.get("allowed_range", [0, 0])
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or (isinstance(value, float) and not math.isfinite(value))
            ):
                anomalies.append("Value must be a finite number.")
            elif not (min_val <= value <= max_val):
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

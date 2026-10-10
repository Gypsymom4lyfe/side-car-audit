import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from receipt_logger import AuditReceiptLogger
from sidecar_engine import SidecarEngine


class SidecarEngineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.baseline_path = Path(self.directory.name) / "baseline.json"
        self.log_path = Path(self.directory.name) / "receipts.jsonl"
        self.baseline_path.write_text(
            json.dumps(
                {
                    "expected_schema": {"id": "integer", "status": "string"},
                    "allowed_range": [0, 100],
                }
            ),
            encoding="utf-8",
        )

    def create_engine(self):
        with patch(
            "sidecar_engine.AuditReceiptLogger",
            return_value=AuditReceiptLogger(self.log_path),
        ):
            return SidecarEngine(str(self.baseline_path))

    def test_clean_packet_writes_clean_receipt(self):
        engine = self.create_engine()

        with patch("builtins.print"):
            result = engine.inspect_stream_packet(
                {"id": 10, "status": "ok", "value": 42}
            )

        self.assertTrue(result)
        receipt = json.loads(self.log_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "CLEAN")
        self.assertEqual(receipt["divergence_details"], {"packet_id": 10})

    def test_missing_key_and_out_of_range_value_write_divergence(self):
        engine = self.create_engine()

        with patch("builtins.print"):
            result = engine.inspect_stream_packet({"id": 10, "value": 101})

        self.assertFalse(result)
        receipt = json.loads(self.log_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "DIVERGENCE_DETECTED")
        self.assertEqual(
            receipt["divergence_details"]["anomalies"],
            [
                "Missing mandatory baseline key: status",
                "Value drift detected: 101 outside allowed bounds [0, 100]",
            ],
        )

    def test_missing_baseline_uses_fallback_config(self):
        missing_path = Path(self.directory.name) / "missing.json"
        with patch(
            "sidecar_engine.AuditReceiptLogger",
            return_value=AuditReceiptLogger(self.log_path),
        ):
            engine = SidecarEngine(str(missing_path))

        self.assertEqual(
            engine.baseline,
            {"expected_schema": {"id": int, "status": str}, "allowed_range": [0, 100]},
        )


if __name__ == "__main__":
    unittest.main()

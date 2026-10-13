import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sidecar_engine import SidecarEngine


class SidecarEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.baseline_path = Path(self.temp_dir.name) / "baseline.json"
        self.baseline = {
            "expected_schema": {"id": "integer", "status": "string"},
            "allowed_range": [0, 100],
        }
        self.write_baseline(self.baseline)
        self.logger_patcher = patch("sidecar_engine.AuditReceiptLogger")
        self.mock_logger_class = self.logger_patcher.start()
        self.addCleanup(self.logger_patcher.stop)
        self.mock_logger_class.return_value.create_receipt.return_value = {
            "current_receipt_hash": "test-hash"
        }

    def write_baseline(self, baseline):
        self.baseline_path.write_text(json.dumps(baseline))

    def create_engine(self):
        return SidecarEngine(str(self.baseline_path))

    def test_unsupported_schema_type_fails_initialization(self):
        self.baseline["expected_schema"]["id"] = "decimal"
        self.write_baseline(self.baseline)

        with self.assertRaisesRegex(ValueError, "Unsupported baseline type"):
            self.create_engine()

    def test_unhashable_schema_type_fails_as_configuration_error(self):
        self.baseline["expected_schema"]["id"] = []
        self.write_baseline(self.baseline)

        with self.assertRaisesRegex(ValueError, "Unsupported baseline type"):
            self.create_engine()

    def test_invalid_ranges_fail_initialization(self):
        for invalid_range in ([0], [10, 0], [0, math.inf], [False, 100]):
            with self.subTest(invalid_range=invalid_range):
                self.baseline["allowed_range"] = invalid_range
                self.write_baseline(self.baseline)
                with self.assertRaises(ValueError):
                    self.create_engine()

    def test_non_numeric_and_non_finite_values_are_divergences(self):
        engine = self.create_engine()
        packet = {"id": 1, "status": "ok"}

        for value in ("45", True, None, math.nan, math.inf):
            with self.subTest(value=value):
                packet["value"] = value
                self.assertFalse(engine.inspect_stream_packet(packet))

    def test_valid_packet_passes_and_out_of_range_packet_fails(self):
        engine = self.create_engine()
        clean_packet = {"id": 1, "status": "ok", "value": 100}
        drift_packet = {"id": 2, "status": "ok", "value": 101}

        self.assertTrue(engine.inspect_stream_packet(clean_packet))
        self.assertFalse(engine.inspect_stream_packet(drift_packet))

    def test_missing_baseline_fails_instead_of_falling_back(self):
        missing_path = Path(self.temp_dir.name) / "missing.json"

        with self.assertRaisesRegex(FileNotFoundError, "Silent fallback prohibited"):
            SidecarEngine(str(missing_path))


if __name__ == "__main__":
    unittest.main()

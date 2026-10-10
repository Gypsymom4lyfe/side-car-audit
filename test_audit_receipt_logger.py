import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from audit_receipt_logger import AuditReceiptLogger, GENESIS_HASH


class AuditReceiptLoggerTests(unittest.TestCase):
    def test_first_receipt_uses_genesis_hash_and_is_hashable(self):
        with tempfile.TemporaryDirectory() as directory:
            log_file = Path(directory) / "receipts.jsonl"
            logger = AuditReceiptLogger(log_file)

            receipt = logger.create_receipt("CLEAN", {})

            self.assertEqual(receipt["previous_receipt_hash"], GENESIS_HASH)
            payload = {key: value for key, value in receipt.items() if key != "current_receipt_hash"}
            expected_hash = hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode("utf-8")
            ).hexdigest()
            self.assertEqual(receipt["current_receipt_hash"], expected_hash)

    def test_receipts_chain_across_calls_and_logger_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            log_file = Path(directory) / "receipts.jsonl"
            first_logger = AuditReceiptLogger(log_file)
            first = first_logger.create_receipt("CLEAN", {})
            second = first_logger.create_receipt("DIVERGENCE_DETECTED", {"field": "value"})

            self.assertEqual(second["previous_receipt_hash"], first["current_receipt_hash"])

            resumed_logger = AuditReceiptLogger(log_file)
            third = resumed_logger.create_receipt("CLEAN", {})
            self.assertEqual(third["previous_receipt_hash"], second["current_receipt_hash"])

            with log_file.open(encoding="utf-8") as log:
                stored_receipts = [json.loads(line) for line in log]
            self.assertEqual(len(stored_receipts), 3)
            self.assertEqual(stored_receipts[-1], third)


if __name__ == "__main__":
    unittest.main()

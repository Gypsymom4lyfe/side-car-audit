import hashlib
import json
import time
import uuid


class AuditReceiptLogger:
    def __init__(self, log_file="audit_chain.jsonl"):
        self.log_file = log_file
        self.last_hash = self._get_last_hash()

    def _get_last_hash(self):
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1].strip())
                    return last_entry.get("current_receipt_hash")
        except FileNotFoundError:
            pass
        return hashlib.sha256(b"SOVEREIGN_SIDECAR_GENESIS_ROOT").hexdigest()

    def create_receipt(self, status: str, divergence_details: dict):
        timestamp = time.time()
        nonce = str(uuid.uuid4())

        receipt_data = {
            "timestamp": timestamp,
            "nonce": nonce,
            "status": status,
            "divergence_details": divergence_details,
            "previous_receipt_hash": self.last_hash,
        }

        payload_string = json.dumps(receipt_data, sort_keys=True)
        current_hash = hashlib.sha256(payload_string.encode("utf-8")).hexdigest()

        complete_receipt = {
            **receipt_data,
            "current_receipt_hash": current_hash,
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(complete_receipt) + "\n")

        self.last_hash = current_hash
        return complete_receipt

import hashlib
import json
import time
import uuid


GENESIS_HASH = hashlib.sha256(b"SOVEREIGN_SIDECAR_GENESIS_ROOT").hexdigest()


class AuditReceiptLogger:
    def __init__(self, log_file="audit_chain.jsonl"):
        self.log_file = log_file
        self.last_hash = self._get_last_hash()

    def _get_last_hash(self):
        """Return the last receipt hash, or the genesis hash for an empty log."""
        try:
            with open(self.log_file, "r", encoding="utf-8") as log:
                last_line = None
                for line in log:
                    if line.strip():
                        last_line = line
                if last_line is not None:
                    last_entry = json.loads(last_line)
                    return last_entry["current_receipt_hash"]
        except FileNotFoundError:
            pass

        return GENESIS_HASH

    def create_receipt(self, status: str, divergence_details: dict):
        """Create and append a hash-chained audit receipt."""
        receipt_data = {
            "timestamp": time.time(),
            "nonce": str(uuid.uuid4()),
            "status": status,
            "divergence_details": divergence_details,
            "previous_receipt_hash": self.last_hash,
        }
        payload = json.dumps(receipt_data, sort_keys=True)
        current_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        complete_receipt = {
            **receipt_data,
            "current_receipt_hash": current_hash,
        }

        with open(self.log_file, "a", encoding="utf-8") as log:
            log.write(json.dumps(complete_receipt) + "\n")

        self.last_hash = current_hash
        return complete_receipt

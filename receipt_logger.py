import hashlib
import json
import os
import time


class AuditReceiptLogger:
    def __init__(self, log_file="audit_chain.jsonl"):
        self.log_file = log_file
        self.seen_nonces = set()
        self.last_hash = self._verify_and_get_last_hash()

    def _verify_and_get_last_hash(self):
        """Validate the complete receipt chain before accepting new entries."""
        genesis_hash = hashlib.sha256(b"SOVEREIGN_SIDECAR_GENESIS_ROOT").hexdigest()

        if not os.path.exists(self.log_file):
            return genesis_hash

        expected_previous_hash = genesis_hash
        try:
            with open(self.log_file, "r") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    entry = json.loads(line.strip())

                    if entry.get("previous_receipt_hash") != expected_previous_hash:
                        raise ValueError(
                            f"CRITICAL: Cryptographic chain broken at line {line_num}! "
                            "Log has been tampered with."
                        )

                    current_stored_hash = entry.get("current_receipt_hash")
                    payload = {
                        key: value
                        for key, value in entry.items()
                        if key != "current_receipt_hash"
                    }
                    payload_string = json.dumps(payload, sort_keys=True)
                    recomputed_hash = hashlib.sha256(
                        payload_string.encode("utf-8")
                    ).hexdigest()

                    if current_stored_hash != recomputed_hash:
                        raise ValueError(
                            f"CRITICAL: Hash mismatch at line {line_num}! "
                            "Payload was modified."
                        )

                    nonce = entry.get("nonce")
                    if not isinstance(nonce, str) or not nonce:
                        raise ValueError(
                            f"CRITICAL: Invalid nonce at line {line_num}."
                        )
                    if nonce in self.seen_nonces:
                        raise ValueError(
                            f"CRITICAL: Duplicate nonce at line {line_num}."
                        )
                    self.seen_nonces.add(nonce)
                    expected_previous_hash = current_stored_hash

            return expected_previous_hash
        except Exception as e:
            raise RuntimeError(f"Audit chain verification failed: {e}") from e

    def create_receipt(self, status: str, divergence_details: dict, nonce: str):
        """Create a receipt after rejecting previously used nonces."""
        if not isinstance(nonce, str) or not nonce:
            raise ValueError("Nonce must be a non-empty string.")
        if nonce in self.seen_nonces:
            raise ValueError(
                "SECURITY ALERT: Replay attack detected! Nonce has already been processed."
            )

        receipt_data = {
            "timestamp": time.time(),
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

        self.seen_nonces.add(nonce)
        self.last_hash = current_hash
        return complete_receipt

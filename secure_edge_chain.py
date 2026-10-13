import hashlib
import json
import time
from typing import Any, Dict, Optional


class SecureEdgeBlock:
    def __init__(
        self,
        index: int,
        previous_hash: str,
        data: Dict[str, Any],
        is_anomaly: bool = False,
    ):
        self.index = index
        self.timestamp = time.time()
        self.previous_hash = previous_hash
        self.data = data
        self.is_anomaly = is_anomaly
        self.hash = self.compute_hash()
        self.signature: Optional[str] = None

    def compute_hash(self) -> str:
        block_content = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "data": self.data,
            "is_anomaly": self.is_anomaly,
        }
        block_string = json.dumps(block_content, sort_keys=True)
        return hashlib.sha256(block_string.encode("utf-8")).hexdigest()

    def sign_block(self, private_key_simulated: str):
        """Create a test-only placeholder, not a cryptographic signature."""
        sig_payload = f"{self.hash}:{private_key_simulated}"
        self.signature = hashlib.sha256(sig_payload.encode("utf-8")).hexdigest()


class ResilientHashChain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self) -> SecureEdgeBlock:
        return SecureEdgeBlock(
            index=0,
            previous_hash="0" * 64,
            data={"status": "genesis_anchor"},
        )

    def append_entry(
        self, raw_input: Any, expected_schema: Dict[str, type]
    ) -> SecureEdgeBlock:
        previous_block = self.chain[-1]

        try:
            validated_data = {}
            for key, expected_type in expected_schema.items():
                if key not in raw_input:
                    raise KeyError(f"Missing required key: {key}")

                value = raw_input[key]
                if not isinstance(value, expected_type):
                    try:
                        value = expected_type(value)
                    except (ValueError, TypeError) as error:
                        raise TypeError(
                            f"Malformed value for {key}: expected "
                            f"{expected_type.__name__}"
                        ) from error

                validated_data[key] = value

            new_block = SecureEdgeBlock(
                index=len(self.chain),
                previous_hash=previous_block.hash,
                data=validated_data,
                is_anomaly=False,
            )
        except (KeyError, TypeError, ValueError) as error:
            anomaly_payload = {
                "raw_input": str(raw_input),
                "error_reason": str(error),
            }
            new_block = SecureEdgeBlock(
                index=len(self.chain),
                previous_hash=previous_block.hash,
                data=anomaly_payload,
                is_anomaly=True,
            )

        new_block.sign_block("node_private_key_placeholder")
        self.chain.append(new_block)
        return new_block

    def verify_chain(self) -> bool:
        if not self.chain:
            return False

        genesis = self.chain[0]
        if (
            genesis.index != 0
            or genesis.previous_hash != "0" * 64
            or genesis.hash != genesis.compute_hash()
        ):
            return False

        for index, block in enumerate(self.chain[1:], start=1):
            previous_block = self.chain[index - 1]
            if (
                block.index != index
                or block.previous_hash != previous_block.hash
                or block.hash != block.compute_hash()
            ):
                return False
        return True

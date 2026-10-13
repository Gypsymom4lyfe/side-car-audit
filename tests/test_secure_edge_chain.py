import unittest

from secure_edge_chain import ResilientHashChain


class ResilientHashChainTests(unittest.TestCase):
    def test_genesis_and_valid_entry_form_a_valid_chain(self):
        chain = ResilientHashChain()

        block = chain.append_entry(
            {"id": 42, "status": "active"},
            {"id": int, "status": str},
        )

        self.assertEqual(block.index, 1)
        self.assertFalse(block.is_anomaly)
        self.assertEqual(block.previous_hash, chain.chain[0].hash)
        self.assertIsNotNone(block.signature)
        self.assertTrue(chain.verify_chain())

    def test_missing_or_malformed_data_is_recorded_as_an_anomaly(self):
        chain = ResilientHashChain()

        missing = chain.append_entry({"id": 1}, {"id": int, "status": str})
        malformed = chain.append_entry(
            {"id": "not-an-integer", "status": "active"},
            {"id": int, "status": str},
        )

        self.assertTrue(missing.is_anomaly)
        self.assertTrue(malformed.is_anomaly)
        self.assertIn("Missing required key", missing.data["error_reason"])
        self.assertIn("Malformed value", malformed.data["error_reason"])
        self.assertTrue(chain.verify_chain())

    def test_modified_block_invalidates_chain(self):
        chain = ResilientHashChain()
        block = chain.append_entry({"id": 1}, {"id": int})
        block.data["id"] = 2

        self.assertFalse(chain.verify_chain())


if __name__ == "__main__":
    unittest.main()

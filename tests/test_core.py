import tempfile
import unittest
from pathlib import Path

from prime_memory_folding import MemoryFolder, PrimeAddress, PrimeMemoryStore, cosine_similarity
from prime_memory_folding.mcp_server import PrimeMemoryMCPServer


class PrimeMemoryCoreTests(unittest.TestCase):
    def test_address_round_trip(self):
        address = PrimeAddress(domain=2, subdomain=3, concept=30, instance=42)
        packed = address.pack()
        unpacked = PrimeAddress.unpack(packed)
        self.assertEqual(unpacked, address)
        self.assertTrue(unpacked.has_all_tag_primes(6))

    def test_store_filters_by_domain_and_tags(self):
        store = PrimeMemoryStore()
        store.add("alpha", domain="project", tags=["code", "technical"], vector=[1, 0])
        store.add("beta", domain="decision", tags=["technical"], vector=[0, 1])

        project_results = store.query(domain="project")
        self.assertEqual(len(project_results), 1)
        self.assertEqual(project_results[0].content, "alpha")

        code_results = store.query(tags=["code"])
        self.assertEqual(len(code_results), 1)
        self.assertEqual(code_results[0].content, "alpha")

    def test_similarity(self):
        self.assertGreater(cosine_similarity([1, 0], [0.9, 0.1]), 0.9)
        self.assertEqual(cosine_similarity([], [1, 2]), 0.0)

    def test_folding_creates_folded_record(self):
        store = PrimeMemoryStore()
        store.add("first related memory", domain="memory", tags=["technical"], vector=[1.0, 0.0], importance=0.8)
        store.add("second related memory", domain="memory", tags=["technical"], vector=[0.95, 0.05], importance=0.7)

        result = MemoryFolder().fold_store(store)
        self.assertEqual(result.folded, 2)
        self.assertEqual(len(result.created), 1)
        self.assertIn("folded", result.created[0].tags)

    def test_json_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "store.json"
            store = PrimeMemoryStore()
            record = store.add("persist me", domain="session", tags=["important"], vector=[0.1, 0.2])
            store.save(path)

            loaded = PrimeMemoryStore.load(path)
            self.assertIsNotNone(loaded.get(record.record_id))
            self.assertEqual(loaded.get(record.record_id).content, "persist me")
            self.assertEqual(loaded.get(record.record_id).tag_product, record.tag_product)

    def test_mcp_tool_schema_properties(self):
        server = PrimeMemoryMCPServer()
        response = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        tools = response["result"]["tools"]
        by_name = {tool["name"]: tool for tool in tools}
        encode_props = by_name["prime_memory_encode"]["inputSchema"]["properties"]
        query_props = by_name["prime_memory_query"]["inputSchema"]["properties"]
        self.assertIn("instance_key", encode_props)
        self.assertIn("vector", query_props)
        self.assertIn("limit", query_props)


if __name__ == "__main__":
    unittest.main()

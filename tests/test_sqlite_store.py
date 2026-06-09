import json
import tempfile
import unittest
from pathlib import Path

from prime_memory_folding.address import U32_MAX
from prime_memory_folding.folding import MemoryFolder
from prime_memory_folding.primes import DEFAULT_TAG_PRIMES
from prime_memory_folding.sqlite_store import (
    export_sqlite_to_json,
    load_store_from_sqlite,
    migrate_json_to_sqlite,
    save_store_to_sqlite,
)
from prime_memory_folding.store import PrimeMemoryStore
from prime_memory_folding.system import PrimeMemorySystem


def _populated_store():
    store = PrimeMemoryStore()
    store.add("alpha", domain="project", tags=["technical", "code"], vector=[1.0, 0.0],
              importance=0.8, metadata={"k": "v"})
    store.add("beta", domain="decision", tags=["technical"], vector=[0.0, 1.0], importance=0.6)
    # Many tags + a novel tag -> tag_product > 2^32 and a packed address > 2^64.
    store.add("gamma", domain="memory", tags=list(DEFAULT_TAG_PRIMES.keys()) + ["novel_x"],
              importance=0.9)
    return store


class SqliteStoreTests(unittest.TestCase):
    def test_save_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "store.db"
            store = _populated_store()
            save_store_to_sqlite(store, db)
            loaded = load_store_from_sqlite(db)

            self.assertEqual(set(loaded.records.keys()), set(store.records.keys()))
            for record_id, record in store.records.items():
                restored = loaded.records[record_id]
                self.assertEqual(restored.address, record.address)
                self.assertEqual(restored.tag_product, record.tag_product)
                self.assertEqual(restored.tags, record.tags)
                self.assertEqual(restored.vector, record.vector)
                self.assertEqual(restored.metadata, record.metadata)
                self.assertEqual(restored.domain, record.domain)
            self.assertEqual(loaded.tag_registry.to_dict(), store.tag_registry.to_dict())

    def test_large_values_exceed_sqlite_integer(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "store.db"
            store = _populated_store()
            gamma = next(r for r in store.records.values() if r.content == "gamma")
            self.assertGreater(gamma.tag_product, U32_MAX)
            self.assertGreater(gamma.address, 1 << 64)  # would overflow a SQLite INTEGER
            save_store_to_sqlite(store, db)
            restored = load_store_from_sqlite(db).records[gamma.record_id]
            self.assertEqual(restored.tag_product, gamma.tag_product)
            self.assertEqual(restored.address, gamma.address)

    def test_query_and_fold_after_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "store.db"
            save_store_to_sqlite(_populated_store(), db)
            loaded = load_store_from_sqlite(db)
            self.assertGreaterEqual(len(loaded.query(tags=["technical"])), 2)
            self.assertEqual(len(loaded.query(domain="project")), 1)
            self.assertIsNotNone(MemoryFolder().fold_store(loaded))

    def test_json_sqlite_migration_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "store.json"
            db = Path(tmp) / "store.db"
            back = Path(tmp) / "back.json"
            _populated_store().save(json_path)
            migrate_json_to_sqlite(json_path, db)
            export_sqlite_to_json(db, back)

            original = json.loads(json_path.read_text())
            roundtripped = json.loads(back.read_text())
            self.assertEqual(
                {r["record_id"] for r in original["records"]},
                {r["record_id"] for r in roundtripped["records"]},
            )
            self.assertEqual(original["tag_primes"], roundtripped["tag_primes"])

    def test_load_missing_sqlite_returns_empty_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            loaded = load_store_from_sqlite(Path(tmp) / "absent.db")
            self.assertEqual(len(loaded.records), 0)

    def test_system_sqlite_backend_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "system.db"
            system = PrimeMemorySystem(db)
            self.assertEqual(system.backend, "sqlite")
            system.remember("persist me", domain="session", tags=["important"], vector=[0.1, 0.2])

            reopened = PrimeMemorySystem(db)
            self.assertEqual(reopened.backend, "sqlite")
            self.assertGreaterEqual(len(reopened.recall(tags=["important"])), 1)

    def test_system_defaults_to_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "store.json"
            system = PrimeMemorySystem(json_path)
            self.assertEqual(system.backend, "json")
            system.remember("x", tags=["technical"])
            self.assertTrue(json_path.exists())

    def test_unknown_backend_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                PrimeMemorySystem(Path(tmp) / "store.db", backend="bogus")
            # A typo on a .db path must not silently fall through to JSON content.
            with self.assertRaises(ValueError):
                PrimeMemorySystem(Path(tmp) / "store.db", backend="sqllite")

    def test_backend_override_is_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            system = PrimeMemorySystem(Path(tmp) / "store.json", backend="SQLite")
            self.assertEqual(system.backend, "sqlite")


if __name__ == "__main__":
    unittest.main()

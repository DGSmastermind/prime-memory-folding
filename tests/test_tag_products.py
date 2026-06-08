import json
import random
import tempfile
import unittest
from pathlib import Path

from prime_memory_folding.primes import DEFAULT_TAG_PRIMES
from prime_memory_folding.address import U32_MAX
from prime_memory_folding.store import PrimeMemoryStore


class TagProductTests(unittest.TestCase):
    def test_many_default_and_novel_tags_do_not_overflow_address(self):
        store = PrimeMemoryStore()
        tags = list(DEFAULT_TAG_PRIMES.keys()) + [
            "novel_alpha",
            "novel_beta",
            "novel_gamma",
            "novel_delta",
            "novel_epsilon",
        ]

        record = store.add("many-tag memory", tags=tags)

        self.assertGreater(record.tag_product, U32_MAX)
        self.assertEqual(len(store.query(tags=tags)), 1)
        self.assertEqual(len(store.query(tags=["technical", "novel_delta"])), 1)
        self.assertEqual(store.query(tags=["missing_tag"]), [])

    def test_random_queries_match_bruteforce_superset_reference(self):
        rng = random.Random(7)
        store = PrimeMemoryStore()
        vocabulary = list(DEFAULT_TAG_PRIMES.keys()) + [f"novel_{index}" for index in range(8)]
        expected_tags = {}

        for index in range(40):
            sample_size = rng.randint(0, 12)
            tags = sorted(rng.sample(vocabulary, sample_size))
            record = store.add(
                f"record {index}",
                domain="memory" if index % 2 else "project",
                tags=tags,
                importance=(index % 10) / 10,
            )
            expected_tags[record.record_id] = set(tags)

        for _ in range(50):
            query_tags = sorted(rng.sample(vocabulary, rng.randint(0, 5)))
            actual = {record.record_id for record in store.query(tags=query_tags, limit=100)}
            expected = {
                record_id
                for record_id, tags in expected_tags.items()
                if set(query_tags).issubset(tags)
            }
            self.assertEqual(actual, expected, f"query_tags={query_tags}")

    def test_persistence_preserves_unbounded_tag_products(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "store.json"
            store = PrimeMemoryStore()
            tags = list(DEFAULT_TAG_PRIMES.keys()) + [f"novel_{index}" for index in range(6)]
            record = store.add("persistent many-tag memory", tags=tags)
            store.save(path)

            loaded = PrimeMemoryStore.load(path)
            loaded_record = loaded.get(record.record_id)
            self.assertIsNotNone(loaded_record)
            self.assertEqual(loaded_record.tag_product, record.tag_product)
            self.assertEqual(len(loaded.query(tags=["technical", "novel_5"])), 1)

    def test_pre_tag_product_store_loads_and_recomputes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "store.json"
            store = PrimeMemoryStore()
            record = store.add("old-format memory", tags=["technical", "code"])
            payload = store.to_dict()
            payload["records"][0].pop("tag_product")
            path.write_text(json.dumps(payload), encoding="utf-8")

            loaded = PrimeMemoryStore.load(path)
            loaded_record = loaded.get(record.record_id)
            self.assertIsNotNone(loaded_record)
            self.assertGreater(loaded_record.tag_product, 1)
            self.assertEqual(len(loaded.query(tags=["technical", "code"])), 1)

    def test_duplicate_query_tags_equal_single_tag_query(self):
        store = PrimeMemoryStore()
        store.add("alpha", domain="memory", tags=["technical", "code"])
        store.add("beta", domain="memory", tags=["code"])

        single = {record.record_id for record in store.query(tags=["technical"])}
        duplicated = {record.record_id for record in store.query(tags=["technical", "technical"])}
        self.assertEqual(duplicated, single)
        self.assertEqual(len(single), 1)

    def test_unknown_query_tag_returns_empty_without_mutating_registry(self):
        store = PrimeMemoryStore()
        store.add("alpha", domain="memory", tags=["technical"])
        before = store.tag_registry.to_dict()

        self.assertEqual(store.query(tags=["never_registered_tag"]), [])
        # A mix of known + unknown must also miss and stay non-mutating.
        self.assertEqual(store.query(tags=["technical", "never_registered_tag"]), [])

        after = store.tag_registry.to_dict()
        self.assertEqual(after, before)

    def test_sort_results_flag_preserves_membership_and_default_orders(self):
        store = PrimeMemoryStore()
        for index in range(10):
            store.add(
                f"r{index}",
                domain="memory",
                tags=["technical"] if index % 2 else ["code"],
                importance=index / 10,
            )

        sorted_ids = {r.record_id for r in store.query(domain="memory", limit=100)}
        unsorted_ids = {
            r.record_id
            for r in store.query(domain="memory", limit=100, sort_results=False)
        }
        self.assertEqual(sorted_ids, unsorted_ids)

        # Default behavior stays best-first by score.
        ordered = store.query(domain="memory", limit=100)
        scores = [r.score() for r in ordered]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_record_has_all_tag_primes_uses_tag_product(self):
        store = PrimeMemoryStore()
        record = store.add("x", domain="memory", tags=["technical", "code"])
        tech = store.tag_registry.get_existing("technical")
        code = store.tag_registry.get_existing("code")
        evidence = store.tag_registry.get_existing("evidence")  # default prime the record lacks

        self.assertTrue(record.has_all_tag_primes(tech * code))
        self.assertTrue(record.has_all_tag_primes(tech))
        self.assertTrue(record.has_all_tag_primes(1))  # empty filter matches all
        self.assertFalse(record.has_all_tag_primes(tech * evidence))

    def test_domain_and_no_domain_query_paths_match_bruteforce(self):
        rng = random.Random(11)
        store = PrimeMemoryStore()
        vocab = list(DEFAULT_TAG_PRIMES.keys())
        domains = ["memory", "project", "decision"]
        reference = {}
        for index in range(30):
            domain = domains[index % len(domains)]
            tags = sorted(rng.sample(vocab, rng.randint(0, 4)))
            record = store.add(f"r{index}", domain=domain, tags=tags)
            reference[record.record_id] = (domain, set(tags))

        # No-domain path scans records.values() directly.
        no_domain = {r.record_id for r in store.query(tags=["technical"], limit=100)}
        self.assertEqual(
            no_domain,
            {rid for rid, (_d, tagset) in reference.items() if {"technical"}.issubset(tagset)},
        )

        # Domain path materializes the domain subset from the index.
        in_domain = {r.record_id for r in store.query(domain="memory", tags=["technical"], limit=100)}
        self.assertEqual(
            in_domain,
            {
                rid
                for rid, (dom, tagset) in reference.items()
                if dom == "memory" and {"technical"}.issubset(tagset)
            },
        )


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmarks"))

import benchmark_filters  # noqa: E402


class BenchmarkSmokeTests(unittest.TestCase):
    def test_run_benchmark_results_are_identical(self):
        report = benchmark_filters.run_benchmark(records=200, iterations=2, seed=3, output=None)
        self.assertEqual(len(report["benchmarks"]), 4)
        for bench in report["benchmarks"]:
            self.assertTrue(bench["results_identical"], f"{bench['name']} diverged")

    def test_tag_filter_and_predicate_match_counts_agree(self):
        report = benchmark_filters.run_benchmark(records=200, iterations=1, seed=3, output=None)
        by_name = {bench["name"]: bench for bench in report["benchmarks"]}
        self.assertEqual(
            by_name["tag_filter_unsorted"]["matches"],
            by_name["tag_predicate_only"]["matches"],
        )

    def test_build_store_is_deterministic(self):
        first = benchmark_filters.build_store(150, seed=5, extra_tags=4, max_tags_per_record=4)
        second = benchmark_filters.build_store(150, seed=5, extra_tags=4, max_tags_per_record=4)
        self.assertEqual(set(first.records.keys()), set(second.records.keys()))


if __name__ == "__main__":
    unittest.main()

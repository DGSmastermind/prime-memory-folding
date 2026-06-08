#!/usr/bin/env python3
"""Reproducible benchmarks for Prime Memory Folding filtering.

Compares the prime-addressed store's filters against naive full scans on a
seeded synthetic dataset, and verifies both approaches return identical result
sets *before* reporting any timings. A benchmark that does not produce identical
results is reported as invalid (and exits non-zero).

Honesty notes
-------------
- These are in-memory, single-process Python microbenchmarks. Absolute numbers
  are machine- and interpreter-dependent; treat ratios as indicative.
- The prime tag filter is still O(n) over candidate records: the win is reducing
  per-record tag-intersection to one integer modulo against a precomputed
  ``tag_product`` (plus O(1) domain bucketing via the domain index), not a
  sublinear lookup.
- Unsorted rows isolate the *filter* cost (`sort_results=False`); the sorted row
  is a full end-to-end ``query()`` including best-first ordering. They are
  labeled distinctly so neither is mistaken for the other.
- These numbers are NOT comparable to the legacy "60,000x vs SQL" figure in the
  Aether evidence bundle, which compared a modulo against a naive Python loop,
  not an indexed SQL query.

Usage
-----
    python3 benchmarks/benchmark_filters.py
    python3 benchmarks/benchmark_filters.py --records 50000 --iterations 7
    python3 benchmarks/benchmark_filters.py --output benchmarks/results/run.json
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prime_memory_folding.primes import (  # noqa: E402
    DEFAULT_DOMAIN_PRIMES,
    DEFAULT_TAG_PRIMES,
)
from prime_memory_folding.store import PrimeMemoryStore  # noqa: E402


def build_store(records: int, seed: int, extra_tags: int, max_tags_per_record: int) -> PrimeMemoryStore:
    """Build a deterministic synthetic store from a fixed seed."""
    rng = random.Random(seed)
    store = PrimeMemoryStore()
    domains = list(DEFAULT_DOMAIN_PRIMES.keys())
    vocabulary = list(DEFAULT_TAG_PRIMES.keys()) + [f"t{index}" for index in range(extra_tags)]
    for index in range(records):
        size = rng.randint(0, max_tags_per_record)
        tags = rng.sample(vocabulary, size)
        store.add(
            f"record {index}",
            domain=rng.choice(domains),
            tags=tags,
            importance=rng.random(),
        )
    return store


def _time(fn: Callable[[], object], iterations: int) -> List[float]:
    fn()  # warm up (and prime caches) before measuring
    samples: List[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return samples


def _summary(samples: List[float]) -> Dict[str, float]:
    return {
        "mean_s": statistics.fmean(samples),
        "median_s": statistics.median(samples),
        "min_s": min(samples),
    }


def _compare(name, prime_fn, naive_fn, prime_ids, naive_ids, iterations) -> Dict[str, object]:
    identical = prime_ids == naive_ids
    prime = _summary(_time(prime_fn, iterations))
    naive = _summary(_time(naive_fn, iterations))
    speedup = naive["median_s"] / prime["median_s"] if prime["median_s"] > 0 else None
    return {
        "name": name,
        "matches": len(prime_ids),
        "results_identical": identical,
        "prime": prime,
        "naive": naive,
        "speedup_median_naive_over_prime": speedup,
    }


def run_benchmark(
    *,
    records: int = 20000,
    iterations: int = 5,
    seed: int = 1234,
    extra_tags: int = 14,
    max_tags_per_record: int = 6,
    query_domain: str = "memory",
    query_tags=("technical", "code"),
    output=None,
) -> Dict[str, object]:
    """Run all filter benchmarks and return a structured report."""
    store = build_store(records, seed, extra_tags, max_tags_per_record)
    all_records = list(store.records.values())
    big = len(all_records) + 1

    dnorm = store.domain_registry.normalize(query_domain)
    qnorm = sorted({store.tag_registry.normalize(tag) for tag in query_tags})
    qset = set(qnorm)
    tag_product = store.tag_registry.product_for_existing(qnorm) or 1

    def score_key(record):
        return (record.score(), record.updated_at)

    # A) Domain filter, unsorted/filter-only: O(1) domain index vs naive scan.
    prime_domain = lambda: store.query(domain=query_domain, limit=big, sort_results=False)
    naive_domain = lambda: [r for r in all_records if r.domain == dnorm]
    bench_a = _compare(
        "domain_filter_unsorted",
        prime_domain,
        naive_domain,
        {r.record_id for r in prime_domain()},
        {r.record_id for r in naive_domain()},
        iterations,
    )

    # B) Tag filter, unsorted/filter-only: divisibility vs naive set issubset.
    prime_tag = lambda: store.query(tags=qnorm, limit=big, sort_results=False)
    naive_tag = lambda: [r for r in all_records if qset.issubset(r.tags)]
    bench_b = _compare(
        "tag_filter_unsorted",
        prime_tag,
        naive_tag,
        {r.record_id for r in prime_tag()},
        {r.record_id for r in naive_tag()},
        iterations,
    )

    # C) Tag predicate only: raw divisibility loop vs set issubset loop.
    prime_pred = lambda: [r for r in all_records if r.has_all_tag_primes(tag_product)]
    naive_pred = lambda: [r for r in all_records if qset.issubset(r.tags)]
    bench_c = _compare(
        "tag_predicate_only",
        prime_pred,
        naive_pred,
        {r.record_id for r in prime_pred()},
        {r.record_id for r in naive_pred()},
        iterations,
    )

    # D) Full end-to-end query (sorted) vs naive scan + equivalent sort.
    prime_full = lambda: store.query(tags=qnorm, limit=big, sort_results=True)
    naive_full = lambda: sorted(
        [r for r in all_records if qset.issubset(r.tags)],
        key=score_key,
        reverse=True,
    )
    bench_d = _compare(
        "tag_query_sorted",
        prime_full,
        naive_full,
        {r.record_id for r in prime_full()},
        {r.record_id for r in naive_full()},
        iterations,
    )

    report: Dict[str, object] = {
        "config": {
            "records": records,
            "iterations": iterations,
            "seed": seed,
            "extra_tags": extra_tags,
            "max_tags_per_record": max_tags_per_record,
            "query_domain": dnorm,
            "query_tags": qnorm,
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
        },
        "benchmarks": [bench_a, bench_b, bench_c, bench_d],
        "notes": [
            "In-memory Python microbenchmark; absolute timings are machine-dependent.",
            "Unsorted rows isolate filter cost; tag_query_sorted is full end-to-end query().",
            "Prime tag filter is O(n) over candidates: one modulo per record vs set issubset.",
            "Domain filter benefits from O(1) domain-index bucketing.",
            "Not comparable to the legacy '60,000x vs SQL' evidence figure.",
        ],
    }

    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["output_path"] = str(path)

    return report


def _print_summary(report: Dict[str, object]) -> None:
    config = report["config"]
    print("Prime Memory Folding filter benchmark")
    print(f"  records={config['records']} iterations={config['iterations']} seed={config['seed']}")
    print(f"  query_domain={config['query_domain']!r} query_tags={config['query_tags']}")
    print("")
    header = f"{'benchmark':<24}{'matches':>9}{'prime ms':>12}{'naive ms':>12}{'speedup':>10}{'ok':>5}"
    print(header)
    print("-" * len(header))
    for bench in report["benchmarks"]:
        speedup = bench["speedup_median_naive_over_prime"]
        speedup_text = f"{speedup:.2f}x" if speedup is not None else "n/a"
        ok_text = "yes" if bench["results_identical"] else "NO"
        print(
            f"{bench['name']:<24}{bench['matches']:>9}"
            f"{bench['prime']['median_s'] * 1000:>12.3f}"
            f"{bench['naive']['median_s'] * 1000:>12.3f}"
            f"{speedup_text:>10}{ok_text:>5}"
        )
    if "output_path" in report:
        print(f"\nWrote JSON results to {report['output_path']}")
    if not all(bench["results_identical"] for bench in report["benchmarks"]):
        print("\nWARNING: prime and naive results diverged - benchmark invalid.", file=sys.stderr)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prime Memory Folding filter benchmarks")
    parser.add_argument("--records", type=int, default=20000)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--max-tags-per-record", type=int, default=6)
    parser.add_argument("--output", type=str, default="benchmarks/results/benchmark_filters.json")
    args = parser.parse_args(argv)

    report = run_benchmark(
        records=args.records,
        iterations=args.iterations,
        seed=args.seed,
        max_tags_per_record=args.max_tags_per_record,
        output=args.output,
    )
    _print_summary(report)
    return 0 if all(bench["results_identical"] for bench in report["benchmarks"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())

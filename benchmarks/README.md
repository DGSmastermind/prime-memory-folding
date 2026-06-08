# Benchmarks

Reproducible microbenchmarks for Prime Memory Folding's filtering paths.

```bash
python3 benchmarks/benchmark_filters.py
python3 benchmarks/benchmark_filters.py --records 50000 --iterations 7
python3 benchmarks/benchmark_filters.py --output benchmarks/results/run.json
```

The script prints a summary table and (by default) writes JSON to
`benchmarks/results/benchmark_filters.json`. The `benchmarks/results/` directory
is gitignored because absolute timings are machine-specific.

## What it measures

The dataset is generated from a fixed seed, so the *records, match counts, and
which records match* are deterministic across runs. Only wall-clock timings vary.

| Benchmark | Prime path | Naive baseline |
| --- | --- | --- |
| `domain_filter_unsorted` | `store.query(domain=..., sort_results=False)` via the O(1) domain index | full scan, `record.domain == d` |
| `tag_filter_unsorted` | `store.query(tags=..., sort_results=False)` (prime-product divisibility) | full scan, `set(query).issubset(record.tags)` |
| `tag_predicate_only` | raw `record.has_all_tag_primes(tag_product)` loop | full scan set issubset |
| `tag_query_sorted` | full `store.query(tags=...)` incl. best-first sort | full scan + equivalent sort |

The `*_unsorted` rows pass `sort_results=False` to isolate filtering cost; they
are filter-only, not a full query. `tag_query_sorted` is the real end-to-end
`query()` including the best-first sort, with the naive baseline sorted the same
way for fairness.

Every benchmark **verifies that the prime path and the naive path return the
identical set of record ids** before reporting timings. If they ever diverge,
the run is marked invalid and the CLI exits non-zero.

## Honesty notes

- These are in-memory, single-process Python microbenchmarks. Treat ratios as
  indicative, not as guaranteed production figures.
- The prime tag filter is still **O(n) over candidate records**. The win is
  reducing per-record tag intersection to a single integer modulo against a
  precomputed `tag_product`, plus O(1) domain bucketing via the domain index —
  not a sublinear lookup.
- These numbers are **not comparable** to the legacy "60,000x vs SQL" figure in
  the `evidence/` bundle, which compared a modulo against a naive Python loop
  rather than an indexed SQL query.
- `tag_predicate_only` exposes the raw predicate cost. As of v0.1.x,
  `MemoryRecord.has_all_tag_primes` operates directly on the precomputed
  `tag_product` (no per-record `PrimeAddress.unpack`). If the prime predicate is
  still not faster than the naive set check, that reflects a real property: exact
  tag intersection via one big-integer modulo is competitive with — but not
  categorically faster than — small-set `issubset` in pure CPython. The honest
  structural wins are the O(1) domain index and deterministic addressing.

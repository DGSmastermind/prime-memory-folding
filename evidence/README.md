# Evidence — historical Aether artifacts (provenance, not product)

These files are **provenance, not product**. They are curated, read-only
artifacts from the Aether-Hyper project that show where Prime Memory Folding's
prime-addressing idea originated. They are **not** part of the runtime, are
**not** imported by `prime_memory_folding/`, and are **not** standalone
benchmarks.

> ⚠️ **Historical figures, not standalone claims.** Some retained documents and
> the origin code quote extreme speedups (e.g. "60,000x vs SQL", "142,857,143×").
> Those are historical Aether-internal figures, mostly measured against naive
> Python scans rather than indexed databases — and the analyses here themselves
> temper those numbers and recommend the hybrid approach this project adopts. For
> honest, reproducible numbers for *this* project, run
> `python3 benchmarks/benchmark_filters.py` (see `../benchmarks/README.md`).

## Contents

- `api/services/impact/prime_metrics_cache.py` — the original Aether prime cache
  this project generalized (its docstring carries the historical "60,000x" line).
- `docs/architecture/PRIME_ENCODED_KNOWLEDGE_ARCHITECTURE_ANALYSIS.md`
- `docs/architecture/PRIME_ENCODING_DECISION_BRIEF.md`
- `docs/architecture/PRIME_KNOWLEDGE_GRAPH_ANALYSIS.md`
- `docs/architecture/prime_vs_traditional_comparison.txt`

Deeper Aether internals (consciousness/memory engine source, database schema,
the 29D reference, external-service clients) are intentionally excluded — see
[../docs/EVIDENCE_MANIFEST.md](../docs/EVIDENCE_MANIFEST.md) and
[../docs/DECOUPLING_MAP.md](../docs/DECOUPLING_MAP.md).

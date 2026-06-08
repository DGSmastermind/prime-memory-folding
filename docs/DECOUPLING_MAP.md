# Aether to Standalone Decoupling Map

This product keeps Aether as provenance, not as a runtime dependency.

> **Public evidence bundle** = the `PRIME_*` architecture analyses,
> `prime_vs_traditional_comparison.txt`, and the origin `prime_metrics_cache.py`
> only. The internal Aether sources listed below **informed the extraction but
> are excluded from the public distribution** (consciousness/memory engine
> source, database schema/migration, the 29D vector reference, and
> external-service clients). "Excluded from public bundle" in the table means the
> idea was extracted into the generic runtime, but the original source file is
> not shipped here.

| Aether Source | Standalone Equivalent | Status |
| --- | --- | --- |
| `api/services/impact/prime_metrics_cache.py` | `prime_memory_folding/store.py`, `address.py`, `primes.py` | Extracted into generic domains/tags; origin file kept in public evidence |
| `api/tests/impact/test_prime_metrics_cache.py` | `tests/test_core.py` | Rebuilt as standalone tests; original excluded from public bundle |
| `docs/architecture/PRIME_*` | `docs/TECHNICAL_WHITEPAPER.md`, `docs/ARCHITECTURE.md` | Kept in public evidence and distilled into generic docs |
| `api/services/memory/semantic_memory.py` | `PrimeMemoryStore.query`, `PrimeMemorySystem.recall` | Simplified, dependency-free; original excluded from public bundle |
| `api/services/memory/aging_policy.py` | `FoldingPolicy`, `MemoryFolder.decay_strength` | Generic decay tiers; original excluded from public bundle |
| `api/services/consciousness/memory/memory_consolidation_service.py` | `MemoryFolder.fold_store` | Consolidation/folding adapted without consciousness engine; original excluded from public bundle |
| `api/services/orchestration/memory_context_loader.py` | Vector-weighted folded records | Future adapter pattern; original excluded from public bundle |
| `api/services/recursive_consciousness_memory_processor.py` | Future recursive folding adapter | Informed extraction; excluded from public bundle |
| `api/services/vector_search.py` | `vectors.py` cosine similarity | Local dependency-free version; original excluded from public bundle |
| `database/consciousness_schema.sql` | Future SQLite/Postgres schema | Informed extraction; excluded from public bundle |
| `docs/consciousness/29D_VECTOR_REFERENCE.md` | Generic variable-length vectors | Aether adapter candidate; excluded from public bundle |

## Removed Runtime Couplings

- Consciousness engine.
- Guardian/conscience approval gates.
- Soul service.
- Quantum processor.
- FlureeDB.
- Jina API.
- PostgreSQL/SQLAlchemy.
- Aether-specific 29D constants.

## Preserved Ideas

- Prime products for exact tag intersection.
- Hot cache as the fast path.
- Vectors for semantic similarity.
- Memory strength, decay, and promotion.
- Folding/consolidation of repeated patterns.
- Provenance-first documentation.

## Optional Future Aether Adapter

A future `prime_memory_folding_aether` adapter can add:

- 29D dimension names.
- Aether import/export.
- Guardian policy hooks.
- Consciousness-memory migration scripts.

That adapter should remain optional so the base project stays IDE-agnostic.

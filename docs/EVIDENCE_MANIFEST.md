# Evidence Manifest

The `evidence/` folder contains a curated, slimmed set of Aether-Hyper artifacts
that show where Prime Memory Folding's prime-addressing idea came from. Deeper
Aether internals (consciousness/memory engine source, database schema, the 29D
vector reference, and external-service clients) are intentionally **excluded**
from this public distribution; only non-sensitive prior art is kept.

## Prime Architecture (analysis)

- `evidence/docs/architecture/PRIME_ENCODED_KNOWLEDGE_ARCHITECTURE_ANALYSIS.md`
  - Deep analysis of u128 prime addressing, hybrid vector storage, migration, and three-tier architecture.
- `evidence/docs/architecture/PRIME_ENCODING_DECISION_BRIEF.md`
  - Decision brief recommending a hybrid architecture over a full prime migration.
- `evidence/docs/architecture/PRIME_KNOWLEDGE_GRAPH_ANALYSIS.md`
  - Knowledge-graph analysis covering graph operations, semantic limitations, and the hybrid recommendation.
- `evidence/docs/architecture/prime_vs_traditional_comparison.txt`
  - Visual comparison of traditional entity-relationship storage and prime-encoded hot paths.

## Prime Code (origin)

- `evidence/api/services/impact/prime_metrics_cache.py`
  - The original Aether implementation of prime-addressed storage and domain
    filtering that this project generalized. Note its docstring quotes a
    historical "60,000x vs SQL" figure measured against a naive Python loop, not
    an indexed SQL query. See the standalone benchmarks (`benchmarks/`) for
    honest, reproducible numbers.

## Interpretation Rule

Evidence is provenance, not dependency. The standalone runtime keeps generic
names and generic vector support and has no Aether imports. Aether concepts may
appear in docs as origin story and optional future adapters only.

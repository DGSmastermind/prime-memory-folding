# Prime Memory Folding Technical Whitepaper

## Abstract

Prime Memory Folding is a hybrid memory system for developer agents and IDE tools. It combines deterministic prime-number addressing for hot-path filters, vector similarity for semantic retrieval, and decay-driven folding for long-term compression. The result is not "prime numbers replace databases." The result is sharper: prime arithmetic handles exact structure, vectors handle meaning, and archives handle durability.

## 1. Address Encoding

Every memory record is assigned a 128-bit address split into four unsigned 32-bit lanes:

```text
bits 127..96   domain
bits  95..64   subdomain
bits  63..32   concept
bits  31..0    instance
```

The standalone runtime stores compact identity data in the packed address:

```text
address =
    domain_prime      << 96 |
    subdomain_prime   << 64 |
    concept_bucket    << 32 |
    stable_instance_id
```

The `domain` and `subdomain` lanes are single primes. The `concept` lane is a 32-bit identity or bucket field. It is not the source of truth for tag filtering because real tag-prime products can exceed 32 bits quickly.

Each record stores a separate unbounded `tag_product` Python integer. This means a query for all records tagged with `technical` and `code` can test:

```python
record.tag_product % (prime("technical") * prime("code")) == 0
```

This is the central trick: exact tag intersection becomes arithmetic divisibility while the packed address remains a compact 128-bit identity.

## 2. What Prime Encoding Is Good At

Prime encoding is excellent for:

- Domain filtering.
- Subdomain filtering.
- Tag intersection.
- Compact identity.
- Cache-friendly indexes.
- Fast pre-filtering before expensive semantic work.

Prime encoding is not a replacement for:

- Fuzzy text search.
- Semantic similarity.
- Rich graph traversal.
- Arbitrary metadata queries.
- Long-term analytical storage.

That limitation is a strength when treated honestly. The architecture keeps each layer doing the job it is good at.

## 3. Hybrid Runtime

Prime Memory Folding uses three conceptual tiers.

```text
Tier 1: Prime hot cache
  - 128-bit addresses
  - Domain/subdomain/tag filters
  - JSON persistence in v0.1

Tier 2: Vector semantic layer
  - Per-record float vectors
  - Cosine similarity
  - Swappable future backend: Qdrant, FAISS, sqlite-vec, pgvector

Tier 3: Archive layer
  - Durable source of truth
  - v0.1 JSON store
  - Future: SQLite, Postgres, S3, Git-backed memory packs
```

The Aether evidence argues for this exact shape: prime addresses for hot deterministic paths, vector search for meaning, and conventional storage for history and auditability.

## 4. Folding Algorithm

Folding compresses repeated or similar records into stronger long-term memories.

The v0.1 algorithm:

1. Apply tier-based decay to each record's `strength`.
2. Prune records below `minimum_strength`.
3. Cluster records that share a domain and have cosine similarity above the threshold.
4. Produce one folded record per cluster.
5. The folded record stores:
   - Weighted prototype vector.
   - Combined tags plus `folded`.
   - Boosted importance.
   - Source record ids in metadata.
   - A compact summary string.

The result is a practical version of "memory consolidation": noisy short-term items decay or merge; important patterns become compact long-term records.

## 5. Generic State Vectors

Aether used 29-dimensional consciousness vectors. Prime Memory Folding treats that as one adapter, not the runtime identity. Any vector length can be used:

- 3D toy examples for tests.
- 29D Aether-style state vectors.
- 384D or 768D text embeddings.
- Domain-specific feature vectors.

The store does not require a fixed dimension. Dot products use the shared prefix of both vectors, while each vector's norm is computed from its full stored length, so cross-length comparisons are supported but should be treated as adapter-level behavior rather than a substitute for normalized embedding pipelines.

## 6. MCP Distribution

The MCP server exposes memory operations through tools:

- `prime_memory_encode`
- `prime_memory_store`
- `prime_memory_query`
- `prime_memory_fold`
- `prime_memory_stats`

This makes the system IDE-agnostic. Any client that can launch a local stdio MCP server can use the same memory engine.

## 7. Why This Is Powerful

The value is the composition:

- Prime addresses make structural recall deterministic; the bundled benchmarks show an O(1) domain-index win and exact tag intersection at parity-to-modestly-faster than naive in-memory scans (dataset-dependent) — modest constant factors, not orders of magnitude or a database replacement.
- Vectors keep semantic recall expressive.
- Folding prevents memory from becoming an unbounded log.
- MCP makes the whole system available to agentic IDEs without custom plugin work.
- The evidence bundle preserves the research trail so future builders can inspect the origin rather than trusting a marketing claim.

## 8. Engineering Roadmap

Near-term:

- Add benchmark scripts comparing tag filters against naive scans.
- Add SQLite persistence.
- Add importers for Markdown repositories.
- Add a 29D adapter as optional Aether provenance support.
- Add a stricter MCP protocol test harness.

Mid-term:

- Add Qdrant or FAISS backend adapter.
- Add GitHub Action CI.
- Publish pip package and npm launcher.
- Add memory pack export/import.

Long-term:

- Add per-IDE memory policies.
- Add team-shared memory archives.
- Add privacy and redaction policies.
- Add graph adjacency indexes for multi-hop recall.

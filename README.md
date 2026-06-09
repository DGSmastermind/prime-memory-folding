# Prime Memory Folding

[![CI](https://github.com/coryhubbell/prime-memory-folding/actions/workflows/ci.yml/badge.svg)](https://github.com/coryhubbell/prime-memory-folding/actions/workflows/ci.yml)

Standalone prime-addressed memory encoding with vector-aware folding and MCP IDE integration.

Prime Memory Folding turns a memory store into three cooperating layers:

- A prime-addressed hot path with an O(1) domain index and exact tag-intersection filtering.
- Vector similarity for semantic recall.
- Folding that decays, clusters, compresses, and promotes durable patterns.
- Pluggable local persistence: JSON by default, or optional SQLite (stdlib, opt-in via a `.db`/`.sqlite` store path).
- A stdio MCP server for IDE and agent clients.
- A slim `evidence/` bundle that preserves the original Prime research trail without shipping Aether internals.

The performance story is intentionally grounded: bundled benchmarks show clear domain-index wins, faster raw tag predicates, and full tag queries at parity to modestly faster than naive in-memory scans depending on dataset and run noise. This is not a database replacement or an orders-of-magnitude claim.

## System Map

```mermaid
flowchart LR
    IDE["IDE / Agent Client"] --> MCP["stdio MCP Server"]
    CLI["CLI"] --> System["PrimeMemorySystem"]
    MCP --> System
    System --> Hot["Prime Hot Cache"]
    System --> Vector["Vector Similarity"]
    System --> Folder["Memory Folding"]
    Hot --> Store["JSON or SQLite Store"]
    Vector --> Store
    Folder --> Store
    Evidence["Curated Evidence Bundle: provenance only"] -.-> System
```

## Encoding Model

Each record has a compact 128-bit address plus an unbounded Python integer for exact tag filtering.

```text
domain_prime << 96 | subdomain_prime << 64 | concept_bucket << 32 | stable_instance_id
```

The address stays compact. The record also stores:

```text
tag_product = product(prime(tag) for tag in record.tags)
```

A query for all records tagged `technical` and `code` becomes:

```text
record.tag_product % product(prime("technical"), prime("code")) == 0
```

```mermaid
flowchart TD
    Input["Record: domain, subdomain, tags, vector"] --> Normalize["Normalize labels"]
    Normalize --> Registry["Prime registries"]
    Registry --> Address["128-bit address"]
    Registry --> Product["unbounded tag_product"]
    Address --> Record["MemoryRecord"]
    Product --> Record
    Record --> Index["domain -> record ids"]
    Record --> Persist["JSON persistence"]
```

## Query Flow

```mermaid
flowchart TD
    Query["Query: optional domain, tags, vector"] --> DomainCheck{"Domain filter?"}
    DomainCheck -- "yes" --> Bucket["Use domain index"]
    DomainCheck -- "no" --> Scan["Scan record values"]
    Bucket --> Strength["strength threshold"]
    Scan --> Strength
    Strength --> TagCheck{"Tag filter?"}
    TagCheck -- "yes" --> Modulo["tag_product modulo test"]
    TagCheck -- "no" --> VectorCheck{"Vector query?"}
    Modulo --> VectorCheck
    VectorCheck -- "yes" --> Similarity["cosine similarity"]
    VectorCheck -- "no" --> Sort["best-first sort"]
    Similarity --> Sort
    Sort --> Results["records / MCP tool content"]
```

## Folding Pipeline

```mermaid
flowchart LR
    New["New memories"] --> Decay["Decay strength"]
    Decay --> Prune["Prune weak records"]
    Prune --> Cluster["Cluster by domain + vector similarity"]
    Cluster --> Fold["Merge repeated patterns"]
    Fold --> Promote["Promote folded memory"]
    Promote --> Store["Persist compact long-term state"]
```

## MCP Handshake

The stdio server is hardened around protocol fixtures and malformed-frame recovery. CI smoke-tests `initialize`, `notifications/initialized`, `tools/list`, and `tools/call`; live IDE clients are still a manual validation step.

```mermaid
sequenceDiagram
    participant Client as IDE or Agent
    participant MCP as prime-memory MCP
    participant Store as Memory Store
    Client->>MCP: initialize
    MCP-->>Client: protocolVersion + tools capability
    Client->>MCP: notifications/initialized
    Client->>MCP: tools/list
    MCP-->>Client: 5 prime_memory_* tools
    Client->>MCP: tools/call prime_memory_stats
    MCP->>Store: stats
    Store-->>MCP: domains, tags, records
    MCP-->>Client: tool content
```

The server exposes:

- `prime_memory_encode`
- `prime_memory_store`
- `prime_memory_query`
- `prime_memory_fold`
- `prime_memory_stats`

## Quick Start

```bash
git clone https://github.com/coryhubbell/prime-memory-folding.git
cd prime-memory-folding
python3 -m unittest discover -s tests
python3 -m prime_memory_folding encode architecture --tags '["technical","standalone"]'
python3 -m prime_memory_folding remember "Prime filters are for hot deterministic recall." --tags '["prime","technical"]' --vector '[1,0,0]' --importance 0.9
python3 -m prime_memory_folding query --tags '["technical"]'
python3 -m prime_memory_folding fold
```

Run the MCP server directly:

```bash
python3 -m prime_memory_folding.mcp_server
```

Or through the npm-style launcher:

```bash
node bin/prime-memory-folding-mcp.js
```

See [docs/MCP_IDE_SETUP.md](docs/MCP_IDE_SETUP.md) for Claude, Cursor, VS Code, and JetBrains configuration examples.

## Benchmarks

Reproducible filter benchmarks compare the prime-addressed store against naive full scans on a seeded dataset and verify identical result sets before timing:

```bash
python3 benchmarks/benchmark_filters.py
```

Typical local results in the current alpha are in this range:

| Path | What It Measures | Honest Read |
| --- | --- | --- |
| `domain_filter_unsorted` | domain index vs full scan | clear constant-factor win |
| `tag_predicate_only` | raw modulo predicate vs `set.issubset` | faster in the bundled benchmark |
| `tag_filter_unsorted` | full unsorted tag query | parity to modestly faster |
| `tag_query_sorted` | full sorted query path | parity to modestly faster |

Absolute timings are machine-dependent. These numbers are not comparable to the historical "60,000x vs SQL" figure in the evidence bundle; that is retained as provenance and caveated in [evidence/README.md](evidence/README.md).

## Repository Layout

```text
prime_memory_folding/       Python core, CLI, and MCP server
tests/                      Standard-library unit tests
benchmarks/                 Reproducible filter benchmarks
examples/                   Minimal usage example
docs/                       Technical docs and collaboration plans
ide/                        IDE configuration templates
evidence/                   Curated Prime prior-art docs and origin cache code
bin/                        Node launcher for MCP distribution
```

## Evidence And Provenance

Prime Memory Folding is standalone at runtime. The `evidence/` folder is not imported by the package; it exists so builders can inspect the origin of the idea:

- the original Prime cache implementation
- three Prime architecture analyses
- a visual prime-vs-traditional comparison
- a historical disclaimer that separates Aether-internal figures from this project's reproducible benchmarks

## Roadmap

- GitHub release tag and path-neutral IDE setup templates.
- Vector backend adapters, memory pack import/export, live IDE smoke validation, and optional Aether provenance adapters.

## Status

`v0.1.0-alpha` is dependency-light, MIT-licensed, and designed for local-first experimentation. It is ready for developers who want to inspect the math, run the tests, and wire a small deterministic memory engine into agentic IDE workflows.

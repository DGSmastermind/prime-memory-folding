# Prime Memory Folding

Standalone prime-addressed memory encoding with vector-aware folding and MCP IDE integration.

Prime Memory Folding extracts the useful core from the Aether-Hyper Prime work into a generic developer tool:

- Prime-addressed hot memory: an O(1) domain index plus exact tag-intersection filtering (modest constant-factor wins over naive in-memory scans — see [Benchmarks](#benchmarks)).
- Vector similarity for semantic retrieval.
- Memory folding that decays, clusters, compresses, and promotes durable patterns.
- A stdio MCP server with example configs for Claude, Cursor, VS Code, and JetBrains. Protocol handshake smoke-tested in CI (initialize/tools-list/tools-call + malformed-frame recovery); not yet validated against a live IDE client.
- A curated `evidence/` bundle of the original prime research: the origin cache implementation and the architectural analyses behind this design.

## Quick Start

```bash
cd "/Users/coryhubbell/Desktop/Code Projects/aether-hyper/PRIME memory Folding"
python3 -m unittest discover -s tests
python3 -m prime_memory_folding encode architecture --tags '["technical","standalone"]'
python3 -m prime_memory_folding remember "Prime filters are for hot deterministic recall." --tags '["prime","technical"]' --vector '[1,0,0]' --importance 0.9
python3 -m prime_memory_folding query --tags '["technical"]'
python3 -m prime_memory_folding fold
```

## MCP Server

```bash
python3 -m prime_memory_folding.mcp_server
```

Or through the npm-style wrapper:

```bash
node bin/prime-memory-folding-mcp.js
```

The server exposes:

- `prime_memory_encode`
- `prime_memory_store`
- `prime_memory_query`
- `prime_memory_fold`
- `prime_memory_stats`

See [docs/MCP_IDE_SETUP.md](docs/MCP_IDE_SETUP.md) for Claude, Cursor, VS Code, and JetBrains configuration examples.

## Benchmarks

Reproducible filter benchmarks compare the prime-addressed store against naive full scans on a seeded dataset, verifying identical results before timing:

```bash
python3 benchmarks/benchmark_filters.py
```

This prints a summary table and writes JSON to `benchmarks/results/` (gitignored). See [benchmarks/README.md](benchmarks/README.md) for methodology and honesty notes — absolute timings are machine-dependent, and these numbers are not comparable to the legacy "60,000x vs SQL" figure in the evidence bundle.

## Core Model

Each record gets a 128-bit address:

```text
domain_prime << 96 | subdomain_prime << 64 | concept_bucket << 32 | stable_instance_id
```

The packed address stays compact, while each record also stores an unbounded `tag_product` Python integer. Exact tag intersection uses divisibility on that stored product:

```text
record.tag_product % product(query_tag_primes) == 0
```

That gives the runtime a compact arithmetic namespace without imposing a 32-bit ceiling on tag sets. Prime products are excellent for exact filters. Vectors remain the right tool for fuzzy meaning. Folding bridges both: it uses decay and vector similarity to merge repeated experiences into compact long-term memory.

## Collaboration Flow

Use [docs/CLAUDE_SELECTOR_PLAN.md](docs/CLAUDE_SELECTOR_PLAN.md) before big changes. Claude should select the next build card and review the diff; Codex should implement and verify; the user remains product lead.

## Repository Layout

```text
prime_memory_folding/       Python core, CLI, and MCP server
tests/                      Standard-library unit tests
examples/                   Minimal usage example
docs/                       Technical docs and collaboration plans
ide/                        IDE configuration templates
evidence/                   Curated Prime prior-art docs and origin cache code
bin/                        Node launcher for MCP distribution
```

## Status

This is a v0.1 standalone alpha. It is intentionally dependency-light and designed to be easy to publish on GitHub, test locally, and extend into a larger MCP-backed IDE memory product.

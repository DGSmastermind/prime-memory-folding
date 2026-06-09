# Prime Memory Folding — Technical Reproducibility Thesis

> **Companion thesis:** Technical reproducibility lane for Prime Memory Folding.
> This document records the implementation invariants, measured claims, and reproduction surface behind the README.

## The thesis, stated mechanically

Prime Memory Folding is a small, inspectable memory engine whose claims can be
checked from the repository itself. The breakthrough is not a slogan about prime
numbers. It is a reproducible composition:

- exact structural addressing and filtering;
- semantic vector recall;
- decay-driven folding;
- local-first persistence;
- MCP distribution;
- tests, benchmarks, and evidence boundaries that keep the public claim surface
  narrower than the ambition.

The repository is the proof object. If a claim cannot be demonstrated by the
code, tests, benchmarks, CI, or curated evidence bundle, it should not appear in
the public voice.

## The core invariant: structure is exact

Each memory record carries two structural artifacts:

```text
address =
    domain_prime      << 96 |
    subdomain_prime   << 64 |
    concept_bucket    << 32 |
    stable_instance_id
```

and:

```text
tag_product = product(prime(tag) for tag in record.tags)
```

This split is important. The 128-bit address remains a compact identity and
bucket key. Tag intersection lives in an unbounded Python integer, because real
tag-prime products exceed 32-bit address lanes quickly. A query for records that
contain every requested tag becomes:

```text
record.tag_product % query_tag_product == 0
```

That predicate is exact. It is not fuzzy matching, embedding similarity, string
search, or a heuristic. If a record's tag product is divisible by the query tag
product, the record has all requested prime-tag factors. If it is not divisible,
it does not.

The public claim should therefore be precise:

- Prime Memory Folding supports deterministic exact tag intersection.
- It does not make arbitrary metadata queries magically fast.
- It does not replace a database index planner.

## The hot path: O(1) domain bucketing plus O(n) tag predicates

The runtime keeps a domain index:

```text
domain -> record ids
```

That makes domain filtering a direct bucket lookup before tag, strength, vector,
or sort work. Tag filtering is different: it remains O(n) over the candidate
records, but each candidate check is reduced to one modulo operation against the
precomputed `tag_product`.

That distinction matters for honest GitHub language:

- "O(1) domain index" is a valid structural claim.
- "Exact tag intersection by divisibility" is a valid structural claim.
- "Tag queries are sublinear" is not a valid claim.
- "Orders of magnitude faster than databases" is not a valid claim.

The measured result is narrower and stronger because it is reproducible:
bundled benchmarks show clear constant-factor domain wins, a faster raw tag
predicate in the provided benchmark, and full tag queries at parity to modestly
faster than naive in-memory scans depending on dataset and run noise.

## The semantic path: vectors are additive, not magical

Prime filters answer structural questions: domain, subdomain, exact tags. Vector
similarity answers a different question: which surviving records are
semantically close to a query vector.

The current runtime keeps this intentionally simple:

- vectors are per-record float lists;
- cosine similarity is dependency-free;
- vector length is not fixed by the base package;
- adapters may impose their own embedding dimensions later.

This is enough for local-first semantic recall and tests. It is not a claim that
the base package includes an embedding model, vector database, reranker, or
domain ontology. Those are adapter and roadmap surfaces.

## Folding: memory is not an append-only log

The folding layer turns noisy memory accumulation into a maintenance pass:

1. decay record strength;
2. prune weak records;
3. cluster records by domain and vector similarity;
4. produce folded records with combined tags, prototype vectors, boosted
   importance, and source ids in metadata.

This is the "memory folding" part of the system: repeated or similar records can
compress into stronger long-term patterns. The claim is practical, not mystical:
the store can decay, merge, and promote records so long-running memory does not
only grow as a flat log.

## Persistence: local-first, boring by default, durable when requested

The default store is JSON because it is transparent, inspectable, and easy to
ship. C4 added optional SQLite using only Python's standard-library `sqlite3`.

Backend selection is intentionally simple:

```text
store.json              -> JSON
store.db/.sqlite/.sqlite3 -> SQLite
backend="sqlite"        -> explicit SQLite
backend="json"          -> explicit JSON
```

The SQLite implementation stores both `address` and `tag_product` as decimal
`TEXT`, not SQLite `INTEGER`, because:

- packed addresses are 128-bit;
- tag products are unbounded;
- SQLite signed integers are limited to 64 bits.

This is a correctness choice, not an optimization detail. The tests cover
large-value round trips and reject unknown backend names before disk I/O so a
typo cannot silently write JSON into a `.db` file.

## MCP: protocol behavior is tested, live clients are a separate gate

The MCP server exposes five tools:

- `prime_memory_encode`
- `prime_memory_store`
- `prime_memory_query`
- `prime_memory_fold`
- `prime_memory_stats`

C3 hardened the server around protocol failure modes:

- malformed JSON frames return JSON-RPC `-32700` parse errors;
- the stdio loop survives and continues serving;
- tool-level failures return `isError: true` tool results;
- unknown protocol methods remain JSON-RPC errors;
- CI runs an initialize -> initialized notification -> tools/list -> tools/call
  smoke.

The safe public claim is: protocol handshake smoke-tested in CI. The unsafe
claim, until C5 proves it, is: validated against every live IDE client.

## Evidence boundaries: provenance is included, runtime coupling is not

The public package is Aether-clean at runtime. The `evidence/` directory exists
for lineage, not imports. It retains the origin prime cache and selected
architecture analyses while excluding identity-bearing internals, private
schemas, external-service clients, and the 29D reference.

That boundary is technical as much as ethical:

- the package can be installed and tested without Aether-Hyper;
- public claims can be evaluated without private services;
- optional future Aether adapters can be built without making the base runtime
  depend on them.

The public README should preserve that distinction: evidence explains where the
idea came from; tests and benchmarks explain what this package currently proves.

## What the test suite proves

The current suite covers the key invariants that matter for a public alpha:

- core address packing and record storage;
- unbounded tag products beyond 32-bit address-lane capacity;
- non-mutating query-tag lookup for unknown tags;
- result equivalence between prime and brute-force query paths;
- benchmark dataset determinism and match-count consistency;
- MCP direct handlers and stream transport behavior;
- malformed-frame recovery;
- IDE config parseability;
- SQLite save/load, JSON-to-SQLite migration, SQLite-to-JSON export;
- large `address` and `tag_product` round trips as SQLite `TEXT`;
- backend override validation.

This does not prove production scale, distributed consistency, privacy policy
enforcement, embedding quality, live IDE compatibility, or multi-user memory
governance. Those are future release gates.

## What the benchmarks prove

The benchmark script is designed to make cheating difficult:

1. generate a deterministic seeded dataset;
2. run prime and naive paths;
3. verify identical result sets before timing;
4. label filter-only and sorted end-to-end paths separately;
5. write machine-specific results to a gitignored output file.

The benchmark supports modest public language:

- domain filtering has a real index win;
- raw tag divisibility is competitive with and faster than the naive set check
  in the bundled run;
- full tag queries are around parity to modestly faster after the C2 fixes;
- all timings are CPython in-memory microbenchmarks.

The benchmark does not support historical Aether speedup figures as current
product claims. Those figures remain provenance only.

## Failure modes already caught

The credibility of the project comes partly from what the review loop found and
fixed:

- the initial tag-product design overflowed a 32-bit address lane on realistic
  tag counts;
- query-time unknown tags could have mutated registries without the
  non-mutating read path;
- the first honest benchmark showed prime filtering slower than naive scans;
- per-record address unpacking dominated query time until removed;
- no-domain queries copied key sets and did unnecessary dict lookups until
  optimized;
- malformed MCP frames could kill the stdio loop until C3;
- unknown persistence backends could silently fall through to JSON until C4.

Those are not embarrassing footnotes. They are evidence that the public repo was
shaped by adversarial verification rather than one-pass confidence.

## Reproduction commands

From a fresh clone:

```bash
python3 -m unittest discover -s tests
npm test
python3 benchmarks/benchmark_filters.py
python3 -m prime_memory_folding encode architecture --tags '["technical","standalone"]'
python3 -m prime_memory_folding remember "Prime filters are deterministic." --tags '["prime","technical"]'
python3 -m prime_memory_folding query --tags '["technical"]'
python3 -m prime_memory_folding --store .prime_memory_folding/store.db remember "SQLite-backed memory" --tags '["sqlite"]'
python3 -m prime_memory_folding --store .prime_memory_folding/store.db query --tags '["sqlite"]'
```

The CI workflow runs the unit suite, a CLI smoke, and an MCP handshake smoke
across supported Python versions.

## Recommended public README claim surface

The README can safely lead with:

- "standalone prime-addressed memory encoding with vector-aware folding";
- "exact tag intersection via unbounded prime products";
- "O(1) domain index";
- "JSON default, optional stdlib SQLite";
- "MCP stdio server with CI-smoke-tested protocol handshake";
- "benchmarks show modest constant-factor wins over naive in-memory scans";
- "Aether-origin evidence included as provenance, not runtime."

The README should avoid:

- "prime numbers replace databases";
- "60,000x faster" or similar historical figures as product claims;
- "validated in all IDEs" before live client tests;
- "consciousness runtime" language for the standalone package;
- any implication that evidence files are imported by the runtime.

## The technical closing

Prime Memory Folding is credible because its ambition is decomposed into
checkable parts. Exact structure is handled by primes. Meaning is handled by
vectors. Time is handled by folding. Durability is handled by JSON or SQLite.
IDE reach is handled by MCP. Trust is handled by tests, benchmarks, CI, and a
public refusal to claim more than those artifacts prove.

That is the technical breakthrough: not a black-box memory promise, but an
auditable memory substrate whose moving parts can each be inspected, tested, and
replaced.

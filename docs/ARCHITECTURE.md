# Architecture

## Components

```text
CLI / MCP server
      |
      v
PrimeMemorySystem
      |
      +-- PrimeMemoryStore
      |     +-- PrimeAddress
      |     +-- PrimeRegistry
      |     +-- JSON persistence
      |
      +-- MemoryFolder
            +-- decay policy
            +-- vector clustering
            +-- folded record creation
```

## Data Model

`MemoryRecord` fields:

- `record_id`: hex form of the packed address.
- `address`: 128-bit integer.
- `domain`: normalized domain label.
- `subdomain`: normalized subdomain label.
- `tags`: normalized tag labels.
- `tag_product`: unbounded product of tag primes, used for exact tag-intersection filtering.
- `content`: text payload.
- `vector`: optional float vector.
- `importance`: static salience, 0 to 1.
- `strength`: dynamic decayed strength, 0 to 1.
- `metadata`: arbitrary JSON-compatible metadata.

## Prime Registries

The runtime assigns stable primes to labels. Defaults cover common IDE memory domains, and new labels get the next available prime. Once a label receives a prime, it must not be reassigned for that store.

## Query Paths

Domain query:

```text
candidate ids = domain index[domain]
```

Tag query:

```text
tag_product = product(query tag primes)
include record if record.tag_product % tag_product == 0
```

Vector query:

```text
pre-filter by domain/tags
score remaining records with cosine similarity
sort descending
```

## Persistence

v0.1 uses one JSON file. This is intentionally boring and portable. The next durable backend should be SQLite because it keeps the same local-first GitHub story while enabling indexes, transactions, and easy inspection.

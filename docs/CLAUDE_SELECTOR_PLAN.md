# Claude Selector Collaboration Plan

This is the collaboration protocol for taking Prime Memory Folding from v0.1 alpha to a real GitHub product.

## Roles

**User/Product Lead**

- Owns product direction and final scope calls.
- Chooses when to prioritize research, polish, packaging, or demos.
- Approves naming, claims, public positioning, and release timing.

**Claude Selector**

- Reads the current repo state and selects the next build card.
- Keeps the work coherent across strategy, docs, architecture, and public-facing claims.
- Reviews Codex diffs before public release.

**Codex Builder**

- Implements the selected build card.
- Runs tests and local smoke checks.
- Keeps changes scoped to the selected objective.

**Aether Evidence**

- Provides provenance, prior art, and origin story through `evidence/`.
- Does not dictate runtime API names or public packaging.

## Selector Loop

1. Claude reads:
   - `README.md`
   - `docs/TECHNICAL_WHITEPAPER.md`
   - `docs/DECOUPLING_MAP.md`
   - `docs/EVIDENCE_MANIFEST.md`
   - `prime_memory_folding/`
   - `tests/`

2. Claude picks exactly one next build card:
   - Benchmark card
   - SQLite persistence card
   - MCP compliance card
   - GitHub release polish card
   - IDE setup validation card
   - Aether 29D optional adapter card

3. Claude emits an approved build card using this format:

```text
Build Card: <short name>
Objective:
Non-goals:
Files allowed:
API contract:
Tests required:
Docs required:
Release gate:
Risk notes:
```

4. Codex implements only that card.

5. Codex reports:
   - Files changed.
   - Tests run.
   - Known limitations.
   - Suggested next card.

6. Claude reviews as selector:
   - Correctness.
   - Public claims.
   - API stability.
   - Test adequacy.
   - Packaging/release risk.

7. User decides whether to merge, revise, or select a new card.

## Initial Recommended Build Cards

### Card 1: Benchmarks

Objective: Add reproducible benchmarks for prime tag/domain filters versus naive scans.

Release gate: `python3 benchmarks/benchmark_filters.py` prints deterministic timings and writes JSON results.

### Card 2: SQLite Persistence

Objective: Replace JSON-only storage with optional SQLite backend while keeping JSON export/import.

Release gate: Unit tests cover save/load, query, fold, and migration from JSON.

### Card 3: MCP Compliance Hardening

Objective: Add request/response fixtures for MCP `initialize`, `tools/list`, and `tools/call`.

Release gate: Tests exercise the server handler without launching an IDE.

### Card 4: GitHub Release Polish

Objective: Add CI, badges, issue templates, benchmark screenshots/text output, and release checklist.

Release gate: A fresh clone can run tests and basic CLI commands from README.

## Claude Prompt

Use this prompt when bringing Claude in:

```text
You are the Claude Selector for Prime Memory Folding.

Read the repo folder:
/Users/coryhubbell/Desktop/Code Projects/aether-hyper/PRIME memory Folding

Your job is not to implement. Your job is to select the next build card for Codex and review whether the current public claims are technically honest.

Start with:
1. README.md
2. docs/TECHNICAL_WHITEPAPER.md
3. docs/DECOUPLING_MAP.md
4. docs/EVIDENCE_MANIFEST.md
5. prime_memory_folding/
6. tests/

Return exactly one build card in this format:
Build Card:
Objective:
Non-goals:
Files allowed:
API contract:
Tests required:
Docs required:
Release gate:
Risk notes:

Be strict about collaboration: Claude selects and reviews, Codex implements, user owns product direction.
```

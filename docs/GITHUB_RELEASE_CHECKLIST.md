# Public Release Gate — v0.1.0-alpha

> **Status vocabulary (use it precisely):**
> **"Pushed to GitHub"** is true — `origin/main` carries the full alpha.
> **"Publicly released"** is **not** true until the repo visibility is flipped to
> public **and** an anonymous browser renders the README without a 404.
> Until both hold, this work is *staged*, not *launched*.

---

## 1. Pre-flip verification (while still private)

- [ ] **Logged-in visual glance (Cory)** — open the repo signed in and confirm the
      badge row renders and all six Mermaid diagrams render with **no parse-error
      boxes**. (Anonymous tooling cannot see a private repo, so this step is human.)
- [ ] `python3 -m unittest discover -s tests` → 40/40 OK; `npm test` → 40/40 OK.
- [ ] CLI smoke from `README.md`; MCP handshake smoke from `docs/MCP_IDE_SETUP.md`.
- [ ] Public claims re-read in `README.md`, `docs/PUBLIC_THESIS.md`,
      `docs/TECHNICAL_REPRODUCIBILITY_THESIS.md`, `docs/TECHNICAL_WHITEPAPER.md`
      (Codex claim-risk: clean).
- [ ] `evidence/` is prior-art only (origin cache + analyses); no consciousness
      internals, schema, or secrets.
- [ ] `.prime_memory_folding/`, `__pycache__/`, `benchmarks/results/`, `.DS_Store`
      are not tracked.

## 2. Repo description (apply ONLY with Cory's approval — GitHub setting)

> Prime-addressed memory engine for agents and IDEs: O(1) domain index, exact
> tag-intersection via prime products, vector recall, decay-folding, and an MCP
> server. JSON or stdlib SQLite. Honest, benchmark-grounded, dependency-light —
> extracted from the Aether-Hyper research system as provenance, not runtime.

```bash
gh repo edit coryhubbell/prime-memory-folding --description "Prime-addressed memory engine for agents and IDEs: O(1) domain index, exact tag-intersection via prime products, vector recall, decay-folding, and an MCP server. JSON or stdlib SQLite. Honest, benchmark-grounded, dependency-light — extracted from the Aether-Hyper research system as provenance, not runtime."
```

## 3. Topics (apply ONLY with Cory's approval — GitHub setting)

`mcp` · `model-context-protocol` · `memory` · `agent-memory` · `llm-memory` ·
`prime-encoding` · `vector-search` · `sqlite` · `python` · `ide-tools` ·
`dependency-light` · `reproducible-benchmarks`

```bash
gh repo edit coryhubbell/prime-memory-folding \
  --add-topic mcp --add-topic model-context-protocol --add-topic memory \
  --add-topic agent-memory --add-topic llm-memory --add-topic prime-encoding \
  --add-topic vector-search --add-topic sqlite --add-topic python \
  --add-topic ide-tools --add-topic dependency-light --add-topic reproducible-benchmarks
```

## 4. v0.1.0-alpha release notes (paste into the GitHub Release)

> **Prime Memory Folding v0.1.0-alpha**
>
> A small, inspectable, dependency-light memory engine for agents and IDE tools —
> extracted from the Aether-Hyper research system, with the math made public and
> the identity-bearing internals left behind.
>
> It composes deterministic prime-addressed structure (O(1) domain index; exact
> tag intersection by prime-product divisibility), dependency-free vector recall,
> decay-driven folding, and an MCP stdio server. Persistence is JSON by default
> with optional standard-library SQLite (128-bit addresses and unbounded tag
> products stored as TEXT).
>
> **Honest scope.** Performance is benchmark-grounded: modest, dataset-dependent
> constant-factor wins over naive in-memory scans — not a database replacement,
> not orders of magnitude. Tag filtering is O(n) candidates × one modulo; the
> O(1) part is the domain index. The MCP protocol handshake is smoke-tested in
> CI; validation against live IDE clients is a future gate. The `evidence/`
> bundle is provenance, not runtime — the historical "60,000×" figure from the
> origin is retained only as a caveated historical artifact.
>
> **Reproduce it:**
>
> ```bash
> python3 -m unittest discover -s tests
> python3 benchmarks/benchmark_filters.py
> python3 -m prime_memory_folding query --tags '["technical"]'
> ```
>
> MIT licensed.

## 5. Visibility flip — the launch gate (Cory executes; Claude does NOT)

- [ ] Cory flips the repo to **Public** (Settings → Danger Zone → Change
      visibility, or `gh repo edit coryhubbell/prime-memory-folding --visibility public`).
- [ ] Cory cuts the release/tag: GitHub → Releases → Draft, tag `v0.1.0-alpha`,
      paste §4 — or `gh release create v0.1.0-alpha --title "v0.1.0-alpha" --notes-file <file>`.

## 6. Post-flip verification (Claude can run once public)

- [ ] Anonymous browser → repo README renders (no 404).
- [ ] Badge row renders, including the now-anon-visible CI badge.
- [ ] All six Mermaid diagrams render (composition, system map, encoding, query,
      folding, MCP handshake) with no error boxes.
- [ ] `v0.1.0-alpha` release is visible.

---

## After launch (honest roadmap)

**Shipped in v0.1.0-alpha:** prime addressing + exact tag intersection, O(1)
domain index, vector recall, folding/decay, JSON + optional SQLite, MCP stdio
server with CI-smoke-tested handshake, reproducible benchmarks.

**Open next:** path-neutral IDE config templates (replace hardcoded local paths);
live-IDE handshake validation; Qdrant/FAISS vector adapter; pip publish; Markdown
importer; optional Aether 29D provenance adapter.

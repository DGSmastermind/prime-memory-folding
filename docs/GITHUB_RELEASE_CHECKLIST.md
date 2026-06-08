# GitHub Release Checklist

## Before Public Push

- Run `python3 -m unittest discover -s tests`.
- Run CLI smoke commands from `README.md`.
- Run MCP smoke command from `docs/MCP_IDE_SETUP.md`.
- Review public claims in `README.md` and `docs/TECHNICAL_WHITEPAPER.md`.
- Confirm `evidence/` contains only intended copied source artifacts.
- Confirm `.prime_memory_folding/` local stores are not committed.

## Suggested First Issues

- Add benchmarks.
- Add SQLite backend.
- Add MCP fixture tests.
- Add markdown importer.
- Add optional Aether 29D adapter.

## Suggested First Tags

- `v0.1.0-alpha`: current standalone alpha.
- `v0.2.0`: benchmarked hot-cache release.
- `v0.3.0`: SQLite backend release.
- `v0.4.0`: MCP compliance hardened release.

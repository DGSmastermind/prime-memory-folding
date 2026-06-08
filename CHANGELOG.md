# Changelog

## Unreleased

- Fixed alpha tag filtering so unbounded tag-prime products are stored on records instead of being forced into the 32-bit concept address lane.
- Clarified that the 128-bit concept lane is a compact identity/bucket field and exact tag intersection uses `record.tag_product`.

## 0.1.0-alpha

- Created standalone Python core.
- Added prime-address packing and label registries.
- Added tag-product filtering.
- Added vector similarity helpers.
- Added decay and folding.
- Added JSON persistence.
- Added CLI.
- Added stdio MCP server.
- Added npm-compatible MCP launcher.
- Added tests, docs, IDE config examples, and Aether evidence bundle.

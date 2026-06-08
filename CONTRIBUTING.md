# Contributing

Prime Memory Folding uses the Claude Selector collaboration loop in `docs/CLAUDE_SELECTOR_PLAN.md`.

For meaningful changes:

1. Start from a build card.
2. Keep the diff scoped to the card.
3. Add or update tests.
4. Run `python3 -m unittest discover -s tests`.
5. Update docs when public behavior or claims change.

The base package should stay generic. Aether-specific behavior belongs in optional adapters or evidence docs.

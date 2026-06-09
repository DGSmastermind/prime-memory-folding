"""Command line interface for Prime Memory Folding."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .mcp_server import main as serve_mcp
from .system import PrimeMemorySystem


def parse_jsonish(value: str | None, fallback: Any) -> Any:
    if value is None:
        return fallback
    return json.loads(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prime-memory", description="Prime Memory Folding CLI")
    parser.add_argument(
        "--store",
        default=".prime_memory_folding/store.json",
        help="Path to the store file; .json uses JSON, .db/.sqlite uses SQLite",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    encode = sub.add_parser("encode", help="Encode a prime address")
    encode.add_argument("domain")
    encode.add_argument("--subdomain", default="general")
    encode.add_argument("--tags", default="[]", help="JSON list of tags")
    encode.add_argument("--instance-key")

    remember = sub.add_parser("remember", help="Store a memory")
    remember.add_argument("content")
    remember.add_argument("--domain", default="memory")
    remember.add_argument("--subdomain", default="general")
    remember.add_argument("--tags", default="[]", help="JSON list of tags")
    remember.add_argument("--vector", default="[]", help="JSON list of numbers")
    remember.add_argument("--importance", type=float, default=0.5)
    remember.add_argument("--metadata", default="{}", help="JSON object")

    query = sub.add_parser("query", help="Query memories")
    query.add_argument("--domain")
    query.add_argument("--tags", default="[]", help="JSON list of tags")
    query.add_argument("--vector", help="JSON list of numbers for similarity search")
    query.add_argument("--limit", type=int, default=10)

    sub.add_parser("fold", help="Run folding pass")
    sub.add_parser("stats", help="Show store statistics")
    sub.add_parser("serve-mcp", help="Run stdio MCP server")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "serve-mcp":
        serve_mcp()
        return

    system = PrimeMemorySystem(Path(args.store))
    payload: Dict[str, Any]

    if args.command == "encode":
        payload = system.encode(
            args.domain,
            subdomain=args.subdomain,
            tags=parse_jsonish(args.tags, []),
            instance_key=args.instance_key,
        )
    elif args.command == "remember":
        payload = system.remember(
            args.content,
            domain=args.domain,
            subdomain=args.subdomain,
            tags=parse_jsonish(args.tags, []),
            vector=parse_jsonish(args.vector, []),
            importance=args.importance,
            metadata=parse_jsonish(args.metadata, {}),
        ).to_dict()
    elif args.command == "query":
        payload = {
            "results": system.recall(
                domain=args.domain,
                tags=parse_jsonish(args.tags, []),
                vector=parse_jsonish(args.vector, None),
                limit=args.limit,
            )
        }
    elif args.command == "fold":
        payload = system.fold().to_dict()
    elif args.command == "stats":
        payload = system.stats()
    else:
        parser.error("unknown command")
        return

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

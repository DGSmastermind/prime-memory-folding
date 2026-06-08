"""A minimal stdio MCP server for Prime Memory Folding.

The implementation intentionally avoids a mandatory MCP SDK dependency. It
speaks line-delimited JSON-RPC over stdin/stdout, which is the transport used
by local MCP servers in most IDE integrations.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .system import PrimeMemorySystem


def default_store_path() -> Path:
    base = Path(os.getenv("PRIME_MEMORY_HOME", ".prime_memory_folding"))
    return base / "store.json"


class PrimeMemoryMCPServer:
    def __init__(self, store_path: Optional[Path] = None) -> None:
        self.system = PrimeMemorySystem(store_path or default_store_path())

    def handle(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = message.get("method")
        request_id = message.get("id")
        try:
            if method == "initialize":
                return self._response(
                    request_id,
                    {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {
                            "name": "prime-memory-folding",
                            "version": "0.1.0",
                        },
                        "capabilities": {"tools": {}},
                    },
                )
            if method == "notifications/initialized":
                return None
            if method == "tools/list":
                return self._response(request_id, {"tools": self._tools()})
            if method == "tools/call":
                params = message.get("params", {})
                return self._response(request_id, self._call_tool(params))
            return self._error(request_id, -32601, f"Unknown method: {method}")
        except Exception as exc:
            return self._error(request_id, -32000, str(exc))

    def _tools(self) -> list[Dict[str, Any]]:
        return [
            {
                "name": "prime_memory_encode",
                "description": "Encode a domain/subdomain/tag set into a 128-bit prime address.",
                "inputSchema": {
                    "type": "object",
                        "properties": {
                            "domain": {"type": "string"},
                            "subdomain": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "instance_key": {"type": "string"},
                        },
                    "required": ["domain"],
                },
            },
            {
                "name": "prime_memory_store",
                "description": "Store a memory record with optional vector and metadata.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "domain": {"type": "string"},
                        "subdomain": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "vector": {"type": "array", "items": {"type": "number"}},
                        "importance": {"type": "number"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "prime_memory_query",
                "description": "Query memory by domain, tags, or vector similarity.",
                "inputSchema": {
                    "type": "object",
                        "properties": {
                            "domain": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "vector": {"type": "array", "items": {"type": "number"}},
                            "limit": {"type": "integer"},
                        },
                },
            },
            {
                "name": "prime_memory_fold",
                "description": "Run decay and folding over the current store.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "prime_memory_stats",
                "description": "Return store statistics and current prime registries.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def _call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        args = params.get("arguments", {}) or {}
        if name == "prime_memory_encode":
            payload = self.system.encode(
                domain=args["domain"],
                subdomain=args.get("subdomain", "general"),
                tags=args.get("tags"),
                instance_key=args.get("instance_key"),
            )
        elif name == "prime_memory_store":
            record = self.system.remember(
                content=args["content"],
                domain=args.get("domain", "memory"),
                subdomain=args.get("subdomain", "general"),
                tags=args.get("tags"),
                vector=args.get("vector"),
                importance=args.get("importance", 0.5),
                metadata=args.get("metadata"),
            )
            payload = record.to_dict()
        elif name == "prime_memory_query":
            payload = {
                "results": self.system.recall(
                    domain=args.get("domain"),
                    tags=args.get("tags"),
                    vector=args.get("vector"),
                    limit=int(args.get("limit", 10)),
                )
            }
        elif name == "prime_memory_fold":
            payload = self.system.fold().to_dict()
        elif name == "prime_memory_stats":
            payload = self.system.stats()
        else:
            raise ValueError(f"Unknown tool: {name}")

        return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}

    def _response(self, request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _error(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def serve(self) -> None:
        for line in sys.stdin:
            if not line.strip():
                continue
            response = self.handle(json.loads(line))
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()


def main() -> None:
    store_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    PrimeMemoryMCPServer(store_arg).serve()


if __name__ == "__main__":
    main()

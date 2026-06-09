"""A minimal stdio MCP server for Prime Memory Folding.

The implementation intentionally avoids a mandatory MCP SDK dependency. It
speaks newline-delimited JSON-RPC 2.0 over stdin/stdout, the transport used by
local stdio MCP servers in most IDE integrations.

Robustness contract:
- A malformed input line yields a JSON-RPC parse error (-32700) and the server
  keeps running; one bad frame never kills the loop.
- Protocol-level problems (unknown method, non-object message) are JSON-RPC
  errors. Tool-level problems (unknown tool, bad arguments) are returned as a
  normal ``tools/call`` result with ``isError: true``, per the MCP convention,
  so the client/model can see and recover from them.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, TextIO

from .system import PrimeMemorySystem

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "prime-memory-folding"
SERVER_VERSION = "0.1.0"


def default_store_path() -> Path:
    base = Path(os.getenv("PRIME_MEMORY_HOME", ".prime_memory_folding"))
    return base / "store.json"


class PrimeMemoryMCPServer:
    def __init__(self, store_path: Optional[Path] = None) -> None:
        self.system = PrimeMemorySystem(store_path or default_store_path())

    # -- request handling -------------------------------------------------

    def handle(self, message: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(message, dict):
            return self._error(None, -32600, "Invalid Request: expected a JSON object")

        method = message.get("method")
        request_id = message.get("id")

        # Notifications carry no id and expect no response.
        if method in ("notifications/initialized", "initialized"):
            return None

        try:
            if method == "initialize":
                return self._response(request_id, self._initialize_result())
            if method == "ping":
                return self._response(request_id, {})
            if method == "tools/list":
                return self._response(request_id, {"tools": self._tools()})
            if method == "tools/call":
                return self._response(request_id, self._safe_call_tool(message.get("params") or {}))
            return self._error(request_id, -32601, f"Method not found: {method}")
        except Exception as exc:  # never let one bad request kill the server
            return self._error(request_id, -32603, f"Internal error: {exc}")

    def _initialize_result(self) -> Dict[str, Any]:
        # We implement a single protocol version; report what we support rather
        # than echoing whatever the client requested.
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "capabilities": {"tools": {"listChanged": False}},
        }

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

    def _safe_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        if not name:
            return self._tool_error("Missing required field: name")
        try:
            return self._call_tool(params)
        except KeyError as exc:
            return self._tool_error(f"Missing required argument: {exc}")
        except Exception as exc:
            return self._tool_error(f"Tool '{name}' failed: {exc}")

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

    def _tool_error(self, message: str) -> Dict[str, Any]:
        return {"content": [{"type": "text", "text": message}], "isError": True}

    def _response(self, request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _error(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    # -- transport --------------------------------------------------------

    @staticmethod
    def _emit(sink: TextIO, payload: Dict[str, Any]) -> None:
        sink.write(json.dumps(payload) + "\n")
        sink.flush()

    def serve(self, stdin: Optional[TextIO] = None, stdout: Optional[TextIO] = None) -> None:
        source = stdin if stdin is not None else sys.stdin
        sink = stdout if stdout is not None else sys.stdout
        for line in source:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                self._emit(sink, self._error(None, -32700, f"Parse error: {exc}"))
                continue
            response = self.handle(message)
            if response is not None:
                self._emit(sink, response)


def main() -> None:
    store_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    PrimeMemoryMCPServer(store_arg).serve()


if __name__ == "__main__":
    main()

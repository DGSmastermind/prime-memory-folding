import io
import json
import tempfile
import unittest
from pathlib import Path

from prime_memory_folding.mcp_server import PROTOCOL_VERSION, PrimeMemoryMCPServer

EXPECTED_TOOLS = {
    "prime_memory_encode",
    "prime_memory_store",
    "prime_memory_query",
    "prime_memory_fold",
    "prime_memory_stats",
}


class McpHandlerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.server = PrimeMemoryMCPServer(Path(self._tmp.name) / "store.json")

    def _req(self, method, params=None, request_id=1):
        message = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        return self.server.handle(message)

    def test_initialize_reports_supported_protocol(self):
        res = self._req("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}})
        self.assertEqual(res["result"]["protocolVersion"], PROTOCOL_VERSION)
        self.assertEqual(res["result"]["serverInfo"]["name"], "prime-memory-folding")
        self.assertIn("tools", res["result"]["capabilities"])

    def test_initialized_notification_returns_no_response(self):
        self.assertIsNone(self.server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_ping(self):
        self.assertEqual(self._req("ping")["result"], {})

    def test_tools_list(self):
        tools = self._req("tools/list")["result"]["tools"]
        self.assertEqual({t["name"] for t in tools}, EXPECTED_TOOLS)
        for tool in tools:
            self.assertIn("inputSchema", tool)
            self.assertIn("description", tool)

    def test_tools_call_happy_paths(self):
        enc = self._req("tools/call", {"name": "prime_memory_encode",
                                       "arguments": {"domain": "project", "tags": ["technical"]}})
        self.assertNotIn("isError", enc["result"])
        self.assertIn("content", enc["result"])

        store = self._req("tools/call", {"name": "prime_memory_store",
                                         "arguments": {"content": "hello", "tags": ["technical"], "vector": [1, 0]}})
        self.assertNotIn("isError", store["result"])

        query = self._req("tools/call", {"name": "prime_memory_query", "arguments": {"tags": ["technical"]}})
        self.assertNotIn("isError", query["result"])
        payload = json.loads(query["result"]["content"][0]["text"])
        self.assertGreaterEqual(len(payload["results"]), 1)

        self.assertNotIn("isError", self._req("tools/call", {"name": "prime_memory_fold"})["result"])
        self.assertNotIn("isError", self._req("tools/call", {"name": "prime_memory_stats"})["result"])

    def test_tools_call_unknown_tool_is_error_result(self):
        res = self._req("tools/call", {"name": "does_not_exist", "arguments": {}})
        self.assertTrue(res["result"]["isError"])

    def test_tools_call_missing_required_arg_is_error_result(self):
        res = self._req("tools/call", {"name": "prime_memory_store", "arguments": {}})
        self.assertTrue(res["result"]["isError"])

    def test_tools_call_missing_name_is_error_result(self):
        res = self._req("tools/call", {"arguments": {}})
        self.assertTrue(res["result"]["isError"])

    def test_unknown_method_is_jsonrpc_error(self):
        self.assertEqual(self._req("frobnicate")["error"]["code"], -32601)

    def test_non_object_message_is_invalid_request(self):
        self.assertEqual(self.server.handle(["not", "an", "object"])["error"]["code"], -32600)


class McpServeTransportTests(unittest.TestCase):
    def _run(self, lines):
        with tempfile.TemporaryDirectory() as tmp:
            server = PrimeMemoryMCPServer(Path(tmp) / "store.json")
            stdin = io.StringIO("".join(line + "\n" for line in lines))
            stdout = io.StringIO()
            server.serve(stdin=stdin, stdout=stdout)
            return [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]

    def test_malformed_frame_does_not_crash_and_emits_parse_error(self):
        out = self._run(["{ this is not json", '{"jsonrpc":"2.0","id":7,"method":"ping"}'])
        self.assertEqual(out[0]["error"]["code"], -32700)
        self.assertEqual(out[1]["id"], 7)
        self.assertEqual(out[1]["result"], {})

    def test_full_handshake_sequence(self):
        out = self._run([
            '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}',
            '{"jsonrpc":"2.0","method":"notifications/initialized"}',
            '{"jsonrpc":"2.0","id":2,"method":"tools/list"}',
            '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"prime_memory_stats"}}',
        ])
        # The notification produces no response, so we expect exactly 3.
        self.assertEqual(len(out), 3)
        self.assertEqual([m["id"] for m in out], [1, 2, 3])
        self.assertIn("protocolVersion", out[0]["result"])
        self.assertIn("tools", out[1]["result"])
        self.assertIn("content", out[2]["result"])


class IdeConfigTests(unittest.TestCase):
    CONFIG_DIR = Path(__file__).resolve().parent.parent / "ide"

    def test_all_ide_configs_valid_json_and_launch_the_server(self):
        configs = sorted(self.CONFIG_DIR.glob("*/*.json"))
        self.assertGreaterEqual(len(configs), 4)
        for path in configs:
            data = json.loads(path.read_text(encoding="utf-8"))
            block = data.get("mcpServers") or data.get("servers")
            self.assertIsNotNone(block, f"{path} missing mcpServers/servers block")
            entry = block["prime-memory-folding"]
            self.assertEqual(entry["command"], "node")
            self.assertTrue(
                any("prime-memory-folding-mcp.js" in arg for arg in entry["args"]),
                f"{path} does not launch the MCP bin",
            )


if __name__ == "__main__":
    unittest.main()

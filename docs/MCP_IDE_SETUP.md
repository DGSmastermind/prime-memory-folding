# MCP IDE Setup

Use absolute paths when configuring IDEs. The examples below point at the local workspace folder.

## Claude Desktop

```json
{
  "mcpServers": {
    "prime-memory-folding": {
      "command": "node",
      "args": [
        "/Users/coryhubbell/Desktop/Code Projects/aether-hyper/PRIME memory Folding/bin/prime-memory-folding-mcp.js"
      ],
      "env": {
        "PRIME_MEMORY_HOME": "/Users/coryhubbell/Desktop/Code Projects/aether-hyper/PRIME memory Folding/.prime_memory_folding"
      }
    }
  }
}
```

## Cursor

```json
{
  "mcpServers": {
    "prime-memory-folding": {
      "command": "node",
      "args": [
        "/Users/coryhubbell/Desktop/Code Projects/aether-hyper/PRIME memory Folding/bin/prime-memory-folding-mcp.js"
      ],
      "env": {
        "PRIME_MEMORY_HOME": "/Users/coryhubbell/Desktop/Code Projects/aether-hyper/PRIME memory Folding/.prime_memory_folding"
      }
    }
  }
}
```

## VS Code MCP Clients

Use the same stdio server:

```json
{
  "servers": {
    "prime-memory-folding": {
      "type": "stdio",
      "command": "node",
      "args": [
        "/Users/coryhubbell/Desktop/Code Projects/aether-hyper/PRIME memory Folding/bin/prime-memory-folding-mcp.js"
      ],
      "env": {
        "PRIME_MEMORY_HOME": "/Users/coryhubbell/Desktop/Code Projects/aether-hyper/PRIME memory Folding/.prime_memory_folding"
      }
    }
  }
}
```

## JetBrains MCP Clients

Use command:

```text
node
```

Arguments:

```text
/Users/coryhubbell/Desktop/Code Projects/aether-hyper/PRIME memory Folding/bin/prime-memory-folding-mcp.js
```

Environment:

```text
PRIME_MEMORY_HOME=/Users/coryhubbell/Desktop/Code Projects/aether-hyper/PRIME memory Folding/.prime_memory_folding
```

## Smoke Test

You can test the server by sending one JSON-RPC request:

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n' | node "/Users/coryhubbell/Desktop/Code Projects/aether-hyper/PRIME memory Folding/bin/prime-memory-folding-mcp.js"
```

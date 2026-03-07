# Claude Code

Add persistent memory to Claude Code in 2 minutes.

Claude Code is Anthropic's CLI-based AI coding assistant. With Remembra, Claude remembers your preferences, project context, and decisions across sessions.

## Prerequisites

1. **Remembra server running** — [Quick start](../getting-started/quickstart.md) or `docker compose up -d`
2. **MCP package installed:**
   ```bash
   pip install remembra[mcp]
   ```

## Setup

Register Remembra as an MCP server:

```bash
claude mcp add remembra \
  -e REMEMBRA_URL=http://localhost:8787 \
  -- remembra-mcp
```

That's it. Claude Code will now have access to Remembra's memory tools.

### With Authentication

If your server has auth enabled:

```bash
claude mcp add remembra \
  -e REMEMBRA_URL=http://localhost:8787 \
  -e REMEMBRA_API_KEY=your_key_here \
  -e REMEMBRA_USER_ID=your_user_id \
  -- remembra-mcp
```

## Verify

```bash
claude mcp list
# remembra: remembra-mcp — ✓ Connected
```

## Try It

Start a Claude Code session and test:

```
You: Remember that I prefer TypeScript, use Tailwind CSS, and deploy to Vercel.
Claude: I'll save that to memory.
       [Tool: store_memory] ✓ Stored — 3 facts extracted

You: What's my preferred stack?
Claude: Let me check my memory...
       [Tool: recall_memories]
       You prefer TypeScript, use Tailwind CSS, and deploy to Vercel.
```

## Project-Wide Config

Share Remembra config with your team by adding `.mcp.json` to your project root:

```json
{
  "mcpServers": {
    "remembra": {
      "command": "remembra-mcp",
      "env": {
        "REMEMBRA_URL": "${REMEMBRA_URL:-http://localhost:8787}",
        "REMEMBRA_API_KEY": "${REMEMBRA_API_KEY}",
        "REMEMBRA_USER_ID": "${REMEMBRA_USER_ID:-default}",
        "REMEMBRA_PROJECT": "${REMEMBRA_PROJECT:-default}"
      }
    }
  }
}
```

Commit this file — anyone who clones the repo gets Remembra automatically.

## Troubleshooting

### "remembra-mcp: command not found"

Make sure the MCP package is installed:

```bash
pip install remembra[mcp]
which remembra-mcp
```

### "Connection refused"

Ensure the Remembra server is running:

```bash
curl http://localhost:8787/health
```

### Tools not appearing

```bash
claude mcp list          # Check status
claude mcp logs remembra # View logs
```

If the status shows disconnected, remove and re-add:

```bash
claude mcp remove remembra
claude mcp add remembra -e REMEMBRA_URL=http://localhost:8787 -- remembra-mcp
```

## Next Steps

- [MCP Tool Reference](mcp-server.md) — Full documentation of all 5 tools and 2 resources
- [Python SDK](../guides/python-sdk.md) — Programmatic access from Python
- [Conversation Ingestion](../guides/conversation-ingestion.md) — Auto-extract memories from conversations

# MCP Server — Tool Reference

Complete reference for Remembra's MCP tools, resources, and configuration.

Use Remembra as persistent memory for AI assistants via the [Model Context Protocol](https://modelcontextprotocol.io).

## Setup Guides

Step-by-step setup instructions for each AI tool:

| Tool | Guide |
|------|-------|
| **Claude Code** | [Setup guide](claude-code.md) — `claude mcp add remembra ...` |
| **Claude Desktop** | [Setup guide](claude-desktop.md) — JSON config |
| **Cursor** | [Setup guide](cursor.md) — `.cursor/mcp.json` |
| **Windsurf** | [Setup guide](windsurf.md) — `mcp_config.json` |
| **Zed** | [Setup guide](zed.md) — `context_servers` in settings |
| **OpenAI Codex** | [Setup guide](codex.md) — `codex mcp add remembra ...` |
| **VS Code + Copilot** | [Setup guide](vscode.md) — `.vscode/mcp.json` |
| **JetBrains IDEs** | [Setup guide](jetbrains.md) — Settings → AI Assistant → MCP |
| **Any MCP client** | [Generic guide](any-mcp-client.md) — stdio, SSE, HTTP |

## Installation

```bash
pip install remembra[mcp]
```

This installs both the Remembra SDK and the MCP server binary (`remembra-mcp`).

---

## Tools Reference

### store_memory

Store information in persistent memory.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | ✅ | Text content to memorize |
| `metadata` | object | ❌ | Key-value metadata (e.g., `{"source": "meeting"}`) |
| `ttl` | string | ❌ | Time-to-live: `24h`, `7d`, `30d`, `1y`, or omit for permanent |

**Example:**
```
Claude: I'll remember that.
[Tool: store_memory]
content: "User prefers TypeScript over JavaScript and uses Tailwind CSS"
metadata: {"source": "preferences"}

Result:
{
  "status": "stored",
  "id": "mem_abc123",
  "extracted_facts": [
    "User prefers TypeScript over JavaScript",
    "User uses Tailwind CSS"
  ],
  "entities": [
    {"name": "TypeScript", "type": "TECHNOLOGY"},
    {"name": "Tailwind CSS", "type": "TECHNOLOGY"}
  ]
}
```

---

### recall_memories

Search persistent memory for relevant information.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | Natural language query or keywords |
| `limit` | int | ❌ | 5 | Max results (1-50) |
| `threshold` | float | ❌ | 0.4 | Min relevance (0.0-1.0) |

**Example:**
```
User: What framework do I prefer?
Claude: Let me check my memory...
[Tool: recall_memories]
query: "user framework preferences"

Result:
{
  "status": "ok",
  "context": "User prefers TypeScript over JavaScript and uses Tailwind CSS.",
  "memories": [
    {
      "id": "mem_abc123",
      "content": "User prefers TypeScript over JavaScript",
      "relevance": 0.92
    }
  ]
}
```

---

### forget_memories

Delete memories from persistent storage. GDPR-compliant.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `memory_id` | string | ❌ | Delete specific memory by ID |
| `entity` | string | ❌ | Delete all memories about an entity |
| `all_memories` | bool | ❌ | Delete ALL memories (use with caution!) |

!!! warning
    Exactly one parameter must be provided. `all_memories=true` is destructive!

**Examples:**
```
# Delete specific memory
[Tool: forget_memories]
memory_id: "mem_abc123"

# Delete all about a person
[Tool: forget_memories]
entity: "John Smith"

# Nuclear option
[Tool: forget_memories]
all_memories: true
```

---

### health_check

Check Remembra server health and connection status.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| (none) | - | - | No parameters needed |

**Example:**
```
[Tool: health_check]

Result:
{
  "status": "ok",
  "server": "http://localhost:8787",
  "health": {
    "status": "healthy",
    "version": "0.9.9",
    "qdrant": "connected",
    "database": "connected"
  }
}
```

---

### ingest_conversation <span class="md-tag">v0.8.0</span>

Automatically extract memories from a conversation. This is the **primary method** for agents to add context to memory.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `messages` | array | ✅ | - | List of `{role, content}` message objects |
| `session_id` | string | ❌ | auto | Session ID for grouping |
| `min_importance` | float | ❌ | 0.5 | Importance threshold (0.0-1.0) |
| `extract_from` | string | ❌ | "both" | `"user"`, `"assistant"`, or `"both"` |
| `store` | bool | ❌ | true | Set `false` for dry-run |

**Example:**
```
[Tool: ingest_conversation]
messages: [
  {"role": "user", "content": "My wife Sarah and I are moving to Seattle next month"},
  {"role": "assistant", "content": "That's exciting! What brings you to Seattle?"},
  {"role": "user", "content": "I got a job at Amazon as a senior engineer"}
]
min_importance: 0.5

Result:
{
  "status": "ok",
  "facts_extracted": 4,
  "facts_stored": 3,
  "facts_deduped": 1,
  "entities_found": 3,
  "facts": [
    {"content": "User's wife is named Sarah", "importance": 0.8},
    {"content": "User is moving to Seattle next month", "importance": 0.7},
    {"content": "User works at Amazon as a senior engineer", "importance": 0.9}
  ],
  "entities": [
    {"name": "Sarah", "type": "PERSON"},
    {"name": "Seattle", "type": "LOCATION"},
    {"name": "Amazon", "type": "ORGANIZATION"}
  ]
}
```

---

### update_memory <span class="md-tag">v0.9.9</span>

Update an existing memory's content. Re-extracts facts and entities from the new content.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `memory_id` | string | ✅ | ID of the memory to update |
| `content` | string | ✅ | New content for the memory |
| `metadata` | object | ❌ | Optional metadata to update |

**Example:**
```
[Tool: update_memory]
memory_id: "mem_abc123"
content: "User is now CTO at Acme Corp (promoted from Senior Engineer)"

Result:
{
  "status": "updated",
  "id": "mem_abc123",
  "extracted_facts": [
    "User is CTO at Acme Corp",
    "User was promoted from Senior Engineer"
  ],
  "updated_entities": [
    {"name": "Acme Corp", "type": "ORGANIZATION"}
  ]
}
```

---

### search_entities <span class="md-tag">v0.9.9</span>

Search the entity graph. Find people, companies, locations, and concepts that Remembra knows about.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ❌ | - | Filter by entity name (partial match) |
| `entity_type` | string | ❌ | - | Filter: `person`, `organization`, `location`, `concept` |
| `limit` | int | ❌ | 20 | Max entities to return (max: 100) |

**Example:**
```
[Tool: search_entities]
query: "Alice"
entity_type: "person"

Result:
{
  "status": "ok",
  "count": 2,
  "entities": [
    {
      "id": "ent_123",
      "name": "Alice Johnson",
      "type": "person",
      "aliases": ["Alice", "AJ"],
      "memory_count": 5
    },
    {
      "id": "ent_456",
      "name": "Alice Chen",
      "type": "person",
      "aliases": [],
      "memory_count": 2
    }
  ]
}
```

---

### list_memories <span class="md-tag">v0.9.9</span>

Browse stored memories without a search query. Returns recent memories.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | int | ❌ | 10 | Max memories to return (1-50) |
| `project_id` | string | ❌ | - | Filter by project namespace |

**Example:**
```
[Tool: list_memories]
limit: 5

Result:
{
  "status": "ok",
  "count": 5,
  "memories": [
    {
      "id": "mem_abc123",
      "content": "User prefers TypeScript over JavaScript...",
      "created_at": "2024-03-08T15:30:00Z"
    },
    {
      "id": "mem_def456",
      "content": "Meeting with Alice scheduled for Friday...",
      "created_at": "2024-03-08T14:20:00Z"
    }
  ]
}
```

---

### share_memory <span class="md-tag">v0.9.9</span>

Share a memory to a collaborative space for cross-agent sharing.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `memory_id` | string | ✅ | ID of the memory to share |
| `space_id` | string | ✅ | ID of the target space |

**Example:**
```
[Tool: share_memory]
memory_id: "mem_abc123"
space_id: "space_engineering"

Result:
{
  "status": "shared",
  "memory_id": "mem_abc123",
  "space_id": "space_engineering",
  "message": "Memory shared to space successfully"
}
```

---

### timeline <span class="md-tag">v0.9.9</span>

Browse memories chronologically, optionally filtered by entity and date range.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entity_name` | string | ❌ | - | Filter by entity (person, org, etc.) |
| `start_date` | string | ❌ | - | Start of range (ISO format, e.g., `2024-01-01`) |
| `end_date` | string | ❌ | - | End of range (ISO format) |
| `limit` | int | ❌ | 20 | Max memories to return |

**Example:**
```
[Tool: timeline]
entity_name: "Alice"
start_date: "2026-01-01"
end_date: "2026-03-01"

Result:
{
  "status": "ok",
  "count": 3,
  "entity_filter": "Alice",
  "date_range": {"start": "2026-01-01", "end": "2026-03-01"},
  "memories": [
    {
      "id": "mem_001",
      "content": "Alice joined the engineering team",
      "created_at": "2026-01-15T10:00:00Z"
    },
    {
      "id": "mem_002",
      "content": "Alice completed the API redesign project",
      "created_at": "2026-02-20T14:30:00Z"
    }
  ]
}
```

---

### relationships_at <span class="md-tag">v0.9.9</span>

Query entity relationships at a specific point in time. Enables temporal queries like "Where did Alice work in January?"

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entity_name` | string | ✅ | - | Entity to query relationships for |
| `as_of` | string | ❌ | current | Point in time (ISO format, e.g., `2022-01-15`) |
| `relationship_type` | string | ❌ | - | Filter: `WORKS_AT`, `SPOUSE_OF`, `ROLE`, etc. |
| `include_history` | bool | ❌ | false | Include superseded relationships |

**Example:**
```
[Tool: relationships_at]
entity_name: "Alice"
as_of: "2025-06-15"
include_history: true

Result:
{
  "status": "ok",
  "entity": "Alice",
  "as_of": "2025-06-15",
  "count": 2,
  "relationships": [
    {
      "type": "WORKS_AT",
      "from": "Alice",
      "to": "Google",
      "valid_from": "2023-03-01",
      "valid_to": null,
      "is_current": true
    },
    {
      "type": "WORKS_AT",
      "from": "Alice",
      "to": "Meta",
      "valid_from": "2020-01-15",
      "valid_to": "2023-02-28",
      "is_current": false,
      "superseded_by": "rel_abc123"
    }
  ]
}
```

---

## Resources

MCP resources provide quick access to memory data without tool calls.

### memory://recent

Returns the 10 most recently stored memories.

```json
{
  "count": 10,
  "memories": [
    {
      "id": "mem_xyz",
      "content": "User prefers dark mode",
      "relevance": 1.0,
      "created_at": "2026-03-03T12:00:00Z"
    }
  ]
}
```

### memory://status

Returns server status and configuration.

```json
{
  "server": "http://localhost:8787",
  "user_id": "user_123",
  "project": "default",
  "health": {"status": "healthy", "version": "0.9.9"}
}
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REMEMBRA_URL` | `http://localhost:8787` | Remembra server URL |
| `REMEMBRA_API_KEY` | - | API key for authentication |
| `REMEMBRA_USER_ID` | `default` | User ID for memory isolation |
| `REMEMBRA_PROJECT` | `default` | Project namespace |
| `REMEMBRA_MCP_TRANSPORT` | `stdio` | Transport: `stdio`, `sse`, or `streamable-http` |

---

## Transport Modes

### stdio (Default)

Standard I/O transport for local MCP clients.

```bash
remembra-mcp
# or explicitly:
REMEMBRA_MCP_TRANSPORT=stdio remembra-mcp
```

### SSE (Server-Sent Events)

For remote/networked connections:

```bash
REMEMBRA_MCP_TRANSPORT=sse remembra-mcp
```

### Streamable HTTP

For HTTP-based transports:

```bash
REMEMBRA_MCP_TRANSPORT=streamable-http remembra-mcp
```

---

## Troubleshooting

### "Connection refused" error

1. Ensure Remembra server is running:
   ```bash
   docker ps | grep remembra
   # or
   curl http://localhost:8787/health
   ```

2. Check the URL in your config matches the running server.

### "Unauthorized" or 401 errors

1. Verify your API key is correct
2. Check if auth is enabled on the server:
   ```bash
   curl -H "X-API-Key: your_key" http://localhost:8787/health
   ```

### Tool not appearing in Claude

1. Restart Claude Code/Desktop after config changes
2. Verify MCP server is running:
   ```bash
   claude mcp list
   ```
3. Check logs for errors:
   ```bash
   claude mcp logs remembra
   ```

### Memory not persisting

1. Check user_id is consistent across sessions
2. Verify store operations return success
3. Check server logs for errors

---

## Best Practices

### 1. Use ingest_conversation for chat context

Instead of manually storing individual facts, ingest the full conversation:

```python
# ❌ Manual (tedious)
store_memory("User likes TypeScript")
store_memory("User works at Acme")

# ✅ Automatic (recommended)
ingest_conversation(messages=[...], min_importance=0.5)
```

### 2. Recall before answering

Always check memory before answering questions about past context:

```
User: What's my preferred stack?
Claude: [recalls memories first, then answers]
```

### 3. Use appropriate TTL

- `24h` — Session context, temporary preferences
- `7d` — Short-term project context
- `30d` — Monthly goals, ongoing work
- `1y` — Long-term preferences, relationships
- (none) — Permanent facts

### 4. Namespace with projects

Use `REMEMBRA_PROJECT` to separate memory spaces:

```bash
REMEMBRA_PROJECT=work-assistant    # Work memories
REMEMBRA_PROJECT=personal-assistant # Personal memories
```

---

## Example: Full Session

```
User: Remember that I'm working on the Acme project with Sarah. 
      We're using React and PostgreSQL. The deadline is March 15th.

Claude: I'll save that context.
[Tool: store_memory]
content: "Working on Acme project with Sarah. Stack: React + PostgreSQL. Deadline: March 15th."
metadata: {"project": "acme", "type": "context"}

Result: ✓ Stored (3 facts extracted, 2 entities found)

---

[Next session]

User: What's the deadline for the project I'm working on?

Claude: Let me check my memory.
[Tool: recall_memories]
query: "project deadline"

Result: "Working on Acme project... Deadline: March 15th"

Claude: The Acme project deadline is March 15th. You're working on it with Sarah using React and PostgreSQL.
```

---

## Related

- [Python SDK](../guides/python-sdk.md)
- [JavaScript SDK](../guides/javascript-sdk.md)
- [Conversation Ingestion](../guides/conversation-ingestion.md)
- [REST API](../guides/rest-api.md)

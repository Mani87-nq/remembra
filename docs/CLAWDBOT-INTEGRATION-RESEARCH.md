# Clawdbot + Remembra Integration Research

## Executive Summary

Clawdbot has a **plugin system** with built-in memory plugin slots. We can create a `remembra` plugin that replaces the default memory system with Remembra's intelligent storage.

## Key Findings

### 1. Memory Plugin Architecture

Clawdbot supports **exclusive memory plugins** via `plugins.slots.memory`:

```json5
{
  plugins: {
    slots: {
      memory: "remembra"  // or "memory-core", "memory-lancedb", "none"
    }
  }
}
```

Only ONE memory plugin can be active at a time.

### 2. Plugin Lifecycle Hooks (Critical!)

The `memory-lancedb` plugin demonstrates two key hooks:

```typescript
// AUTO-RECALL: Inject memories before agent starts
api.on("before_agent_start", async (event) => {
  // event.prompt contains the user's message
  // Return { prependContext: "..." } to inject memories
});

// AUTO-CAPTURE: Store important info after agent ends
api.on("agent_end", async (event) => {
  // event.messages contains the conversation
  // Analyze and store to memory
});
```

### 3. Pre-Compaction Memory Flush

Clawdbot has a **separate** pre-compaction hook (not in the plugin system yet):

```json5
{
  agents: {
    defaults: {
      compaction: {
        memoryFlush: {
          enabled: true,
          softThresholdTokens: 4000,
          systemPrompt: "Session nearing compaction. Store durable memories now.",
          prompt: "Write any lasting notes to memory/..."
        }
      }
    }
  }
}
```

This triggers a silent agentic turn to write memories before compaction.

### 4. What memory-lancedb Does (Reference Implementation)

- **Auto-recall**: Embeds user prompt → vector search → injects relevant memories
- **Auto-capture**: Filters messages for "capturable" content → stores automatically
- **Tools**: `memory_recall`, `memory_store`, `memory_forget`
- **Pattern detection**: Triggers on "remember", preferences, contacts, decisions
- **Duplicate detection**: High-similarity check before storing

## Remembra Plugin Design

### Plugin Structure

```
clawdbot-remembra/
├── clawdbot.plugin.json
├── package.json
├── index.ts
├── src/
│   ├── client.ts       # Remembra API client
│   ├── recall.ts       # Auto-recall logic
│   ├── capture.ts      # Auto-capture logic
│   └── tools.ts        # Tool definitions
└── README.md
```

### Plugin Manifest (clawdbot.plugin.json)

```json
{
  "id": "remembra",
  "kind": "memory",
  "name": "Remembra",
  "description": "AI memory with entity resolution, temporal features, and graph-aware recall",
  "configSchema": {
    "type": "object",
    "properties": {
      "apiUrl": { "type": "string", "default": "http://localhost:8787" },
      "apiKey": { "type": "string" },
      "userId": { "type": "string" },
      "autoRecall": { "type": "boolean", "default": true },
      "autoCapture": { "type": "boolean", "default": true }
    },
    "required": ["apiKey"]
  }
}
```

### Core Implementation

```typescript
import type { ClawdbotPluginApi } from "clawdbot/plugin-sdk";
import { RemembraClient } from "./src/client.js";

const remembraPlugin = {
  id: "remembra",
  name: "Remembra",
  kind: "memory" as const,
  configSchema: { /* ... */ },
  
  register(api: ClawdbotPluginApi) {
    const cfg = api.pluginConfig;
    const client = new RemembraClient(cfg.apiUrl, cfg.apiKey);
    
    // AUTO-RECALL: Before agent starts
    if (cfg.autoRecall) {
      api.on("before_agent_start", async (event) => {
        const memories = await client.recall(event.prompt, cfg.userId);
        if (memories.length === 0) return;
        
        return {
          prependContext: formatMemoriesForContext(memories)
        };
      });
    }
    
    // AUTO-CAPTURE: After agent ends
    if (cfg.autoCapture) {
      api.on("agent_end", async (event) => {
        const toStore = extractCapturableContent(event.messages);
        for (const content of toStore) {
          await client.store(content, cfg.userId);
        }
      });
    }
    
    // TOOLS: memory_recall, memory_store, memory_forget
    api.registerTool(/* memory_recall */);
    api.registerTool(/* memory_store */);
    api.registerTool(/* memory_forget */);
    
    // CLI: remembra status/recall/store/forget
    api.registerCli(/* ... */);
  }
};

export default remembraPlugin;
```

### Advantages Over File-Based Memory

| Feature | File-Based (memory-core) | Remembra Plugin |
|---------|--------------------------|-----------------|
| Entity Resolution | ❌ | ✅ "Mr. Kim" = "David Kim" |
| Temporal Decay | ❌ | ✅ Ebbinghaus-based |
| TTL Support | ❌ | ✅ session → permanent |
| Hybrid Search | Basic | ✅ Vector + BM25 + Graph |
| Cross-Session | ❌ Files per session | ✅ Unified memory layer |
| Multi-Agent | ❌ Per workspace | ✅ User-scoped |

## Implementation Plan

### Phase 1: Basic Plugin (1-2 days)
- [ ] Create plugin scaffold
- [ ] Implement RemembraClient (API wrapper)
- [ ] Register `memory_recall`, `memory_store`, `memory_forget` tools
- [ ] Test with `plugins.slots.memory = "remembra"`

### Phase 2: Auto-Recall/Capture (1 day)
- [ ] Implement `before_agent_start` hook
- [ ] Implement `agent_end` hook
- [ ] Add smart capture filtering (patterns, duplicates)
- [ ] Test end-to-end flow

### Phase 3: Pre-Compaction Integration (1 day)
- [ ] Customize `compaction.memoryFlush` prompts
- [ ] Or: Hook into compaction events (may need core changes)
- [ ] Test context preservation across compaction

### Phase 4: Polish & Distribution (1 day)
- [ ] CLI commands (`clawdbot remembra status/recall/store`)
- [ ] Configuration UI hints
- [ ] Documentation
- [ ] Publish to npm as `@remembra/clawdbot`

## Quick Start (After Plugin Built)

```bash
# Install
clawdbot plugins install @remembra/clawdbot

# Configure
clawdbot config set plugins.slots.memory remembra
clawdbot config set plugins.entries.remembra.config.apiUrl http://localhost:8787
clawdbot config set plugins.entries.remembra.config.apiKey YOUR_KEY

# Restart
clawdbot gateway restart
```

## Open Questions

1. **Compaction hook access**: Can plugins hook into pre-compaction, or is it hardcoded?
2. **Session memory**: Should we also index session transcripts via Remembra?
3. **Entity scope**: Per-user or per-agent entity resolution?
4. **Fallback**: What happens if Remembra server is down?

## References

- Clawdbot plugin docs: `/plugin.md`
- Memory docs: `/concepts/memory.md`
- memory-lancedb source: `extensions/memory-lancedb/index.ts`
- memory-core source: `extensions/memory-core/index.ts`

# Week 8 Research: Temporal Features

## Executive Summary

Temporal features transform Remembra from a static memory store into a **time-aware knowledge system**. This enables:
- Memories that automatically expire (TTL)
- Relevance decay over time (old memories rank lower)
- Historical queries ("What did I know on Feb 15th?")
- Fact versioning (track how information changes)

---

## 1. Industry Research

### Zep/Graphiti (State of the Art)
- **Paper:** "Zep: A Temporal Knowledge Graph Architecture for Agent Memory" (Jan 2025)
- **Performance:** 94.8% on DMR benchmark (vs MemGPT's 93.4%)
- **Key Innovation:** Temporally-aware knowledge graph that maintains historical relationships
- **Dual-timestamp model:**
  - `event_time` - When the fact was true
  - `ingestion_time` - When we learned it
- **Non-lossy updates:** New info doesn't delete old, creates new version with validity periods

### CortexGraph (Human-like Forgetting)
- Implements Ebbinghaus forgetting curves
- Memories decay unless reinforced through retrieval
- JSONL for short-term, Markdown for long-term
- MCP server integration for Claude

### Kore (Local Memory with Decay)
- Half-life based on importance:
  - Casual notes: 7 days
  - Critical info: 1 year
- Auto-importance scoring (local, no LLM needed)
- Memories fade unless retrieved

### MemoryBank Paper
- Ebbinghaus forgetting curve: `R = e^(-t/S)`
  - R = retention
  - t = time elapsed
  - S = stability (how well it's learned)

---

## 2. Temporal Data Model

### Current Schema
```sql
memories (
    id, user_id, project_id, content, 
    created_at,  -- Only timestamp we have
    ...
)
```

### Proposed Schema Extensions
```sql
-- Add temporal columns to memories
ALTER TABLE memories ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE memories ADD COLUMN valid_from TIMESTAMP;  -- When fact became true
ALTER TABLE memories ADD COLUMN valid_until TIMESTAMP; -- When fact stopped being true (NULL = still valid)
ALTER TABLE memories ADD COLUMN expires_at TIMESTAMP;  -- TTL: when to auto-delete
ALTER TABLE memories ADD COLUMN last_accessed_at TIMESTAMP; -- For decay calculation
ALTER TABLE memories ADD COLUMN access_count INTEGER DEFAULT 0; -- Reinforcement
ALTER TABLE memories ADD COLUMN decay_rate REAL DEFAULT 1.0; -- Custom decay speed
```

### Temporal Validity
```
Timeline:
─────────────────────────────────────────────────►
     |<---- valid_from      valid_until ---->|
     [======= Memory is TRUE in this window =====]
```

---

## 3. Memory Decay Algorithm

### Ebbinghaus Forgetting Curve
```python
import math
from datetime import datetime, timedelta

def calculate_retention(
    created_at: datetime,
    last_accessed_at: datetime,
    access_count: int,
    base_half_life_days: float = 30.0,
) -> float:
    """
    Calculate memory retention (0.0 to 1.0) using Ebbinghaus curve.
    
    Each access reinforces the memory, extending half-life.
    """
    now = datetime.utcnow()
    
    # Time since last access (in days)
    time_since_access = (now - last_accessed_at).total_seconds() / 86400
    
    # Reinforcement: each access doubles the half-life (up to a cap)
    reinforced_half_life = base_half_life_days * (2 ** min(access_count, 5))
    
    # Exponential decay: R = e^(-t/half_life * ln(2))
    decay_constant = math.log(2) / reinforced_half_life
    retention = math.exp(-decay_constant * time_since_access)
    
    return max(0.0, min(1.0, retention))
```

### Decay Tiers (Kore-inspired)
| Memory Type | Base Half-Life | Description |
|-------------|----------------|-------------|
| ephemeral | 1 day | Transient info, session context |
| normal | 7 days | Standard memories |
| important | 30 days | Key facts, decisions |
| permanent | 365 days | Critical info, core knowledge |

---

## 4. TTL (Time-to-Live) Implementation

### Auto-Expiration
```python
async def cleanup_expired_memories(db: Database) -> int:
    """Delete memories past their expires_at timestamp."""
    result = await db.execute("""
        DELETE FROM memories 
        WHERE expires_at IS NOT NULL 
        AND expires_at < datetime('now')
    """)
    return result.rowcount
```

### Soft Delete Option
Instead of hard delete, mark as expired:
```sql
UPDATE memories 
SET valid_until = datetime('now'), is_expired = TRUE
WHERE expires_at IS NOT NULL AND expires_at < datetime('now')
```

### TTL Configuration
```
REMEMBRA_DEFAULT_TTL_DAYS=null  # null = no expiration
REMEMBRA_EPHEMERAL_TTL_HOURS=24
REMEMBRA_ENABLE_AUTO_CLEANUP=true
REMEMBRA_CLEANUP_INTERVAL_HOURS=1
```

---

## 5. Historical Queries (Time Travel)

### Query Types

**Point-in-Time Query:**
```python
# What did I know about "Project X" on Feb 15th?
await memory.recall(
    query="Project X",
    as_of="2026-02-15T00:00:00Z"
)
```

**Implementation:**
```sql
SELECT * FROM memories
WHERE user_id = ?
AND created_at <= ?  -- Existed by that date
AND (valid_until IS NULL OR valid_until > ?)  -- Still valid then
ORDER BY created_at DESC
```

**Temporal Range Query:**
```python
# How did my understanding of "budgets" change over time?
await memory.recall(
    query="budgets",
    from_date="2026-01-01",
    to_date="2026-03-01",
    show_versions=True
)
```

---

## 6. Relevance Scoring with Decay

### Current Scoring (Week 6)
```python
score = (
    semantic_weight * semantic_score +
    recency_weight * recency_score +
    entity_weight * entity_score +
    keyword_weight * keyword_score
)
```

### Enhanced with Decay
```python
def calculate_relevance(
    semantic_score: float,
    memory: Memory,
    query_time: datetime = None,
) -> float:
    query_time = query_time or datetime.utcnow()
    
    # Calculate retention (0.0 to 1.0)
    retention = calculate_retention(
        created_at=memory.created_at,
        last_accessed_at=memory.last_accessed_at,
        access_count=memory.access_count,
    )
    
    # Apply decay to relevance
    base_score = semantic_score
    decayed_score = base_score * retention
    
    # Floor to prevent total loss of important memories
    min_retention = 0.1 if memory.importance == "permanent" else 0.01
    
    return max(decayed_score, base_score * min_retention)
```

---

## 7. Implementation Plan

### Phase 1: Schema & TTL (3 hours)
- Add temporal columns to memories table
- Implement expires_at field
- Background cleanup job for expired memories
- Store endpoint accepts `ttl_hours` parameter

### Phase 2: Access Tracking (2 hours)
- Update last_accessed_at on recall
- Increment access_count on retrieval
- Track which memories are "hot" vs "cold"

### Phase 3: Decay Algorithm (3 hours)
- Implement Ebbinghaus-based retention calculation
- Integrate decay into relevance ranking
- Configurable decay rates per memory/user

### Phase 4: Historical Queries (4 hours)
- Add `as_of` parameter to recall
- Implement valid_from/valid_until tracking
- Support temporal range queries

### Phase 5: Fact Versioning (3 hours)
- When updating a fact, create new version
- Link versions together (previous_version_id)
- Query: "Show me how this fact changed"

**Total: ~15 hours**

---

## 8. Config Variables

```
# TTL
REMEMBRA_DEFAULT_TTL_DAYS=null
REMEMBRA_ENABLE_AUTO_CLEANUP=true
REMEMBRA_CLEANUP_INTERVAL_HOURS=1

# Decay
REMEMBRA_ENABLE_DECAY=true
REMEMBRA_BASE_HALF_LIFE_DAYS=30
REMEMBRA_MIN_RETENTION=0.01
REMEMBRA_MAX_REINFORCEMENT_MULTIPLIER=32

# Historical
REMEMBRA_ENABLE_VERSIONING=true
REMEMBRA_KEEP_VERSIONS=10
```

---

## 9. API Changes

### Store Endpoint
```python
class StoreRequest(BaseModel):
    content: str
    user_id: str
    ttl_hours: int | None = None  # NEW
    importance: Literal["ephemeral", "normal", "important", "permanent"] = "normal"  # NEW
    valid_from: datetime | None = None  # NEW: when this fact became true
```

### Recall Endpoint
```python
class RecallRequest(BaseModel):
    query: str
    user_id: str
    as_of: datetime | None = None  # NEW: time-travel query
    include_expired: bool = False  # NEW: include decayed memories
    min_retention: float = 0.1  # NEW: filter out heavily decayed
```

---

## References
- [Zep Paper](https://arxiv.org/abs/2501.13956) - Temporal Knowledge Graph Architecture
- [CortexGraph](https://github.com/prefrontal-systems/cortexgraph) - Human-like forgetting
- [Kore HN Discussion](https://news.ycombinator.com/item?id=47070979) - Ebbinghaus decay
- [MemoryBank Paper](https://arxiv.org/pdf/2305.10250) - Forgetting curve formula

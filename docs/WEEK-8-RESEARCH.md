# Week 8 Research: Temporal Features

**Date:** 2026-03-01
**Status:** READY FOR REVIEW
**Reviewer:** Mani

---

## Executive Summary

Week 8 focuses on making Remembra time-aware. Memories should decay, expire, and be queryable at specific points in time. This mirrors how human memory works and is critical for production AI agents.

---

## Research Sources

| Source | Credibility | Key Insight |
|--------|-------------|-------------|
| AWS AgentCore Deep Dive | ★★★★★ | Temporal ordering, conflict resolution with recency priority |
| OneUpTime Long-Term Memory | ★★★★☆ | Episodic vs semantic decay rates, importance scoring |
| arXiv Field-Theoretic Memory | ★★★★☆ | Thermodynamic decay contributes 31.8% to context retention |
| arXiv Forgetful but Faithful | ★★★★★ | Temporal hygiene + importance estimation = best privacy/recall balance |

---

## Key Findings

### 1. Memory Decay Patterns (CRITICAL)

**Different memory types decay differently:**
- **Episodic memories** (specific events) → decay FASTER
- **Semantic memories** (facts/knowledge) → decay SLOWER

**Research recommendation:**
```python
# Exponential decay formula
importance *= exp(-decay_rate * days_since_access)

# Default decay rates (per research)
EPISODIC_DECAY = 0.05  # Half-life ~14 days
SEMANTIC_DECAY = 0.01  # Half-life ~70 days
```

**arXiv finding:** "Thermodynamic decay contributes 31.8% to context retention improvement" — meaning decay is NOT optional, it's a major quality factor.

### 2. TTL (Time-to-Live) Best Practices

**From Tellius research:**
- In-memory datasets: 30 days default TTL
- Live/active datasets: 120 minutes default

**Our recommendation for Remembra:**
| Memory Type | Default TTL | Configurable |
|-------------|-------------|--------------|
| Episodic | 90 days | Yes |
| Semantic | None (permanent) | Yes |
| Procedural | None | Yes |
| User-specified | Custom | Yes |

**Implementation:**
```python
memory.store(
    "Meeting with John at 3pm tomorrow",
    ttl="7d",  # Auto-expire after 7 days
    memory_type="episodic"
)
```

### 3. Temporal Conflict Resolution

**AWS AgentCore approach (recommended):**
```
Existing: "Customer budget is $500"
New: "Customer mentioned budget increased to $750"
Result: New active memory with $750, previous memory marked INACTIVE
```

**Key principles:**
1. **Recency wins** — newer information takes priority
2. **Don't delete** — mark old memories inactive (audit trail)
3. **Timestamp everything** — created_at, updated_at, last_accessed

### 4. Historical Queries (as_of)

**Use case:** "What did I know about John as of January 2026?"

**Implementation approach:**
```python
# Query memories as they existed at a point in time
context = memory.recall(
    "What do I know about John?",
    as_of="2026-01-15T00:00:00Z"
)
```

**SQL pattern:**
```sql
SELECT * FROM memories 
WHERE user_id = ? 
  AND created_at <= ?
  AND (invalidated_at IS NULL OR invalidated_at > ?)
ORDER BY created_at DESC
```

### 5. Access-Based Importance

**OneUpTime pattern:**
```python
@dataclass
class MemoryEntry:
    access_count: int = 0
    last_accessed: datetime = None
    importance: float = 0.5
    
    def on_access(self):
        self.access_count += 1
        self.last_accessed = datetime.now()
        # Boost importance on access
        self.importance = min(1.0, self.importance + 0.1)
```

**Frequently accessed memories should decay slower.** This is how human memory works — rehearsal strengthens recall.

---

## Proposed Implementation

### Database Schema Changes

```sql
-- Add temporal columns to memories table
ALTER TABLE memories ADD COLUMN expires_at TEXT;  -- TTL
ALTER TABLE memories ADD COLUMN decay_rate REAL DEFAULT 0.01;
ALTER TABLE memories ADD COLUMN invalidated_at TEXT;  -- Soft delete timestamp
ALTER TABLE memories ADD COLUMN memory_type TEXT DEFAULT 'semantic';

-- Index for historical queries
CREATE INDEX idx_memories_temporal ON memories(created_at, invalidated_at);
```

### API Changes

**Store with TTL:**
```python
POST /api/v1/memories
{
    "content": "Meeting tomorrow at 3pm",
    "ttl_days": 7,
    "memory_type": "episodic"
}
```

**Recall with as_of:**
```python
POST /api/v1/memories/recall
{
    "query": "What meetings do I have?",
    "as_of": "2026-02-15T00:00:00Z"
}
```

**New endpoint - Apply decay:**
```python
POST /api/v1/memories/maintenance/decay
# Runs decay algorithm on all memories
# Returns: {"processed": 1500, "pruned": 23}
```

### SDK Changes

```python
# TTL support
memory.store("Event reminder", ttl="24h")
memory.store("Preference", ttl=None)  # Permanent

# Historical queries
memory.recall("user preferences", as_of="2026-01-01")

# Memory maintenance
memory.run_decay()  # Apply decay algorithm
memory.prune_expired()  # Remove expired memories
```

---

## Week 8 Task Breakdown

| Task | Priority | Est. Hours | Notes |
|------|----------|------------|-------|
| TTL support (expires_at) | HIGH | 4 | Schema + store + cleanup job |
| Memory decay algorithm | HIGH | 4 | Exponential decay with access boost |
| Historical queries (as_of) | MEDIUM | 4 | Query memories at point in time |
| Soft delete (invalidated_at) | HIGH | 2 | Never hard delete, mark inactive |
| Decay maintenance endpoint | MEDIUM | 2 | Manual/cron trigger for decay |
| Performance optimization | MEDIUM | 3 | Index tuning, batch operations |
| **Fix consolidation FK bug** | CRITICAL | 3 | Blocking issue from Week 7 |
| **Changelog ingestion** | HIGH | 3 | New feature for project history |

**Total estimated: ~25 hours**

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Decay too aggressive | Medium | High | Make decay_rate configurable per-user |
| Historical queries slow | Medium | Medium | Proper indexing, query optimization |
| TTL cleanup missing memories | Low | High | Soft delete first, hard delete after 30d |
| Breaking existing memories | Medium | High | Migration script, backward compat |

---

## Open Questions for Mani

1. **Default TTL for episodic memories?** Research suggests 90 days, but could be shorter for some use cases.

2. **Should decay run automatically?** Options:
   - On every recall (slight latency hit)
   - Background job (cron-style)
   - Manual trigger only

3. **Memory types?** Should we enforce types (episodic/semantic/procedural) or keep it flexible with metadata?

4. **Changelog ingestion scope?** Just CHANGELOG.md or also README, git commits, release notes?

---

## Recommendation

**Build order:**
1. Fix consolidation FK bug (unblocks everything)
2. TTL + expires_at (most requested feature)
3. Soft delete + invalidated_at (safety net)
4. Decay algorithm (quality improvement)
5. Historical queries (power user feature)
6. Changelog ingestion (dogfooding feature)

**Confidence level:** HIGH — research is solid, patterns are proven.

---

*Ready for your review, Mani. Let me know if you want to adjust anything before we build.*

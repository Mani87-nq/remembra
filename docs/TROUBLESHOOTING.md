# Troubleshooting Guide

Common issues and solutions when setting up and running Remembra.

---

## Table of Contents

1. [Recall Returns Empty Results](#recall-returns-empty-results)
2. [Entity Graph Not Loading](#entity-graph-not-loading)
3. [Dashboard Shows Data but Features Don't Work](#dashboard-shows-data-but-features-dont-work)
4. [Qdrant Connection Issues](#qdrant-connection-issues)

---

## Recall Returns Empty Results

### Symptoms
- `POST /api/v1/memories/recall` returns `{"memories": [], "context": ""}`
- Timeline shows memories exist (they're in SQLite)
- New memories store and recall correctly
- Only OLD memories can't be found

### Cause
Memories were stored in SQLite but their vector embeddings weren't saved to Qdrant. This can happen if:
- Qdrant was temporarily unavailable during store
- The embedding service failed silently
- Memories were imported/migrated without re-vectorization

### Diagnosis
```bash
# Check if memories exist in SQLite
curl -s "$API/debug/timeline?page=1" -H "Authorization: Bearer $TOKEN" | jq '.total'
# Returns: 44 (memories exist)

# Check if recall finds them
curl -s -X POST "$API/memories/recall" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "any keyword", "limit": 10}' | jq '.memories | length'
# Returns: 0 (vectors missing)
```

### Solution
Use the admin rebuild-vectors endpoint (requires superadmin/owner access):

```bash
# Dry run first - see what's missing
curl -s -X POST "$API/admin/rebuild-vectors?dry_run=true" \
  -H "Authorization: Bearer $TOKEN" | jq .

# If missing memories found, run for real
curl -s -X POST "$API/admin/rebuild-vectors?dry_run=false" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

This will:
1. Scan all memories in SQLite
2. Check which ones are missing from Qdrant
3. Re-generate embeddings and store them

---

## Entity Graph Not Loading

### Symptoms
- Graph visualization shows "Loading..." forever or errors
- Console shows many failed API requests
- Other dashboard features work fine

### Cause (Fixed in v0.7.2)
The EntityGraph component was making N+1 queries - one API call per entity to fetch relationships. With 50+ entities, this caused:
- Rate limiting
- Slow load times
- Potential timeouts

### Solution
Update to v0.7.2+ which uses the efficient `/debug/entities/graph` endpoint that returns all nodes and edges in a single request.

If you're on an older version, update `dashboard/src/components/EntityGraph.tsx`:

```typescript
// OLD (inefficient)
const fetchGraphData = async () => {
  const entities = await api.listEntities();
  for (const entity of entities) {
    const rels = await api.getEntityRelationships(entity.id); // N+1!
  }
};

// NEW (efficient)
const fetchGraphData = async () => {
  const graphData = await api.getEntityGraph(projectId);
  // Single request returns all nodes + edges
};
```

---

## Dashboard Shows Data but Features Don't Work

### Symptoms
- Timeline shows memories
- Analytics shows stats
- But recall/search returns nothing
- Graph loads but shows no connections

### Cause
This usually indicates a split-brain state where:
- SQLite has the memory metadata
- Qdrant is missing the vector embeddings
- Or vice versa

### Diagnosis
```bash
# Check health endpoint
curl -s "$API/health" | jq .

# Should show:
{
  "status": "ok",
  "dependencies": {
    "qdrant": { "status": "ok" }
  }
}
```

### Solution
1. Ensure Qdrant is running and accessible
2. Run the rebuild-vectors endpoint (see above)
3. If issues persist, check Qdrant collection exists:

```bash
# Direct Qdrant check (if accessible)
curl -s "http://localhost:6333/collections/remembra" | jq .
```

---

## Qdrant Connection Issues

### Symptoms
- Health check shows `"qdrant": { "status": "error" }`
- Store operations fail
- Application logs show connection errors

### Common Causes

**1. Wrong Qdrant URL**
```bash
# Check your environment
echo $QDRANT_URL
# Should be: http://localhost:6333 or your Qdrant host
```

**2. Qdrant not running**
```bash
# Docker
docker ps | grep qdrant

# Start if needed
docker run -d -p 6333:6333 qdrant/qdrant
```

**3. Collection doesn't exist**
Remembra auto-creates the collection on startup. If it fails:
```bash
# Check logs for initialization errors
docker logs remembra-api 2>&1 | grep -i "collection\|qdrant"
```

**4. Network issues (Docker)**
If running in Docker, ensure containers can communicate:
```yaml
# docker-compose.yml
services:
  api:
    environment:
      - QDRANT_URL=http://qdrant:6333  # Use service name, not localhost
  qdrant:
    image: qdrant/qdrant
```

---

## Still Having Issues?

1. Check the logs: `docker logs remembra-api`
2. Enable debug logging: `REMEMBRA_LOG_LEVEL=debug`
3. Join our Discord: https://discord.gg/Bzv3JshRa3
4. Open an issue: https://github.com/remembradev/remembra/issues

---

*Last updated: March 6, 2026*

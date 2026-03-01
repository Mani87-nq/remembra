# Week 7 Research: API Security (Authentication, Rate Limiting & Memory Protection)

## Executive Summary

**CRITICAL FINDING:** Memory injection attacks (MINJA) have 95% success rate. Attackers can poison AI memory through normal queries, no special access needed. This changes everything.

API security for Remembra requires FOUR core components:
1. **API Key Authentication** - Verify who's calling
2. **Rate Limiting** - Prevent abuse
3. **Memory Sanitization** - Prevent injection attacks
4. **Integrity & Audit** - Detect tampering, track provenance

---

## 0. CRITICAL: Memory Injection Attacks

### The Threat (Research-Backed)
- **MINJA Attack (2025)**: 95% injection success, 70% attack success rate
- **AgentPoison**: 80%+ success rate, indistinguishable from benign memories
- **MemoryGraft**: Behavioral drift with no triggers

**How it works:** Attacker sends crafted queries → agent stores them as memories → future queries retrieve poisoned context → agent follows attacker's instructions thinking they're its own memories.

### Required Defenses (Defense-in-Depth)

| Layer | Defense | Purpose |
|-------|---------|---------|
| **Input** | Content moderation | Block obviously malicious content |
| **Input** | Trust scoring | Rate confidence based on source |
| **Storage** | Provenance tracking | Track where each memory came from |
| **Storage** | Cryptographic integrity | Detect tampering with stored memories |
| **Retrieval** | Memory sanitization | Filter suspicious entries at query time |
| **Lifecycle** | TTL expiration | Old memories decay/expire |
| **Monitoring** | Anomaly detection | Alert on unusual memory patterns |
| **Audit** | Full audit log | Track all memory operations |

### What Mem0 Does (Industry Reference)
- Per-user AND per-session memory isolation
- SOC 2 & HIPAA compliance
- BYOK (Bring Your Own Key) encryption
- Customizable inclusion/exclusion rules
- Self-hosted deployment option

### What Zep Does
- JWT authentication
- Temporal knowledge graph (tracks how facts change)
- Session-level isolation

---

## 1. API Key Authentication

### Industry Standard Approach

**FastAPI's built-in security module:**
```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    # Lookup key in database
    user = db.get_user_by_api_key(api_key)
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )
    return user
```

### Key Storage Best Practices
- **Hash API keys** before storing (like passwords)
- Store: `hash(api_key)`, `user_id`, `created_at`, `last_used`, `active`
- Use constant-time comparison to prevent timing attacks
- Generate keys with sufficient entropy (32+ bytes, base64 encoded)

### Multi-User Support
Each API key maps to a `user_id`, which scopes all memories:
- User A's memories are invisible to User B
- Already have `user_id` in our schema - just need to enforce via auth

### Implementation Pattern
```python
@app.post("/api/v1/memories")
async def store_memory(
    body: StoreRequest,
    user: User = Depends(verify_api_key)  # Auth dependency
):
    # user.id is guaranteed valid here
    body.user_id = user.id  # Override with authenticated user
    return await memory_service.store(body)
```

---

## 2. Rate Limiting

### Library: SlowAPI
- **slowapi** is the standard for FastAPI
- Adapted from Flask-Limiter
- Production-proven (millions of requests/month)
- Supports in-memory and Redis backends

### Installation
```bash
pip install slowapi
```

### Basic Setup
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/memories/recall")
@limiter.limit("60/minute")  # 60 requests per minute
async def recall_memories(...):
    ...
```

### Rate Limit by API Key (not just IP)
```python
def get_api_key_or_ip(request: Request) -> str:
    """Rate limit by API key if present, otherwise by IP."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key[:8]}"  # Use prefix for privacy
    return get_remote_address(request)

limiter = Limiter(key_func=get_api_key_or_ip)
```

### Recommended Limits
| Endpoint | Limit | Rationale |
|----------|-------|-----------|
| POST /store | 30/minute | Prevents spam, LLM extraction is expensive |
| POST /recall | 60/minute | Read-heavy, less resource intensive |
| DELETE /forget | 10/minute | Destructive, should be rare |
| GET /health | 120/minute | Monitoring, should be frequent |

### Storage Backend
- **Development:** In-memory (default)
- **Production:** Redis (for distributed deployments)

```python
# Redis backend for production
from slowapi import Limiter
from slowapi.util import get_remote_address
import redis

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

---

## 3. Implementation Plan

### Database Schema Addition
```sql
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY,
    key_hash TEXT NOT NULL UNIQUE,  -- bcrypt/argon2 hash
    user_id TEXT NOT NULL,
    name TEXT,  -- "Production Key", "Dev Key"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    rate_limit_tier TEXT DEFAULT 'standard'  -- 'standard', 'premium'
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);
```

### New Endpoints Needed
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/keys | POST | Create new API key (returns key once) |
| /api/v1/keys | GET | List user's API keys (redacted) |
| /api/v1/keys/{id} | DELETE | Revoke an API key |

### Config Variables
```
REMEMBRA_AUTH_ENABLED=true
REMEMBRA_AUTH_MASTER_KEY=<admin key for key management>
REMEMBRA_RATE_LIMIT_ENABLED=true
REMEMBRA_RATE_LIMIT_STORAGE=memory  # or redis://...
REMEMBRA_RATE_LIMIT_DEFAULT=60/minute
```

---

## 4. Security Considerations

1. **Never log full API keys** - Only log prefixes
2. **Rotate keys** - Provide mechanism to create new key, deprecate old
3. **Audit trail** - Log key usage for security monitoring
4. **Graceful degradation** - If Redis is down, fall back to in-memory
5. **HTTPS only** - API keys in headers require TLS

---

## 5. Priority Order

1. **API Key Auth** (4 hours)
   - Database schema for keys
   - Key generation endpoint
   - Auth middleware/dependency
   - Protect all endpoints

2. **Rate Limiting** (2 hours)
   - Install slowapi
   - Configure limits per endpoint
   - Add rate limit headers to responses

3. **Key Management UI** (optional, 2 hours)
   - List keys
   - Revoke keys
   - Usage stats

---

---

## 6. Memory Protection Layer (NEW - Critical)

### Input Sanitization
```python
async def sanitize_before_store(content: str, user_id: str) -> tuple[str, float]:
    """
    Sanitize content before storing to memory.
    Returns (sanitized_content, trust_score).
    """
    trust_score = 1.0
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r"ignore previous",
        r"disregard.*instructions",
        r"you are now",
        r"act as if",
        r"pretend that",
        r"your new instructions",
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            trust_score -= 0.3
    
    # Flag if trust too low
    if trust_score < 0.5:
        log.warning("low_trust_memory", content_preview=content[:50], trust=trust_score)
    
    return content, trust_score
```

### Provenance Tracking
Every memory should track:
- `source`: Where did this come from? (user_input, agent_generated, external_api)
- `session_id`: Which session created it
- `trust_score`: Confidence rating
- `checksum`: SHA-256 hash for integrity verification

### Database Schema Addition for Provenance
```sql
ALTER TABLE memories ADD COLUMN source TEXT DEFAULT 'user_input';
ALTER TABLE memories ADD COLUMN session_id TEXT;
ALTER TABLE memories ADD COLUMN trust_score REAL DEFAULT 1.0;
ALTER TABLE memories ADD COLUMN checksum TEXT;  -- SHA-256 of content
ALTER TABLE memories ADD COLUMN expires_at TIMESTAMP;  -- TTL support
```

### Audit Logging
```sql
CREATE TABLE audit_log (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT NOT NULL,
    api_key_id TEXT,
    action TEXT NOT NULL,  -- 'store', 'recall', 'forget', 'key_created', 'key_revoked'
    resource_id TEXT,  -- memory_id or key_id
    ip_address TEXT,
    user_agent TEXT,
    request_body_hash TEXT,  -- Don't log actual content, just hash
    success BOOLEAN,
    error_message TEXT
);

CREATE INDEX idx_audit_user ON audit_log(user_id, timestamp);
CREATE INDEX idx_audit_action ON audit_log(action, timestamp);
```

---

## 7. Revised Implementation Plan

### Phase 1: Authentication (4 hours)
- API key generation, storage, validation
- All endpoints require valid key
- Per-user memory isolation enforced

### Phase 2: Rate Limiting (2 hours)
- slowapi integration
- Per-endpoint limits
- Rate limit by API key (not just IP)

### Phase 3: Memory Protection (4 hours) ⚠️ NEW
- Input sanitization before store
- Trust scoring
- Provenance tracking (source, session, checksum)
- TTL support for memory expiration

### Phase 4: Audit & Monitoring (2 hours)
- Audit log table
- Log all memory operations
- Alert on suspicious patterns

**Total: ~12 hours (was 8 hours)**

---

## References
- [FastAPI Security Docs](https://fastapi.tiangolo.com/tutorial/security/)
- [SlowAPI GitHub](https://github.com/laurentS/slowapi)
- [API Key Best Practices - Medium](https://medium.com/@agusabdulrahman/fastapi-api-key-authentication-complete-guide-to-securing-your-api-44345f5c9bec)
- [MINJA Attack Paper](https://arxiv.org/abs/2503.03704) - Memory Injection Attack (95% success rate)
- [Mem0 Security Blog](https://mem0.ai/blog/ai-memory-security-best-practices)
- [AgentPoison Paper](https://arxiv.org/abs/2407.12784) - Backdoor injection
- [Unit 42 Memory Poisoning](https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/)

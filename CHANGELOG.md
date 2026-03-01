# Changelog

All notable changes to Remembra will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-03-01

### Added
- **API Key Authentication** - Secure access control for all memory operations
  - Generate API keys with `rem_` prefix and 256-bit entropy
  - Keys hashed with bcrypt before storage (never stored in plaintext)
  - Per-user memory isolation enforced via API key
  - Master key support for admin operations
  - Key management endpoints: POST/GET/DELETE /api/v1/keys
  
- **Rate Limiting** - Protection against abuse and DoS
  - Per-endpoint limits (store: 30/min, recall: 60/min, forget: 10/min)
  - Rate limit by API key (not just IP)
  - Uses `slowapi` with in-memory or Redis backend
  - Configurable via environment variables
  
- **Memory Protection Layer** - Defense against prompt injection (MINJA)
  - Input sanitization before storage
  - Trust scoring based on suspicious pattern detection
  - Patterns detected: instruction override, role manipulation, delimiter injection
  - SHA-256 checksums for integrity verification
  - Content provenance tracking (source, trust_score, checksum)
  
- **Audit Logging** - Security monitoring and compliance
  - Logs all memory operations (store, recall, forget)
  - Logs authentication events (key created, revoked, failed attempts)
  - Includes: timestamp, user_id, key_id, action, resource_id, IP, success
  - Never logs actual memory content or full API keys
  
- New `auth/` module with:
  - `keys.py` - API key generation, hashing, validation
  - `middleware.py` - FastAPI dependencies for authentication
  
- New `security/` module with:
  - `sanitizer.py` - Content sanitization and trust scoring
  - `audit.py` - Security audit logging
  
- Database schema updates:
  - `api_keys` table for key storage
  - `audit_log` table for security events
  - Memory provenance columns: source, trust_score, checksum

### Configuration
- `REMEMBRA_AUTH_ENABLED` - Enable API key authentication (default: true)
- `REMEMBRA_AUTH_MASTER_KEY` - Master key for admin operations
- `REMEMBRA_RATE_LIMIT_ENABLED` - Enable rate limiting (default: true)
- `REMEMBRA_RATE_LIMIT_STORAGE` - Rate limit backend: "memory" or "redis://..."
- `REMEMBRA_SANITIZATION_ENABLED` - Enable input sanitization (default: true)
- `REMEMBRA_TRUST_SCORE_THRESHOLD` - Suspicious content threshold (default: 0.5)

### Security
- OWASP API Security Top 10 addressed
- Defense-in-depth against memory injection attacks (MINJA - 95% success rate in research)
- Cross-user memory access blocked via API key scoping
- user_id in requests overridden by authenticated user (prevents spoofing)

### Dependencies
- Added `bcrypt>=4.0.0` for key hashing
- Added `slowapi>=0.1.9` for rate limiting

## [0.4.0] - 2026-03-01

### Added
- **Hybrid Search** - Combines semantic (vector) and keyword (BM25) matching
  - **SQLite FTS5** integration for persistent full-text indexing
  - In-memory BM25 fallback when FTS5 unavailable
  - Score normalization with min-max scaling
  - Configurable alpha weight for keyword/semantic balance
  - Reciprocal Rank Fusion (RRF) option for rank-based fusion
  
- **CrossEncoder Reranking** - Optional post-retrieval reranking (NEW)
  - Uses `sentence-transformers` CrossEncoder models
  - Reduces hallucinations by ~35% (per Databricks research)
  - Default model: `cross-encoder/ms-marco-MiniLM-L-6-v2` (local, free)
  - Graceful degradation when model unavailable
  - Blends rerank scores with original scores
  
- **Graph-Aware Retrieval** - Uses entity relationships for smarter recall
  - Traverses entity graph to find related memories
  - Alias matching ("Mr. Kim" → "David Kim")
  - Configurable traversal depth (default: 2 hops)
  - Entity neighborhood expansion
  
- **Context Window Optimization** - Smart truncation for LLM context limits
  - **tiktoken integration** for accurate token counting (NEW)
  - Character-based fallback estimation
  - `max_tokens` parameter on `recall()` endpoint
  - Relevance-aware truncation at sentence boundaries
  
- **Advanced Relevance Ranking** - Multi-signal scoring
  - Recency boost (newer memories score higher)
  - Entity match boost (entities in query)
  - Keyword match boost (from BM25)
  - Diversity-aware reranking (MMR) to reduce redundancy
  - Configurable weights via environment variables
  
- New `retrieval/` module with:
  - `hybrid.py` - BM25Index, HybridSearcher
  - `graph.py` - GraphRetriever for entity traversal
  - `context.py` - ContextOptimizer with tiktoken
  - `ranking.py` - RelevanceRanker with configurable boosts
  - `reranker.py` - CrossEncoderReranker for quality improvement (NEW)
  
- FTS5 full-text search table in SQLite (`memories_fts`)
- Comprehensive tests for all retrieval features

### Configuration
- `REMEMBRA_HYBRID_SEARCH_ENABLED` - Toggle hybrid search (default: true)
- `REMEMBRA_HYBRID_ALPHA` - Keyword weight 0-1 (default: 0.4)
- `REMEMBRA_RERANK_ENABLED` - Toggle CrossEncoder reranking (default: false)
- `REMEMBRA_RERANK_MODEL` - CrossEncoder model name
- `REMEMBRA_DEFAULT_MAX_TOKENS` - Max context tokens (default: 4000)
- `REMEMBRA_GRAPH_RETRIEVAL_ENABLED` - Toggle graph traversal (default: true)
- `REMEMBRA_GRAPH_TRAVERSAL_DEPTH` - Entity graph depth (default: 2)
- `REMEMBRA_RANKING_SEMANTIC_WEIGHT` - Ranking semantic weight (default: 0.6)
- `REMEMBRA_RANKING_RECENCY_WEIGHT` - Ranking recency weight (default: 0.15)
- `REMEMBRA_RANKING_ENTITY_WEIGHT` - Ranking entity weight (default: 0.15)
- `REMEMBRA_RANKING_KEYWORD_WEIGHT` - Ranking keyword weight (default: 0.1)
- `REMEMBRA_RANKING_RECENCY_DECAY_DAYS` - Recency half-life (default: 30)

### Changed
- `recall()` now uses advanced retrieval pipeline by default
- `RecallRequest` accepts `max_tokens`, `enable_hybrid`, `enable_rerank` params
- `store()` now indexes memories in FTS5 for keyword search
- Improved relevance scoring considers multiple signals
- Context output optimized for LLM consumption

### Dependencies
- Added `tiktoken>=0.7.0` to server extras
- Added `sentence-transformers>=2.5.0` as optional `rerank` extra

## [0.3.0] - 2026-03-01

### Added
- **Entity Extraction** - LLM extracts PERSON, ORG, LOCATION entities from memories
- **Entity Matching** - Resolves aliases ("Mr. Kim" → "David Kim", "NYC" → "New York City")
- **Alias Management** - Automatic alias tracking and resolution
- **Relationship Storage** - Stores entity relationships (WORKS_AT, SPOUSE_OF, KNOWS, etc.)
- **Memory-Entity Links** - Bidirectional links between memories and entities
- **Entity-Aware Recall** - Find memories via entity graph traversal
- New `entities.py` module for entity extraction
- New `matcher.py` module for entity resolution
- Entity resolution documentation

### Changed
- Memory storage now extracts and links entities automatically
- Recall considers entity relationships for improved relevance

## [0.2.0] - 2026-03-01

### Added
- **LLM-powered fact extraction** - Transforms messy text into clean atomic facts
- **Memory consolidation** - ADD/UPDATE/DELETE/NOOP logic prevents duplicates
- **Smart merging** - Updates preserve history (e.g., "VP of Sales (promoted from Director)")
- New extraction module with configurable LLM backend
- New consolidation module for memory conflict resolution

### Changed
- `store()` now uses intelligent extraction by default
- Improved recall relevance with semantic understanding
- Default threshold lowered to 0.40 for better recall

### Configuration
- `REMEMBRA_SMART_EXTRACTION_ENABLED` - Toggle LLM extraction (default: true)
- `REMEMBRA_EXTRACTION_MODEL` - Model for extraction (default: gpt-4o-mini)
- `REMEMBRA_CONSOLIDATION_THRESHOLD` - Similarity threshold for consolidation

## [0.1.0] - 2026-03-01

### Added
- Initial release of Remembra
- Python SDK with `Memory` client class
- REST API with FastAPI
- `store()` - Store memories with automatic fact extraction
- `recall()` - Semantic search across memories
- `forget()` - GDPR-compliant deletion
- Qdrant vector store integration
- SQLite metadata storage
- Embedding support for OpenAI, Ollama, and Cohere
- Docker and docker-compose setup
- Comprehensive test suite

### Notes
- This is an alpha release - API may change
- Entity resolution coming in v0.2.0
- LLM-powered extraction coming in v0.2.0

## [0.4.1] - 2026-03-01

### Fixed
- API recall endpoint signature (removed duplicate max_tokens argument)
- Hybrid search fallback path (correct method signature for fusion)
- Test compatibility with HybridSearchConfig API

### Added
- RELEASE-CHECKLIST.md - mandatory pre-deploy verification

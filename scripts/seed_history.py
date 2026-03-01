#!/usr/bin/env python3
"""
Seed Remembra with its own build history.
Dogfooding: The memory system remembers its own development.
"""

import sys
sys.path.insert(0, "/Users/dolphy/Projects/remembra/src")

from remembra import Memory

# Initialize memory for the Remembra project itself
# Using general_agent to keep all memories in one namespace
memory = Memory(
    base_url="http://localhost:8787",
    user_id="general_agent",
    project="clawdbot_main"
)

# Historical context to seed
BUILD_HISTORY = [
    # Week 1-3: Foundation
    {
        "content": "Remembra v0.1.0 released on 2026-03-01. Initial release with Python SDK, REST API (FastAPI), store/recall/forget operations, Qdrant vector store, SQLite metadata, embedding support for OpenAI/Ollama/Cohere, Docker setup. This covered Weeks 1-3 of the build plan.",
        "metadata": {"week": "1-3", "version": "0.1.0", "phase": "Foundation"}
    },
    # Week 4: Smart Extraction
    {
        "content": "Remembra v0.2.0 released on 2026-03-01. Week 4 build: LLM-powered fact extraction, memory consolidation with ADD/UPDATE/DELETE/NOOP logic, smart merging that preserves history. Default extraction model is gpt-4o-mini.",
        "metadata": {"week": "4", "version": "0.2.0", "phase": "Intelligence"}
    },
    # Week 5: Entity Resolution
    {
        "content": "Remembra v0.3.0 released on 2026-03-01. Week 5 build: Entity extraction (PERSON, ORG, LOCATION), entity matching and alias resolution (Mr. Kim → David Kim), relationship storage (WORKS_AT, SPOUSE_OF), memory-entity bidirectional links, entity-aware recall.",
        "metadata": {"week": "5", "version": "0.3.0", "phase": "Intelligence"}
    },
    # Week 6: Advanced Retrieval (deployed twice)
    {
        "content": "Remembra v0.4.0 released on 2026-03-01. Week 6 build: Hybrid search (semantic + BM25 keyword), SQLite FTS5 integration, CrossEncoder reranking, graph-aware retrieval, context window optimization with tiktoken, advanced relevance ranking with recency/entity/keyword boosts.",
        "metadata": {"week": "6", "version": "0.4.0", "phase": "Intelligence"}
    },
    {
        "content": "Remembra v0.4.1 hotfix released on 2026-03-01. Week 6 had to deploy TWICE due to API recall endpoint signature bug and hybrid search fallback path issues. Created RELEASE-CHECKLIST.md to prevent future issues.",
        "metadata": {"week": "6", "version": "0.4.1", "phase": "Intelligence", "type": "hotfix"}
    },
    # Week 7: Security
    {
        "content": "Remembra v0.5.0 released on 2026-03-01. Week 7 build: API key authentication with bcrypt hashing, rate limiting with slowapi, memory protection against prompt injection (MINJA), input sanitization and trust scoring, audit logging for compliance. Auth currently disabled for local dev.",
        "metadata": {"week": "7", "version": "0.5.0", "phase": "Security"}
    },
    # Current state
    {
        "content": "Remembra is currently at Week 7 of the 12-week MVP build plan. Next up is Week 8: Temporal Features (timestamps, TTL, memory decay, historical queries). Target MVP completion is Week 12 with Docker self-host + beta users.",
        "metadata": {"week": "7", "version": "0.5.0", "status": "current"}
    },
    # Key decisions
    {
        "content": "Key Remembra architecture decisions: Python with FastAPI, Qdrant for vectors, SQLite for metadata (PostgreSQL for prod), model-agnostic embeddings (OpenAI/Cohere/Ollama), React + Tailwind dashboard planned for Week 9-10.",
        "metadata": {"type": "architecture", "phase": "all"}
    },
    # Lessons learned
    {
        "content": "Lesson learned Week 6: Always run full test suite before deploy. The v0.4.1 hotfix was needed because API signature changes broke recall endpoint. Created RELEASE-CHECKLIST.md as mandatory pre-deploy verification.",
        "metadata": {"type": "lesson", "week": "6"}
    },
]

def seed():
    """Seed all historical context."""
    print("🌱 Seeding Remembra with build history...\n")
    
    for i, item in enumerate(BUILD_HISTORY, 1):
        result = memory.store(item["content"], metadata=item["metadata"])
        print(f"  [{i}/{len(BUILD_HISTORY)}] Stored: {item['metadata'].get('version', item['metadata'].get('type', 'info'))}")
        print(f"       Facts: {result.extracted_facts[:2]}...")
    
    print(f"\n✅ Seeded {len(BUILD_HISTORY)} historical memories")
    print("\nTest recall:")
    result = memory.recall("What week are we on and what was deployed twice?")
    print(f"  {result.context}")

if __name__ == "__main__":
    seed()

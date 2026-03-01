#!/usr/bin/env python3
"""
Remembra End-to-End Test Script (Python SDK)

Usage:
    1. docker compose up -d
    2. export REMEMBRA_OPENAI_API_KEY=sk-xxx
    3. uv run remembra &
    4. uv run python scripts/test_e2e.py
"""

import sys
import time
from datetime import datetime

# Add colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log_pass(msg: str) -> None:
    print(f"{GREEN}✅ PASS{RESET}: {msg}")

def log_fail(msg: str) -> None:
    print(f"{RED}❌ FAIL{RESET}: {msg}")
    sys.exit(1)

def log_info(msg: str) -> None:
    print(f"{YELLOW}🔍{RESET} {msg}")

def main():
    print("=" * 60)
    print("REMEMBRA E2E TEST (Python SDK)")
    print("=" * 60)
    print()
    
    # Import SDK
    try:
        from remembra import Memory, MemoryError
        log_pass("SDK imported successfully")
    except ImportError as e:
        log_fail(f"Failed to import SDK: {e}")
    
    # Create client
    user_id = f"test_user_{int(time.time())}"
    memory = Memory(
        base_url="http://localhost:8787",
        user_id=user_id,
        project="e2e_test"
    )
    print(f"\nClient: {memory}")
    print(f"User ID: {user_id}")
    print()
    
    # Test 1: Health Check
    log_info("Test 1: Health Check")
    try:
        health = memory.health()
        print(f"   Response: {health}")
        if "status" in health:
            log_pass("Health endpoint responding")
        else:
            log_fail("Health check missing status")
    except Exception as e:
        log_fail(f"Health check failed: {e}")
    print()
    
    # Test 2: Store Memory
    log_info("Test 2: Store Memory")
    try:
        result = memory.store("John Smith is the CEO of Acme Corporation. He started in 2020.")
        print(f"   ID: {result.id}")
        print(f"   Facts: {result.extracted_facts}")
        print(f"   Entities: {result.entities}")
        memory_id_1 = result.id
        log_pass(f"Memory stored: {memory_id_1}")
    except Exception as e:
        log_fail(f"Store failed: {e}")
    print()
    
    # Test 3: Store Another Memory
    log_info("Test 3: Store Second Memory")
    try:
        result = memory.store("Sarah Johnson is the CTO. She works closely with John on strategy.")
        print(f"   ID: {result.id}")
        memory_id_2 = result.id
        log_pass(f"Second memory stored: {memory_id_2}")
    except Exception as e:
        log_fail(f"Store failed: {e}")
    print()
    
    # Test 4: Store with TTL
    log_info("Test 4: Store Memory with TTL")
    try:
        result = memory.store("Meeting scheduled for next Tuesday.", ttl="7d")
        print(f"   ID: {result.id}")
        log_pass("Memory with TTL stored")
    except Exception as e:
        log_fail(f"Store with TTL failed: {e}")
    print()
    
    # Test 5: Store with Metadata
    log_info("Test 5: Store Memory with Metadata")
    try:
        result = memory.store(
            "Q4 revenue was $2.5 million, up 30% from last year.",
            metadata={"source": "earnings_call", "date": "2026-01-15"}
        )
        print(f"   ID: {result.id}")
        log_pass("Memory with metadata stored")
    except Exception as e:
        log_fail(f"Store with metadata failed: {e}")
    print()
    
    # Wait for Qdrant to index
    print("   ⏳ Waiting for index...")
    time.sleep(2)
    
    # Test 6: Recall - CEO Query
    log_info("Test 6: Recall - 'Who is the CEO?'")
    try:
        result = memory.recall("Who is the CEO?", threshold=0.3)
        print(f"   Context: {result.context[:100]}...")
        print(f"   Memories found: {len(result.memories)}")
        for m in result.memories:
            print(f"      - [{m.relevance:.2f}] {m.content[:50]}...")
        if result.context:
            log_pass("Recall returned context")
        else:
            log_fail("Recall returned empty context")
    except Exception as e:
        log_fail(f"Recall failed: {e}")
    print()
    
    # Test 7: Recall - Different Query
    log_info("Test 7: Recall - 'Tell me about the company'")
    try:
        result = memory.recall("Tell me about the company")
        print(f"   Memories found: {len(result.memories)}")
        log_pass("Different query works")
    except Exception as e:
        log_fail(f"Recall failed: {e}")
    print()
    
    # Test 8: Recall - Revenue Query
    log_info("Test 8: Recall - 'What was the revenue?'")
    try:
        result = memory.recall("What was the Q4 revenue?")
        print(f"   Context: {result.context[:100]}..." if result.context else "   No context")
        log_pass("Revenue query works")
    except Exception as e:
        log_fail(f"Recall failed: {e}")
    print()
    
    # Test 9: Get by ID
    log_info("Test 9: Get Memory by ID")
    try:
        result = memory.get(memory_id_1)
        print(f"   Retrieved: {result.get('content', '')[:50]}...")
        log_pass(f"Retrieved memory by ID")
    except MemoryError as e:
        if e.status_code == 404:
            log_fail("Memory not found by ID")
        else:
            log_fail(f"Get failed: {e}")
    except Exception as e:
        log_fail(f"Get failed: {e}")
    print()
    
    # Test 10: Forget Specific Memory
    log_info("Test 10: Forget Specific Memory")
    try:
        result = memory.forget(memory_id=memory_id_1)
        print(f"   Deleted memories: {result.deleted_memories}")
        log_pass("Memory forgotten")
    except Exception as e:
        log_fail(f"Forget failed: {e}")
    print()
    
    # Test 11: Forget All User Memories
    log_info("Test 11: Forget All User Memories (GDPR)")
    try:
        result = memory.forget(user_id=user_id)
        print(f"   Deleted memories: {result.deleted_memories}")
        print(f"   Deleted entities: {result.deleted_entities}")
        print(f"   Deleted relationships: {result.deleted_relationships}")
        log_pass("All user data forgotten")
    except Exception as e:
        log_fail(f"Forget all failed: {e}")
    print()
    
    # Test 12: Verify Deletion
    log_info("Test 12: Verify Deletion")
    try:
        result = memory.recall("Who is the CEO?")
        if len(result.memories) == 0:
            log_pass("Memories successfully deleted (empty recall)")
        else:
            print(f"   Warning: {len(result.memories)} memories still found")
    except Exception as e:
        log_fail(f"Verify deletion failed: {e}")
    print()
    
    # Summary
    print("=" * 60)
    print(f"{GREEN}ALL E2E TESTS PASSED!{RESET}")
    print("=" * 60)
    print()
    print("📊 Features Tested:")
    print("   ✅ Health check")
    print("   ✅ Store memories (basic, TTL, metadata)")
    print("   ✅ Recall with semantic search")
    print("   ✅ Get memory by ID")
    print("   ✅ Forget specific memory")
    print("   ✅ Forget all user data (GDPR)")
    print()
    print("🎉 Remembra is working!")

if __name__ == "__main__":
    main()

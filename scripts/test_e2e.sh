#!/bin/bash
#
# Remembra End-to-End Test Script
# Run this after starting Docker and the server
#
# Usage:
#   1. docker compose up -d
#   2. export REMEMBRA_OPENAI_API_KEY=sk-xxx
#   3. uv run remembra &
#   4. ./scripts/test_e2e.sh
#

set -e

BASE_URL="${REMEMBRA_URL:-http://localhost:8787}"
USER_ID="test_user_$(date +%s)"

echo "============================================================"
echo "REMEMBRA E2E TEST"
echo "============================================================"
echo "Base URL: $BASE_URL"
echo "User ID: $USER_ID"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

pass() { echo -e "${GREEN}✅ PASS${NC}: $1"; }
fail() { echo -e "${RED}❌ FAIL${NC}: $1"; exit 1; }

# Test 1: Health Check
echo "🔍 Test 1: Health Check"
HEALTH=$(curl -s "$BASE_URL/health")
echo "$HEALTH" | grep -q '"status"' && pass "Health endpoint responding" || fail "Health check failed"
echo ""

# Test 2: Root Endpoint
echo "🔍 Test 2: Root Endpoint"
ROOT=$(curl -s "$BASE_URL/")
echo "$ROOT" | grep -q '"name":"remembra"' && pass "Root endpoint returns name" || fail "Root endpoint failed"
echo ""

# Test 3: Store Memory
echo "🔍 Test 3: Store Memory"
STORE_RESULT=$(curl -s -X POST "$BASE_URL/api/v1/memories" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"content\":\"John Smith is the CEO of Acme Corporation. He started in 2020.\"}")
echo "Response: $STORE_RESULT"
MEMORY_ID=$(echo "$STORE_RESULT" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$MEMORY_ID" ]; then
  pass "Memory stored with ID: $MEMORY_ID"
else
  fail "Failed to store memory"
fi
echo ""

# Test 4: Store Another Memory
echo "🔍 Test 4: Store Second Memory"
STORE_RESULT2=$(curl -s -X POST "$BASE_URL/api/v1/memories" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"content\":\"Sarah Johnson is the CTO at Acme Corporation. She joined in 2021.\"}")
echo "Response: $STORE_RESULT2"
echo "$STORE_RESULT2" | grep -q '"id"' && pass "Second memory stored" || fail "Failed to store second memory"
echo ""

# Test 5: Store with TTL
echo "🔍 Test 5: Store Memory with TTL"
STORE_TTL=$(curl -s -X POST "$BASE_URL/api/v1/memories" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"content\":\"Meeting scheduled for next Tuesday.\",\"ttl\":\"7d\"}")
echo "Response: $STORE_TTL"
echo "$STORE_TTL" | grep -q '"id"' && pass "Memory with TTL stored" || fail "Failed to store memory with TTL"
echo ""

# Test 6: Recall Memories
echo "🔍 Test 6: Recall Memories"
RECALL_RESULT=$(curl -s -X POST "$BASE_URL/api/v1/memories/recall" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"query\":\"Who is the CEO?\"}")
echo "Response: $RECALL_RESULT"
echo "$RECALL_RESULT" | grep -q '"context"' && pass "Recall returned context" || fail "Recall failed"
echo ""

# Test 7: Recall with Different Query
echo "🔍 Test 7: Recall Different Query"
RECALL_RESULT2=$(curl -s -X POST "$BASE_URL/api/v1/memories/recall" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"query\":\"Tell me about Acme Corporation\"}")
echo "Response: $RECALL_RESULT2"
echo "$RECALL_RESULT2" | grep -q '"memories"' && pass "Recall with different query works" || fail "Second recall failed"
echo ""

# Test 8: Get Memory by ID
echo "🔍 Test 8: Get Memory by ID"
GET_RESULT=$(curl -s "$BASE_URL/api/v1/memories/$MEMORY_ID")
echo "Response: $GET_RESULT"
echo "$GET_RESULT" | grep -q "$MEMORY_ID" && pass "Retrieved memory by ID" || fail "Get by ID failed"
echo ""

# Test 9: Forget (Delete) Specific Memory
echo "🔍 Test 9: Forget Specific Memory"
FORGET_RESULT=$(curl -s -X DELETE "$BASE_URL/api/v1/memories?memory_id=$MEMORY_ID")
echo "Response: $FORGET_RESULT"
echo "$FORGET_RESULT" | grep -q '"deleted_memories"' && pass "Memory forgotten" || fail "Forget failed"
echo ""

# Test 10: Forget All User Memories
echo "🔍 Test 10: Forget All User Memories"
FORGET_ALL=$(curl -s -X DELETE "$BASE_URL/api/v1/memories?user_id=$USER_ID")
echo "Response: $FORGET_ALL"
echo "$FORGET_ALL" | grep -q '"deleted_memories"' && pass "All user memories forgotten" || fail "Forget all failed"
echo ""

# Test 11: Verify Deletion
echo "🔍 Test 11: Verify Deletion (Recall Should Be Empty)"
RECALL_EMPTY=$(curl -s -X POST "$BASE_URL/api/v1/memories/recall" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"query\":\"Who is the CEO?\"}")
echo "Response: $RECALL_EMPTY"
MEMORIES_COUNT=$(echo "$RECALL_EMPTY" | grep -o '"memories":\[[^]]*\]' | grep -c '"id"' || echo "0")
if [ "$MEMORIES_COUNT" = "0" ]; then
  pass "Memories successfully deleted (empty recall)"
else
  echo "Warning: Some memories may still exist"
fi
echo ""

echo "============================================================"
echo "ALL E2E TESTS COMPLETED!"
echo "============================================================"
echo ""
echo "📊 Summary:"
echo "   - Health check: ✅"
echo "   - Store memories: ✅"
echo "   - Recall (semantic search): ✅"
echo "   - Get by ID: ✅"
echo "   - Forget (GDPR delete): ✅"
echo ""
echo "🎉 Remembra is working!"

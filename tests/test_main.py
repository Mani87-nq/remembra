"""Smoke tests for the FastAPI application skeleton."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from remembra.main import app
from remembra.models.memory import RecallResponse, StoreResponse
from remembra.services.memory import MemoryService


@pytest.fixture()
def mock_memory_service():
    """Create a mock memory service for testing."""
    service = MagicMock(spec=MemoryService)
    
    # Mock store
    service.store = AsyncMock(return_value=StoreResponse(
        id="test-memory-id",
        extracted_facts=["John is the CTO at Acme Corp."],
        entities=[],
    ))
    
    # Mock recall
    service.recall = AsyncMock(return_value=RecallResponse(
        context="John is the CTO at Acme Corp.",
        memories=[],
        entities=[],
    ))
    
    # Mock forget
    from remembra.models.memory import ForgetResponse
    service.forget = AsyncMock(return_value=ForgetResponse(
        deleted_memories=0,
        deleted_entities=0,
        deleted_relationships=0,
    ))
    
    return service


@pytest.fixture()
async def client(mock_memory_service):
    """Test client with mocked services."""
    # Inject mock service into app state
    app.state.memory_service = mock_memory_service
    
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


async def test_root(client: AsyncClient) -> None:
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "remembra"
    assert "version" in data


async def test_docs_available(client: AsyncClient) -> None:
    r = await client.get("/docs")
    assert r.status_code == 200


async def test_openapi_schema(client: AsyncClient) -> None:
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert schema["info"]["title"] == "Remembra"


async def test_store_memory_returns_201(client: AsyncClient, mock_memory_service) -> None:
    r = await client.post(
        "/api/v1/memories",
        json={"user_id": "test-user", "content": "John is the CTO at Acme Corp."},
    )
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["id"] == "test-memory-id"
    assert isinstance(data["extracted_facts"], list)
    assert isinstance(data["entities"], list)
    
    # Verify the service was called
    mock_memory_service.store.assert_called_once()


async def test_recall_memories(client: AsyncClient, mock_memory_service) -> None:
    r = await client.post(
        "/api/v1/memories/recall",
        json={"user_id": "test-user", "query": "Who is John?"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "context" in data
    assert "memories" in data
    assert "entities" in data
    
    # Verify the service was called
    mock_memory_service.recall.assert_called_once()


async def test_store_empty_content_rejected(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/memories",
        json={"user_id": "test-user", "content": "   "},
    )
    assert r.status_code == 422


async def test_forget_requires_filter(client: AsyncClient) -> None:
    r = await client.delete("/api/v1/memories")
    assert r.status_code == 422

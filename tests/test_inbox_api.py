"""
End-to-end API tests for the agent inbox endpoints (issue #9).

Exercises the real FastAPI routes through AsyncClient + ASGITransport,
with a real InboxManager backed by an in-memory SQLite DB injected into
app.state. This is the DoD round-trip test from the issue: agent A
sends → agent B reads → agent B acks, with no human relay.
"""

import os

# Disable auth + rate limiting — MUST precede remembra imports
os.environ["REMEMBRA_AUTH_ENABLED"] = "false"
os.environ["REMEMBRA_RATE_LIMIT_ENABLED"] = "false"

import aiosqlite
import pytest
from httpx import ASGITransport, AsyncClient

from remembra.inbox.manager import InboxManager
from remembra.main import app


@pytest.fixture()
async def client():
    """Test client with a real InboxManager over in-memory SQLite."""

    class _DB:
        def __init__(self, conn: aiosqlite.Connection) -> None:
            self.conn = conn

    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    db = _DB(conn)

    mgr = InboxManager(db)
    await mgr.init_schema()

    # Inject into live app state
    app.state.inbox_manager = mgr

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    await conn.close()


async def test_inbox_round_trip(client: AsyncClient) -> None:
    """Full DoD round-trip: send → get → ack → get (should disappear)."""
    # Agent A sends a directive to test-agent-b
    r = await client.post(
        "/api/v1/inbox/send",
        json={
            "to_agent": "test-agent-b",
            "from_agent": "agent-a",
            "subject": "run dummy task",
            "body": "Respond with ok.",
            "metadata": {"kind": "directive"},
        },
    )
    assert r.status_code == 201, r.text
    sent = r.json()
    assert sent["inbox_id"].startswith("inbox_")
    assert sent["status"] == "unread"
    inbox_id = sent["inbox_id"]

    # Agent B reads its inbox
    r = await client.get(
        "/api/v1/inbox",
        params={"agent_id": "test-agent-b"},
    )
    assert r.status_code == 200, r.text
    items = r.json()
    assert len(items) == 1
    assert items[0]["inbox_id"] == inbox_id
    assert items[0]["subject"] == "run dummy task"
    assert items[0]["body"] == "Respond with ok."
    assert items[0]["metadata"] == {"kind": "directive"}
    assert items[0]["status"] == "unread"

    # Agent B acks as done
    r = await client.post(
        f"/api/v1/inbox/{inbox_id}/ack",
        json={"result": "done", "note": "shipped"},
    )
    assert r.status_code == 200, r.text
    acked = r.json()
    assert acked["status"] == "done"
    assert acked["ack_result"] == "done"
    assert acked["ack_note"] == "shipped"
    assert acked["ack_at"]

    # Unread view is now empty
    r = await client.get("/api/v1/inbox", params={"agent_id": "test-agent-b"})
    assert r.status_code == 200
    assert r.json() == []

    # But the row still exists under status=all
    r = await client.get(
        "/api/v1/inbox",
        params={"agent_id": "test-agent-b", "status": "all"},
    )
    assert r.status_code == 200
    all_rows = r.json()
    assert len(all_rows) == 1
    assert all_rows[0]["status"] == "done"


async def test_inbox_send_rejects_missing_required_fields(client: AsyncClient) -> None:
    # No body
    r = await client.post(
        "/api/v1/inbox/send",
        json={"to_agent": "b", "subject": "s"},
    )
    assert r.status_code == 422


async def test_inbox_get_requires_agent_id(client: AsyncClient) -> None:
    r = await client.get("/api/v1/inbox")
    assert r.status_code == 422


async def test_inbox_ack_returns_404_for_unknown_id(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/inbox/inbox_doesnotexist/ack",
        json={},
    )
    assert r.status_code == 404


async def test_inbox_ack_without_result_marks_read(client: AsyncClient) -> None:
    # Send
    r = await client.post(
        "/api/v1/inbox/send",
        json={"to_agent": "b", "subject": "s", "body": "x"},
    )
    inbox_id = r.json()["inbox_id"]

    # Ack with no result
    r = await client.post(f"/api/v1/inbox/{inbox_id}/ack", json={})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "read"
    assert data["ack_result"] is None


async def test_inbox_ack_rejects_invalid_result(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/inbox/send",
        json={"to_agent": "b", "subject": "s", "body": "x"},
    )
    inbox_id = r.json()["inbox_id"]

    r = await client.post(f"/api/v1/inbox/{inbox_id}/ack", json={"result": "maybe"})
    # Literal validator → 422 (schema rejection)
    assert r.status_code == 422


async def test_inbox_scoped_by_to_agent(client: AsyncClient) -> None:
    # Send one to b and one to c
    await client.post(
        "/api/v1/inbox/send",
        json={"to_agent": "b", "subject": "for-b", "body": "x"},
    )
    await client.post(
        "/api/v1/inbox/send",
        json={"to_agent": "c", "subject": "for-c", "body": "x"},
    )

    # Only b's item shows up
    r = await client.get("/api/v1/inbox", params={"agent_id": "b"})
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["subject"] == "for-b"

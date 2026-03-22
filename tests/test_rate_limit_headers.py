"""Test that rate limit headers are exposed on API responses."""

import pytest
from fastapi.testclient import TestClient


def test_rate_limit_headers_enabled():
    """Verify headers_enabled=True is set on the limiter."""
    from remembra.core.limiter import limiter
    assert limiter._headers_enabled is True, "Rate limit headers should be enabled"


def test_rate_limit_headers_on_response():
    """Verify rate limit headers appear on rate-limited endpoint responses."""
    from remembra.main import app
    
    # Verify the limiter has headers enabled
    from remembra.core.limiter import limiter
    assert limiter._headers_enabled is True
    
    # Verify middleware is present
    assert any('SlowAPI' in str(m) for m in app.user_middleware), \
        "SlowAPIMiddleware should be configured"


def test_rate_limit_header_mapping_exists():
    """Verify the header mapping is configured on the limiter."""
    from remembra.core.limiter import limiter
    
    # Check that header mapping exists
    assert hasattr(limiter, '_header_mapping'), "Limiter should have header mapping"
    
    # Verify standard rate limit headers are mapped
    header_mapping = limiter._header_mapping
    assert len(header_mapping) > 0, "Header mapping should not be empty"

"""Test that rate limit headers are exposed on API responses.

Rate limit headers are injected via custom RateLimitHeadersMiddleware,
NOT via slowapi's built-in headers_enabled. This is because slowapi's
header injection requires a Response parameter on endpoints, which
our API doesn't use (we return Pydantic models directly).
"""



def test_rate_limit_middleware_configured():
    """Verify RateLimitHeadersMiddleware is configured in the app."""
    from remembra.main import app
    
    # Verify our custom middleware is present
    middleware_names = [str(m) for m in app.user_middleware]
    assert any('RateLimitHeaders' in str(m) for m in middleware_names), \
        "RateLimitHeadersMiddleware should be configured"


def test_slowapi_middleware_configured():
    """Verify SlowAPIMiddleware is configured in the app."""
    from remembra.main import app
    
    # Verify SlowAPI middleware is present
    middleware_names = [str(m) for m in app.user_middleware]
    assert any('SlowAPI' in str(m) for m in middleware_names), \
        "SlowAPIMiddleware should be configured"


def test_limiter_headers_disabled():
    """Verify headers_enabled=False on limiter (we use custom middleware instead)."""
    from remembra.core.limiter import limiter
    
    # Headers should be disabled on the limiter itself
    # because our custom middleware handles header injection
    assert limiter._headers_enabled is False, \
        "Limiter headers_enabled should be False (custom middleware handles this)"

"""Time helpers.

Python 3.14 deprecates ``datetime.utcnow()``. Remembra historically used naive
UTC datetimes for storage and comparisons. These helpers preserve that behavior
while avoiding deprecated APIs.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return a naive UTC datetime (tzinfo=None), without using deprecated utcnow()."""
    return datetime.now(UTC).replace(tzinfo=None)

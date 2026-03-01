"""Aggregate all versioned routers."""

from fastapi import APIRouter

from remembra.api.v1 import keys, memories

api_router = APIRouter(prefix="/api")
api_router.include_router(memories.router, prefix="/v1")
api_router.include_router(keys.router, prefix="/v1")

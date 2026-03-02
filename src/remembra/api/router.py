"""Aggregate all versioned routers."""

from fastapi import APIRouter

from remembra.api.v1 import cloud, debug, keys, memories, ingest, temporal, entities

api_router = APIRouter(prefix="/api")
api_router.include_router(memories.router, prefix="/v1")
api_router.include_router(keys.router, prefix="/v1")
api_router.include_router(ingest.router, prefix="/v1")
api_router.include_router(temporal.router, prefix="/v1")
api_router.include_router(entities.router, prefix="/v1")
api_router.include_router(cloud.router, prefix="/v1")
api_router.include_router(debug.router, prefix="/v1")

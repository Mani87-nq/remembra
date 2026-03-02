"""Aggregate all versioned routers."""

from fastapi import APIRouter

from remembra.api.v1 import admin, cloud, conflicts, debug, keys, memories, ingest, temporal, entities, transfer, webhooks

api_router = APIRouter(prefix="/api")
api_router.include_router(memories.router, prefix="/v1")
api_router.include_router(keys.router, prefix="/v1")
api_router.include_router(ingest.router, prefix="/v1")
api_router.include_router(temporal.router, prefix="/v1")
api_router.include_router(entities.router, prefix="/v1")
api_router.include_router(cloud.router, prefix="/v1")
api_router.include_router(debug.router, prefix="/v1")
api_router.include_router(webhooks.router, prefix="/v1")
api_router.include_router(conflicts.router, prefix="/v1")
api_router.include_router(admin.router, prefix="/v1")
api_router.include_router(transfer.router, prefix="/v1")

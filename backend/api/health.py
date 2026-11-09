from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict:
    """Return service health status."""
    return {"status": "ok", "version": "1.0.0"}

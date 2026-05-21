"""API router package for the target backend layout."""

from fastapi import APIRouter

from app.api import chunks, documents, graph


api_router = APIRouter()
api_router.include_router(documents.router)
api_router.include_router(chunks.router)
api_router.include_router(graph.router)

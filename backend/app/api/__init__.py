"""API router package for the target backend layout."""

from fastapi import APIRouter

from app.api import (
    chunks,
    documents,
    graph,
    learning_paths,
    mastery,
    modules,
    neo4j_runtime,
    practice,
    review,
    tutor,
    workspaces,
)


api_router = APIRouter()
api_router.include_router(documents.router)
api_router.include_router(chunks.router)
api_router.include_router(graph.router)
api_router.include_router(learning_paths.router)
api_router.include_router(modules.router)
api_router.include_router(practice.router)
api_router.include_router(mastery.router)
api_router.include_router(review.router)
api_router.include_router(tutor.router)
api_router.include_router(workspaces.router)
api_router.include_router(neo4j_runtime.router)

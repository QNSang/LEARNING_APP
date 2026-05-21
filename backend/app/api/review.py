"""Spaced repetition review API routes."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.db.repositories.mastery_repo import MasteryRepository, get_mastery_repository
from app.db.repositories.practice_repo import PracticeRepository, get_practice_repository
from app.models.mastery import UserNodeMasteryCreate
from app.models.practice import PracticeAttemptCreate
from app.models.review import ReviewQueue, ReviewQueueItem, ReviewResult, ReviewSubmission
from app.services.fsrs_service import FSRSService, get_fsrs_service


router = APIRouter(tags=["review"])


@router.get("/review/queue", response_model=ReviewQueue)
async def get_review_queue(
    user_id: UUID | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    mastery_repo: MasteryRepository = Depends(get_mastery_repository),
    practice_repo: PracticeRepository = Depends(get_practice_repository),
) -> ReviewQueue:
    """Return due review items, prioritizing weak and prerequisite-heavy nodes."""

    due_at = datetime.now(UTC)
    rows = mastery_repo.list_due(user_id=user_id, limit=limit, due_at=due_at)
    items: list[ReviewQueueItem] = []
    for row in rows:
        node = row.pop("knowledge_nodes", {}) or {}
        mastery = mastery_repo.get_by_user_and_node(
            user_id=user_id,
            node_id=UUID(str(row["node_id"])),
        )
        if mastery is None:
            continue

        fsrs_state = mastery.fsrs_state or {}
        prerequisite_count = int(fsrs_state.get("prerequisite_count", 0))
        weakness = 1.0 - mastery.mastery_score
        overdue = 0.0
        if mastery.next_review_at:
            overdue = max(0.0, (due_at - mastery.next_review_at).total_seconds() / 86400)
        priority = weakness * 10 + prerequisite_count * 0.75 + overdue

        items.append(
            ReviewQueueItem(
                mastery=mastery,
                practice_item=practice_repo.get_first_for_node(mastery.node_id),
                node_label=node.get("label") or "Untitled node",
                node_description=node.get("description"),
                prerequisite_count=prerequisite_count,
                priority=round(priority, 3),
            )
        )

    items.sort(key=lambda item: item.priority, reverse=True)
    return ReviewQueue(user_id=user_id, due_at=due_at, items=items)


@router.post("/review/attempts", response_model=ReviewResult)
async def submit_review_attempt(
    payload: ReviewSubmission,
    practice_repo: PracticeRepository = Depends(get_practice_repository),
    mastery_repo: MasteryRepository = Depends(get_mastery_repository),
    fsrs: FSRSService = Depends(get_fsrs_service),
) -> ReviewResult:
    """Save a review attempt and schedule the next review."""

    attempt = practice_repo.create_attempt(
        PracticeAttemptCreate(
            user_id=payload.user_id,
            practice_item_id=payload.practice_item_id,
            node_id=payload.node_id,
            answer=payload.answer,
            is_correct=payload.is_correct,
            score=payload.score,
            feedback=payload.feedback,
        )
    )
    existing = mastery_repo.get_by_user_and_node(
        user_id=payload.user_id,
        node_id=payload.node_id,
    )
    previous_score = existing.mastery_score if existing else 0.0
    fsrs_state = fsrs.schedule(
        score=payload.score,
        previous_state=existing.fsrs_state if existing else None,
    )
    mastery_score = fsrs.mastery_score(score=payload.score, previous_score=previous_score)
    mastery = mastery_repo.upsert(
        UserNodeMasteryCreate(
            user_id=payload.user_id,
            node_id=payload.node_id,
            mastery_score=mastery_score,
            status=fsrs.status_for(score=payload.score, mastery_score=mastery_score),
            last_reviewed_at=datetime.now(UTC),
            next_review_at=datetime.fromisoformat(fsrs_state["next_review_at"]),
            review_count=(existing.review_count if existing else 0) + 1,
            correct_count=(existing.correct_count if existing else 0)
            + (1 if payload.score >= 0.65 else 0),
            wrong_count=(existing.wrong_count if existing else 0)
            + (1 if payload.score < 0.65 else 0),
            fsrs_state=fsrs_state,
        )
    )
    return ReviewResult(attempt_id=attempt.id, mastery=mastery, fsrs_state=fsrs_state)

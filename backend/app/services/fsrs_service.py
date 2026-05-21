"""Spaced repetition scheduling service.

This implements a compact FSRS-inspired scheduler without adding a runtime
dependency. The state shape is intentionally transparent so it can be migrated
to a full FSRS library later without changing API contracts.
"""

from datetime import UTC, datetime, timedelta
from typing import Any


class FSRSService:
    """Compute the next review date from a graded recall attempt."""

    def schedule(
        self,
        *,
        score: float,
        previous_state: dict[str, Any] | None = None,
        reviewed_at: datetime | None = None,
    ) -> dict[str, Any]:
        now = reviewed_at or datetime.now(UTC)
        state = dict(previous_state or {})
        stability = float(state.get("stability", 0.0))
        difficulty = float(state.get("difficulty", 5.0))
        reps = int(state.get("reps", 0)) + 1
        lapses = int(state.get("lapses", 0))

        rating = self._score_to_rating(score)
        if rating <= 1:
            stability = 0.5
            difficulty = min(10.0, difficulty + 1.2)
            lapses += 1
        else:
            stability_gain = {2: 1.6, 3: 2.5, 4: 3.4}[rating]
            stability = max(1.0, stability * stability_gain if stability else stability_gain)
            difficulty = max(1.0, difficulty - (rating - 2) * 0.45)

        interval_days = self._interval_days(rating, stability, reps)
        next_review_at = now + timedelta(days=interval_days)

        return {
            "algorithm": "fsrs-lite",
            "rating": rating,
            "stability": round(stability, 3),
            "difficulty": round(difficulty, 3),
            "reps": reps,
            "lapses": lapses,
            "last_score": round(score, 3),
            "last_reviewed_at": now.isoformat(),
            "next_review_at": next_review_at.isoformat(),
            "interval_days": interval_days,
        }

    def mastery_score(self, *, score: float, previous_score: float) -> float:
        weighted = previous_score * 0.65 + score * 0.35
        if score < 0.4:
            weighted -= 0.12
        return min(1.0, max(0.0, weighted))

    def status_for(self, *, score: float, mastery_score: float) -> str:
        if score < 0.4:
            return "weak"
        if mastery_score >= 0.85:
            return "mastered"
        if mastery_score >= 0.55:
            return "review"
        return "learning"

    def _score_to_rating(self, score: float) -> int:
        if score < 0.4:
            return 1
        if score < 0.65:
            return 2
        if score < 0.9:
            return 3
        return 4

    def _interval_days(self, rating: int, stability: float, reps: int) -> int:
        if rating <= 1:
            return 1
        if reps <= 1:
            return 1 if rating == 2 else 2
        return max(1, min(365, round(stability)))


def get_fsrs_service() -> FSRSService:
    return FSRSService()

-- Phase 6: spaced repetition scheduling support.

ALTER TABLE user_node_mastery
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS fsrs_state JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_user_node_mastery_status
  ON user_node_mastery(status);

CREATE INDEX IF NOT EXISTS idx_user_node_mastery_due_priority
  ON user_node_mastery(user_id, next_review_at, status);

CREATE INDEX IF NOT EXISTS idx_practice_attempts_created_at
  ON practice_attempts(created_at);

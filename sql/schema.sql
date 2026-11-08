CREATE TABLE IF NOT EXISTS enriched_stories (
    story_id BIGINT PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT,
    author TEXT,
    score INTEGER,
    story_created_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB NOT NULL,
    topic TEXT NOT NULL,
    model_name TEXT NOT NULL,
    classified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_enriched_stories_created_at
    ON enriched_stories (story_created_at DESC);

CREATE INDEX IF NOT EXISTS idx_enriched_stories_topic
    ON enriched_stories (topic);
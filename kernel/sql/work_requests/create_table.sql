CREATE TABLE IF NOT EXISTS work_requests (
    work_request_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    source TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    thread_id TEXT,
    user_id TEXT,
    intents TEXT NOT NULL,
    task_ids TEXT NOT NULL,
    artifact_ids TEXT NOT NULL,
    synthesis_result TEXT,
    prior_context_ids TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

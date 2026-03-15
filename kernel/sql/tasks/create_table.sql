CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    subject TEXT NOT NULL,
    outcome TEXT,
    domain TEXT NOT NULL,
    created_by TEXT NOT NULL,
    owner_worker TEXT,
    priority INTEGER NOT NULL,
    status TEXT NOT NULL,
    expected_outputs TEXT NOT NULL,
    parent_task_id TEXT,
    dependencies TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    artifacts TEXT NOT NULL,
    thread_id TEXT
);
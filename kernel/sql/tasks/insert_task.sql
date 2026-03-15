INSERT INTO tasks (
    task_id,
    action,
    subject,
    outcome,
    domain,
    created_by,
    owner_worker,
    priority,
    status,
    expected_outputs,
    parent_task_id,
    dependencies,
    created_at,
    updated_at,
    artifacts,
    thread_id
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
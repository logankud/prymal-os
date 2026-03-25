UPDATE tasks
SET
    action = ?,
    subject = ?,
    outcome = ?,
    domain = ?,
    created_by = ?,
    owner_worker = ?,
    priority = ?,
    status = ?,
    expected_outputs = ?,
    expected_token_count = ?,
    due_date = ?,
    dependency_str = ?,
    parent_task_id = ?,
    dependencies = ?,
    created_at = ?,
    updated_at = ?,
    artifacts = ?,
    thread_id = ?,
    work_request_id = ?,
    intent_index = ?
WHERE task_id = ?;

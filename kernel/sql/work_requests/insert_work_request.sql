INSERT INTO work_requests (
    work_request_id, status, source, raw_text, thread_id, user_id,
    intents, task_ids, artifact_ids, synthesis_result, prior_context_ids,
    created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);

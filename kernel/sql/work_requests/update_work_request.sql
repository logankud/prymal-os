UPDATE work_requests SET
    status = ?,
    task_ids = ?,
    artifact_ids = ?,
    synthesis_result = ?,
    updated_at = ?
WHERE work_request_id = ?;

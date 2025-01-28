CREATE TABLE threads (
    thread_id SERIAL PRIMARY KEY, -- Auto-incrementing ID
    content JSONB NOT NULL,       -- Langgraph checkpointer JSONB format
    update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- current timestamp
);

INSERT INTO threads (content) VALUES
('{"checkpointer_id": 1, "status": "completed", "result": "Thread analysis complete."}'),
('{"checkpointer_id": 2, "status": "in_progress", "result": "Processing node relationships."}'),
('{"checkpointer_id": 3, "status": "failed", "error": "Missing data at step 4."}');
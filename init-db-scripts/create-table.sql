CREATE TABLE conversation_state (
    thread_id VARCHAR(255) PRIMARY KEY,
    state_data JSON NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
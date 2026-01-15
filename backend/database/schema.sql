-- Schemas table
CREATE TABLE IF NOT EXISTS schemas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    definition TEXT NOT NULL,  -- JSON string of Pydantic model definition
    is_template BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processing jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- 'image' or 'pdf'
    provider TEXT NOT NULL,    -- 'nebius', 'openrouter', 'gemini'
    model TEXT NOT NULL,
    schema_id INTEGER,
    schema_name TEXT,
    status TEXT NOT NULL,      -- 'pending', 'processing', 'success', 'error'
    result TEXT,               -- JSON string of extracted data
    error_message TEXT,
    processing_time_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (schema_id) REFERENCES schemas(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_provider ON processing_jobs(provider);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON processing_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_schemas_is_template ON schemas(is_template);

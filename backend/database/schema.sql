-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

-- Uploaded files table
CREATE TABLE IF NOT EXISTS uploaded_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT NOT NULL UNIQUE,
    original_filename TEXT NOT NULL,
    file_extension TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    user_id INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
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
    metadata TEXT,             -- JSON string of job metadata (e.g. classifier/debug info)
    error_message TEXT,
    processing_time_seconds REAL,
    processing_method TEXT DEFAULT 'vision',  -- 'vision' or 'text'
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    estimated_cost REAL,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (schema_id) REFERENCES schemas(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Benchmark runs table
CREATE TABLE IF NOT EXISTS benchmark_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    sample_count INTEGER NOT NULL,
    overall_accuracy REAL,
    avg_latency REAL,
    total_cost REAL,
    total_prompt_tokens INTEGER,
    total_completion_tokens INTEGER,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Benchmark results table
CREATE TABLE IF NOT EXISTS benchmark_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    sample_index INTEGER NOT NULL,
    file_path TEXT,
    accuracy_score REAL,
    latency REAL,
    cost REAL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    expected_json TEXT,
    actual_json TEXT,
    field_scores TEXT,
    error_message TEXT,
    FOREIGN KEY (run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_provider ON processing_jobs(provider);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON processing_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_processing_method ON processing_jobs(processing_method);
CREATE INDEX IF NOT EXISTS idx_schemas_is_template ON schemas(is_template);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_file_id ON uploaded_files(file_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_user_id ON uploaded_files(user_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_dataset ON benchmark_runs(dataset);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_provider ON benchmark_runs(provider);
CREATE INDEX IF NOT EXISTS idx_benchmark_results_run_id ON benchmark_results(run_id);

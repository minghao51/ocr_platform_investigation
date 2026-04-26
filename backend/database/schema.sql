-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    daily_requests INTEGER DEFAULT 0,
    last_request_date TEXT,
    is_limited BOOLEAN DEFAULT 0,
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
    guest_token TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Processing jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- 'image' or 'pdf'
    provider TEXT NOT NULL,    -- 'openrouter', 'gemini', 'litellm', 'docling-local'
    model TEXT NOT NULL,
    schema_id INTEGER,
    schema_name TEXT,
    status TEXT NOT NULL,      -- 'pending', 'processing', 'success', 'error'
    result TEXT,               -- JSON string of extracted data
    metadata TEXT,             -- JSON string of job metadata (e.g. classifier/debug info)
    error_message TEXT,
    processing_time_seconds REAL,
    processing_method TEXT DEFAULT 'vision',  -- 'vision' or 'text'
    quality_score REAL,
    quality_checks TEXT,             -- JSON string of quality gate results
    preprocessing_applied TEXT,      -- JSON string of preprocessing operations
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    estimated_cost REAL,
    document_type TEXT,
    correction_status TEXT DEFAULT 'uncorrected',
    user_id INTEGER,
    guest_token TEXT,
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

-- Schema suggestion drafts generated from uploaded documents
CREATE TABLE IF NOT EXISTS schema_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_ids TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    document_type TEXT,
    draft_name TEXT,
    schema_definition TEXT NOT NULL,
    field_descriptions TEXT,
    rationale TEXT,
    confidence REAL,
    status TEXT DEFAULT 'draft',
    created_by_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Human-in-the-loop corrections for processing jobs
CREATE TABLE IF NOT EXISTS job_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    original_result TEXT NOT NULL,
    corrected_result TEXT NOT NULL,
    diff_summary TEXT,
    feedback_tags TEXT,
    notes TEXT,
    reviewer_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES processing_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Prompt/routing learning summaries derived from accepted corrections
CREATE TABLE IF NOT EXISTS prompt_learning_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_name TEXT,
    provider TEXT,
    model TEXT,
    processing_method TEXT,
    entry_type TEXT NOT NULL,
    content TEXT NOT NULL,
    source_correction_count INTEGER DEFAULT 0,
    last_correction_id INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (last_correction_id) REFERENCES job_corrections(id) ON DELETE SET NULL
);

-- Durable queue for background OCR processing jobs
CREATE TABLE IF NOT EXISTS job_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL UNIQUE,
    task_type TEXT NOT NULL,          -- 'processing' | 'text'
    file_path TEXT NOT NULL,
    payload TEXT,                     -- JSON-encoded kwargs for worker
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'processing' | 'completed' | 'failed'
    attempts INTEGER NOT NULL DEFAULT 0,
    worker_id TEXT,
    locked_at TIMESTAMP,
    last_error TEXT,
    run_after TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES processing_jobs(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_provider ON processing_jobs(provider);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON processing_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_processing_method ON processing_jobs(processing_method);
CREATE INDEX IF NOT EXISTS idx_jobs_guest_token ON processing_jobs(guest_token);
CREATE INDEX IF NOT EXISTS idx_jobs_document_type ON processing_jobs(document_type);
CREATE INDEX IF NOT EXISTS idx_jobs_correction_status ON processing_jobs(correction_status);
CREATE INDEX IF NOT EXISTS idx_schemas_is_template ON schemas(is_template);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_file_id ON uploaded_files(file_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_user_id ON uploaded_files(user_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_guest_token ON uploaded_files(guest_token);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_dataset ON benchmark_runs(dataset);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_provider ON benchmark_runs(provider);
CREATE INDEX IF NOT EXISTS idx_benchmark_results_run_id ON benchmark_results(run_id);
CREATE INDEX IF NOT EXISTS idx_schema_suggestions_created_by ON schema_suggestions(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_job_corrections_job_id ON job_corrections(job_id);
CREATE INDEX IF NOT EXISTS idx_prompt_learning_schema_name ON prompt_learning_entries(schema_name);
CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status);
CREATE INDEX IF NOT EXISTS idx_job_queue_run_after ON job_queue(run_after);

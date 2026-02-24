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
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    processing_method TEXT DEFAULT 'vision',  -- 'vision' or 'text'
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (schema_id) REFERENCES schemas(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_provider ON processing_jobs(provider);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON processing_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_processing_method ON processing_jobs(processing_method);
CREATE INDEX IF NOT EXISTS idx_schemas_is_template ON schemas(is_template);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_file_id ON uploaded_files(file_id);

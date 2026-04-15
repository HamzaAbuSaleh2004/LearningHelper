-- Step 1: Create the 'learning_helper' database first (if you haven't)
-- CREATE DATABASE learning_helper;

-- Step 2: Connect to 'learning_helper' then run this:

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    level VARCHAR(50) DEFAULT 'Beginner',
    goals JSONB DEFAULT '[]',
    weights JSONB DEFAULT '{}',
    enrolled_courses JSONB DEFAULT '[]',
    active_course TEXT DEFAULT NULL,
    feedback_history JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    size INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    state TEXT NOT NULL,
    profile_id TEXT,
    health_total INTEGER,
    preservation_passed INTEGER,
    words INTEGER NOT NULL DEFAULT 0,
    paragraphs INTEGER NOT NULL DEFAULT 0,
    headings INTEGER NOT NULL DEFAULT 0,
    tables INTEGER NOT NULL DEFAULT 0,
    figures INTEGER NOT NULL DEFAULT 0,
    "references" INTEGER NOT NULL DEFAULT 0,
    sections INTEGER NOT NULL DEFAULT 0,
    owner TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_history_owner ON history(owner, updated_at);

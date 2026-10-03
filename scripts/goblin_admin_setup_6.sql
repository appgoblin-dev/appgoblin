CREATE TABLE user_generated_reports (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users (id),
    report_name VARCHAR(255) NOT NULL,
    s3_key TEXT NOT NULL,
    filters JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_generated_reports_user_created
ON user_generated_reports (user_id, created_at DESC);

CREATE TABLE user_requested_mapping (
    id SERIAL PRIMARY KEY,
    user_id INT NULL REFERENCES users (id),
    map_type VARCHAR(255) NOT NULL,
    value_to_be_mapped TEXT NOT NULL,
    additional_info JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_requested_mapping_created
ON user_requested_mapping (user_id, created_at DESC);

CREATE OR REPLACE FUNCTION CANONICALIZE_EMAIL(email TEXT)
RETURNS TEXT
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT
        split_part(
            replace(
                split_part(lower(trim(email)), '@', 1),
                '.',
                ''
            ),
            '+',
            1
        )
        || '@' ||
        lower(split_part(trim(email), '@', 2))
$$;


ALTER TABLE users
ADD COLUMN canonical_email TEXT;

UPDATE users
SET canonical_email = CANONICALIZE_EMAIL(email);

CREATE UNIQUE INDEX users_canonical_email_unique
ON users (canonical_email);

-- ============================================================================
-- API KEYS TABLE
-- ============================================================================
-- Allows users to generate API keys for programmatic access to the public API.
-- Keys are stored as SHA-256 hashes. The raw key prefix (first 8 chars) is
-- stored for display purposes so users can identify keys.
-- ============================================================================

CREATE TABLE public.api_keys (
    id serial4 NOT NULL,
    user_id int4 NOT NULL,
    key_hash text NOT NULL,
    key_prefix text NOT NULL,
    name text NOT NULL,
    is_active bool DEFAULT true NOT NULL,
    last_used_at timestamptz NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    expires_at timestamptz NULL,

    CONSTRAINT api_keys_pkey PRIMARY KEY (id),
    CONSTRAINT api_keys_key_hash_unique UNIQUE (key_hash),
    CONSTRAINT api_keys_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.users (id) ON DELETE CASCADE
);

CREATE INDEX idx_api_keys_key_hash ON public.api_keys USING btree (key_hash);
CREATE INDEX idx_api_keys_user_id ON public.api_keys USING btree (user_id);

-- allow connecting to the DB
GRANT CONNECT ON DATABASE goblinadmin TO frontend;

-- allow using the public schema
GRANT USAGE ON SCHEMA public TO frontend;

-- grant read/write on all current tables in public
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO frontend;

-- grant usage/select on sequences (needed if you use serials/identity columns)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO frontend;

-- ensure future tables/sequences created in public are also accessible
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT,
INSERT,
UPDATE,
DELETE ON TABLES TO frontend;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE,
SELECT ON SEQUENCES TO frontend;

CREATE TABLE public.users (
    id serial4 NOT NULL,
    email text NOT NULL,
    username text NOT NULL,
    password_hash text NOT NULL,
    email_verified bool DEFAULT false NOT NULL,
    totp_key bytea NULL,
    recovery_code bytea NOT NULL,
    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT users_pkey PRIMARY KEY (id)
);
CREATE INDEX email_index ON public.users USING btree (email);


CREATE TABLE public.sessions (
    id text NOT NULL,
    user_id int4 NOT NULL,
    expires_at timestamptz NOT NULL,
    two_factor_verified bool DEFAULT false NOT NULL,
    CONSTRAINT sessions_pkey PRIMARY KEY (id),
    CONSTRAINT sessions_user_id_fkey FOREIGN KEY (
        user_id
    ) REFERENCES public.users (id)
);

CREATE TABLE public.email_verification_requests (
    id text NOT NULL,
    user_id int4 NOT NULL,
    email text NOT NULL,
    code text NOT NULL,
    expires_at timestamptz NOT NULL,
    CONSTRAINT email_verification_requests_pkey PRIMARY KEY (id),
    CONSTRAINT email_verification_requests_user_id_fkey FOREIGN KEY (
        user_id
    ) REFERENCES public.users (id)
);

CREATE TABLE public.providers (
    id serial4 NOT NULL,
    name text NOT NULL,
    CONSTRAINT providers_pkey PRIMARY KEY (id)
);


CREATE TABLE public.password_reset_sessions (
    id text NOT NULL,
    user_id int4 NOT NULL,
    email text NOT NULL,
    code text NOT NULL,
    expires_at timestamptz NOT NULL,
    email_verified bool DEFAULT false NOT NULL,
    two_factor_verified bool DEFAULT false NOT NULL,
    CONSTRAINT password_reset_sessions_pkey PRIMARY KEY (id),
    CONSTRAINT password_reset_sessions_user_id_fkey FOREIGN KEY (
        user_id
    ) REFERENCES public.users (id)
);


CREATE TABLE public.user_requested_scan (
    id serial4 NOT NULL,
    store_id varchar NOT NULL,
    created_at timestamp DEFAULT current_timestamp null,
    user_id int8 NULL,
    CONSTRAINT user_requested_scan_pkey PRIMARY KEY (id)
);


ALTER TABLE public.user_requested_scan ADD CONSTRAINT user_requested_scan_user_id_fkey FOREIGN KEY (
    user_id
) REFERENCES public.users (id);


-- ============================================================================
-- PROVIDER SUBSCRIPTION & ORGANIZATION SCHEMA
-- ============================================================================
-- This migration adds support for:
-- - Organizations (multi-user accounts)
-- - Provider subscriptions with flexible feature tagging
-- - Seat-based billing
-- ============================================================================

CREATE TABLE public.providers (
    id serial4 NOT NULL,
    name text NOT NULL,
    CONSTRAINT providers_pkey PRIMARY KEY (id),
    CONSTRAINT providers_name_unique UNIQUE (name)
);

INSERT INTO public.providers (id, name) VALUES
(1, 'stripe'),
(2, 'paypal'),
(3, 'manual');
SELECT setval(
    pg_get_serial_sequence('public.providers', 'id'),
    (SELECT max(id) FROM public.providers)
);
-- ============================================================================
-- 1. ORGANIZATIONS
-- ============================================================================
-- Organizations allow multiple users to share a subscription
CREATE TABLE public.organizations (
    id serial4 NOT NULL,
    name text NOT NULL,
    slug text NOT NULL, -- URL-friendly identifier
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,

    provider_customer_id text NULL,

    CONSTRAINT organizations_pkey PRIMARY KEY (id),
    CONSTRAINT organizations_slug_key UNIQUE (slug)
);

CREATE INDEX organizations_provider_customer_id_idx ON public.organizations USING btree (
    provider_customer_id
);

-- ============================================================================
-- 2. ORGANIZATION MEMBERSHIPS
-- ============================================================================
-- Links users to organizations with roles
CREATE TABLE public.organization_members (
    id serial4 NOT NULL,
    organization_id int4 NOT NULL,
    user_id int4 NOT NULL,
    role text DEFAULT 'member' NOT NULL, -- 'owner', 'admin', 'member'
    created_at timestamptz DEFAULT now() NOT NULL,

    CONSTRAINT organization_members_pkey PRIMARY KEY (id),
    CONSTRAINT organization_members_org_user_unique UNIQUE (
        organization_id, user_id
    ),
    CONSTRAINT organization_members_organization_id_fkey FOREIGN KEY (
        organization_id
    )
    REFERENCES public.organizations (id) ON DELETE CASCADE,
    CONSTRAINT organization_members_user_id_fkey FOREIGN KEY (user_id)
    REFERENCES public.users (id) ON DELETE CASCADE,
    CONSTRAINT organization_members_role_check CHECK (
        role IN ('owner', 'admin', 'member')
    )
);

CREATE INDEX organization_members_user_id_idx ON public.organization_members USING btree (
    user_id
);
CREATE INDEX organization_members_organization_id_idx ON public.organization_members USING btree (
    organization_id
);

-- ============================================================================
-- 3. SUBSCRIPTIONS
-- ============================================================================
-- Tracks subscriptions (can be for individual users OR organizations)

CREATE TABLE public.subscriptions (
    id serial4 NOT NULL,

    -- Owner (either user OR organization)
    user_id int4 NULL,
    organization_id int4 NULL,

    -- Payment provider
    provider_name text NOT NULL REFERENCES providers (name),

    -- Provider identifiers
    provider_subscription_id text NOT NULL,
    provider_customer_id text NOT NULL,
    provider_product_id text NOT NULL,
    provider_price_id text NULL,

    -- Subscription status (normalized)
    -- 'active', 'canceled', 'past_due', 'unpaid', 'trialing', 'incomplete'
    status text NOT NULL,

    -- Seat management
    seats_total int4 DEFAULT 1 NOT NULL,

    -- Billing period
    current_period_start timestamptz NOT NULL,
    current_period_end timestamptz NOT NULL,

    -- Cancellation / trial
    cancel_at timestamptz NULL,
    cancel_requested_at timestamptz NULL,
    trial_end timestamptz NULL,

    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,

    CONSTRAINT subscriptions_pkey PRIMARY KEY (id),

    CONSTRAINT subscriptions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES public.users (id),

    CONSTRAINT subscriptions_organization_id_fkey
    FOREIGN KEY (organization_id) REFERENCES public.organizations (id),

    CONSTRAINT subscriptions_owner_check CHECK (
        (user_id IS NOT null AND organization_id IS null)
        OR (user_id IS null AND organization_id IS NOT null)
    ),

    CONSTRAINT subscriptions_status_check CHECK (
        status IN (
            'active',
            'canceled',
            'past_due',
            'unpaid',
            'trialing',
            'incomplete'
        )
    )
);

CREATE UNIQUE INDEX subscriptions_one_active_user_per_product
ON subscriptions (user_id, provider_product_id)
WHERE user_id IS NOT null AND status = 'active';

CREATE UNIQUE INDEX subscriptions_one_active_org_per_product
ON subscriptions (organization_id, provider_product_id)
WHERE organization_id IS NOT null AND status = 'active';

CREATE UNIQUE INDEX subscriptions_provider_subscription_unique
ON subscriptions (provider_name, provider_subscription_id);


CREATE INDEX subscriptions_user_id_idx ON public.subscriptions USING btree (
    user_id
);
CREATE INDEX subscriptions_organization_id_idx ON public.subscriptions USING btree (
    organization_id
);
CREATE INDEX subscriptions_provider_customer_id_idx ON public.subscriptions USING btree (
    provider_customer_id
);
CREATE INDEX subscriptions_status_idx ON public.subscriptions USING btree (
    status
);


-- Add provider ID and customer ID to users table for individual subscriptions
ALTER TABLE public.users ADD COLUMN provider_name text NULL;
ALTER TABLE public.users ADD COLUMN provider_customer_id text NULL;

ALTER TABLE public.users ADD CONSTRAINT users_provider_name_fkey
FOREIGN KEY (provider_name) REFERENCES public.providers (name);


CREATE INDEX users_provider_customer_id_idx ON public.users USING btree (
    provider_customer_id
);

-- 1. Unique constraints to prevent duplicates
ALTER TABLE users ADD CONSTRAINT users_provider_customer_unique
UNIQUE (provider_customer_id);

ALTER TABLE organizations ADD CONSTRAINT orgs_provider_customer_unique
UNIQUE (provider_customer_id);


CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON public.organizations
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON public.subscriptions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE users
ADD COLUMN created_at timestamp with time zone DEFAULT now() NOT NULL;

CREATE TABLE search_queries (
    id bigserial PRIMARY KEY,
    search_term text NOT NULL,
    user_id int4 NULL REFERENCES users (id),
    created_at timestamptz DEFAULT now() NOT NULL
);

CREATE INDEX idx_search_queries_created_at ON search_queries (created_at DESC);
CREATE INDEX idx_search_queries_term ON search_queries (search_term);

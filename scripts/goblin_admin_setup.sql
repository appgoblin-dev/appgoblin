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
-- STRIPE SUBSCRIPTION & ORGANIZATION SCHEMA
-- ============================================================================
-- This migration adds support for:
-- - Organizations (multi-user accounts)
-- - Stripe subscriptions with flexible feature tagging
-- - Seat-based billing
-- ============================================================================

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

    -- Stripe identifiers
    stripe_customer_id text NULL, -- Stripe customer ID

    CONSTRAINT organizations_pkey PRIMARY KEY (id),
    CONSTRAINT organizations_slug_key UNIQUE (slug)
);

CREATE INDEX organizations_stripe_customer_id_idx ON public.organizations USING btree (
    stripe_customer_id
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
-- Tracks Stripe subscriptions (can be for individual users OR organizations)
CREATE TABLE public.subscriptions (
    id serial4 NOT NULL,

    -- Owner (either user OR organization, not both)
    user_id int4 NULL, -- For individual subscriptions
    organization_id int4 NULL, -- For organization subscriptions

    -- Stripe data
    stripe_subscription_id text NOT NULL,
    stripe_customer_id text NOT NULL,
    stripe_price_id text NOT NULL, -- The Stripe price being billed

    -- Subscription status
    -- 'active', 'canceled', 'past_due', 'unpaid', 'trialing', 'incomplete'
    status text NOT NULL,

    -- Seat management
    seats_total int4 DEFAULT 1 NOT NULL, -- Total seats purchased
    seats_used int4 DEFAULT 0 NOT NULL, -- Seats currently in use

    -- Timestamps
    current_period_start timestamptz NOT NULL,
    current_period_end timestamptz NOT NULL,
    cancel_at timestamptz NULL, -- When subscription will be canceled
    canceled_at timestamptz NULL, -- When cancellation was requested
    trial_end timestamptz NULL,

    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,

    CONSTRAINT subscriptions_pkey PRIMARY KEY (id),
    CONSTRAINT subscriptions_stripe_subscription_id_key UNIQUE (
        stripe_subscription_id
    ),
    CONSTRAINT subscriptions_user_id_fkey FOREIGN KEY (user_id)
    REFERENCES public.users (id) ON DELETE CASCADE,
    CONSTRAINT subscriptions_organization_id_fkey FOREIGN KEY (organization_id)
    REFERENCES public.organizations (id) ON DELETE CASCADE,

    -- Ensure subscription belongs to either user OR organization, not both
    CONSTRAINT subscriptions_owner_check CHECK (
        (user_id IS NOT null AND organization_id IS null)
        OR (user_id IS null AND organization_id IS NOT null)
    ),

    -- Ensure seats_used doesn't exceed seats_total
    CONSTRAINT subscriptions_seats_check CHECK (seats_used <= seats_total)
);

CREATE INDEX subscriptions_user_id_idx ON public.subscriptions USING btree (
    user_id
);
CREATE INDEX subscriptions_organization_id_idx ON public.subscriptions USING btree (
    organization_id
);
CREATE INDEX subscriptions_stripe_customer_id_idx ON public.subscriptions USING btree (
    stripe_customer_id
);
CREATE INDEX subscriptions_status_idx ON public.subscriptions USING btree (
    status
);

-- ============================================================================
-- 4. SUBSCRIPTION FEATURES (FLEXIBLE TAGGING)
-- ============================================================================
-- Maps subscriptions to feature tags for flexible access control
-- This allows you to grant different capabilities per subscription
CREATE TABLE public.subscription_features (
    id serial4 NOT NULL,
    -- e.g., 'app-ads-txt', 'b2b-premium', 'aso-premium'
    subscription_id int4 NOT NULL,
    feature_tag text NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,

    CONSTRAINT subscription_features_pkey PRIMARY KEY (id),
    CONSTRAINT subscription_features_unique UNIQUE (
        subscription_id, feature_tag
    ),
    CONSTRAINT subscription_features_subscription_id_fkey FOREIGN KEY (
        subscription_id
    )
    REFERENCES public.subscriptions (id) ON DELETE CASCADE
);

CREATE INDEX subscription_features_subscription_id_idx ON public.subscription_features USING btree (
    subscription_id
);
CREATE INDEX subscription_features_feature_tag_idx ON public.subscription_features USING btree (
    feature_tag
);

-- Add Stripe customer ID to users table for individual subscriptions
ALTER TABLE public.users
ADD COLUMN stripe_customer_id text NULL;

CREATE INDEX users_stripe_customer_id_idx ON public.users USING btree (
    stripe_customer_id
);


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

-- ============================================================================
-- 9. GRANT PERMISSIONS
-- ============================================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO frontend;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO frontend;

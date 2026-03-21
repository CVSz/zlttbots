CREATE TABLE IF NOT EXISTS tenants (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'free',
    region TEXT NOT NULL DEFAULT 'US',
    api_key_hash TEXT NOT NULL UNIQUE,
    daily_spend_limit NUMERIC NOT NULL DEFAULT 100,
    kill_switch BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tenant_usage_events (
    id BIGSERIAL PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    units INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS generated_products (
    id TEXT PRIMARY KEY,
    tenant_id BIGINT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    market TEXT NOT NULL,
    niche TEXT NOT NULL,
    title TEXT NOT NULL,
    landing_url TEXT NOT NULL,
    price NUMERIC NOT NULL,
    currency TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_usage_events_tenant_created_at
ON tenant_usage_events(tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_generated_products_tenant_market
ON generated_products(tenant_id, market);

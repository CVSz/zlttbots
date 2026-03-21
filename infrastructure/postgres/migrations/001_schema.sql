
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";



CREATE TABLE IF NOT EXISTS accounts (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

username TEXT UNIQUE NOT NULL,

password TEXT NOT NULL,

proxy TEXT,

active BOOLEAN DEFAULT TRUE,

created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS proxies (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

host TEXT,

port INT,

username TEXT,

password TEXT,

active BOOLEAN DEFAULT TRUE

);



CREATE TABLE IF NOT EXISTS products (

id BIGINT PRIMARY KEY,

name TEXT,

price NUMERIC,

rating NUMERIC,

sold INT,

source TEXT,

affiliate_link TEXT,

created_at TIMESTAMP DEFAULT NOW()

);

CREATE TABLE IF NOT EXISTS arbitrage_events (

id serial primary key,

product_name text,

buy_source text,

sell_source text,

buy_price numeric,

sell_price numeric,

profit numeric,

created_at timestamp default now()

);


CREATE TABLE IF NOT EXISTS tiktok_products (

id BIGINT PRIMARY KEY,

name TEXT,

price NUMERIC,

sales INT,

rating NUMERIC,

trend_score NUMERIC,

updated_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS campaigns (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

product_id BIGINT REFERENCES products(id),

name TEXT,

created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS videos (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

file TEXT,

caption TEXT,

status TEXT DEFAULT 'pending',

campaign_id UUID REFERENCES campaigns(id),

created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS jobs (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

video TEXT,

status TEXT DEFAULT 'pending',

created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE IF NOT EXISTS campaign_metrics (

id BIGSERIAL PRIMARY KEY,

campaign_id UUID REFERENCES campaigns(id),

views INT DEFAULT 0,

clicks INT DEFAULT 0,

conversions INT DEFAULT 0,

revenue NUMERIC DEFAULT 0,

created_at TIMESTAMP DEFAULT NOW()

);

CREATE TABLE IF NOT EXISTS clicks (

id BIGSERIAL PRIMARY KEY,

campaign_id UUID,

ip TEXT,

country TEXT,

user_agent TEXT,

fingerprint TEXT,

target_url TEXT,

created_at TIMESTAMP DEFAULT NOW()

);

ALTER TABLE clicks
ADD COLUMN IF NOT EXISTS target_url TEXT;



CREATE TABLE IF NOT EXISTS orders (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

campaign_id UUID,

product_id BIGINT,

amount NUMERIC,

created_at TIMESTAMP DEFAULT NOW()

);



CREATE INDEX IF NOT EXISTS idx_click_campaign

ON clicks(campaign_id);



CREATE INDEX IF NOT EXISTS idx_orders_campaign

ON orders(campaign_id);



CREATE INDEX IF NOT EXISTS idx_products_sales

ON products(sold);





CREATE TABLE IF NOT EXISTS rl_decisions (

id BIGSERIAL PRIMARY KEY,

campaign_id TEXT NOT NULL,

selected_campaign_id TEXT NOT NULL,

score NUMERIC NOT NULL,

features JSONB NOT NULL DEFAULT '{}'::jsonb,

created_at TIMESTAMP DEFAULT NOW()

);

CREATE INDEX IF NOT EXISTS idx_rl_decisions_campaign_created_at

ON rl_decisions(campaign_id, created_at DESC);

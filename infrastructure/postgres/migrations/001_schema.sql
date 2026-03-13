
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";



CREATE TABLE accounts (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

username TEXT UNIQUE NOT NULL,

password TEXT NOT NULL,

proxy TEXT,

active BOOLEAN DEFAULT TRUE,

created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE proxies (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

host TEXT,

port INT,

username TEXT,

password TEXT,

active BOOLEAN DEFAULT TRUE

);



CREATE TABLE products (

id BIGINT PRIMARY KEY,

name TEXT,

price NUMERIC,

rating NUMERIC,

sold INT,

source TEXT,

affiliate_link TEXT,

created_at TIMESTAMP DEFAULT NOW()

);

create table arbitrage_events (

id serial primary key,

product_name text,

buy_source text,

sell_source text,

buy_price numeric,

sell_price numeric,

profit numeric,

created_at timestamp default now()

);


CREATE TABLE tiktok_products (

id BIGINT PRIMARY KEY,

name TEXT,

price NUMERIC,

sales INT,

rating NUMERIC,

trend_score NUMERIC,

updated_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE campaigns (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

product_id BIGINT REFERENCES products(id),

name TEXT,

created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE videos (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

file TEXT,

caption TEXT,

status TEXT DEFAULT 'pending',

campaign_id UUID REFERENCES campaigns(id),

created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE jobs (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

video TEXT,

status TEXT DEFAULT 'pending',

created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE clicks (

id BIGSERIAL PRIMARY KEY,

campaign_id UUID,

ip TEXT,

country TEXT,

user_agent TEXT,

fingerprint TEXT,

created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE orders (

id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

campaign_id UUID,

product_id BIGINT,

amount NUMERIC,

created_at TIMESTAMP DEFAULT NOW()

);



CREATE INDEX idx_click_campaign

ON clicks(campaign_id);



CREATE INDEX idx_orders_campaign

ON orders(campaign_id);



CREATE INDEX idx_products_sales

ON products(sold);




#!/usr/bin/env bash

set -euo pipefail

PROJECT="zlttbots"

echo "Creating project structure..."

mkdir -p "$PROJECT"

cd "$PROJECT"

mkdir -p \
services/tiktok-uploader \
services/tiktok-uploader/src \
services/tiktok-uploader/src/core \
services/tiktok-uploader/src/automation \
services/tiktok-uploader/src/models \
services/tiktok-uploader/src/config \
services/tiktok-uploader/src/utils \
services/tiktok-uploader/docker


echo "Generating package.json"

cat > services/tiktok-uploader/package.json << 'EOF'
{
"name": "zlttbots-tiktok-uploader",
"version": "1.0.0",
"type": "module",
"scripts": {
"start": "node src/index.js"
},
"dependencies": {
"playwright": "^1.43.0",
"dotenv": "^16.4.0",
"pg": "^8.11.0",
"axios": "^1.6.0",
"uuid": "^9.0.0"
}
}
EOF


echo "Generating env config"

cat > services/tiktok-uploader/src/config/env.js << 'EOF'
import dotenv from "dotenv"

dotenv.config()

export const config = {
db: process.env.DB_URL,
videoDir: process.env.VIDEO_DIR || "./videos",
}
EOF



echo "Generating database layer"

cat > services/tiktok-uploader/src/core/database.js << 'EOF'
import pkg from "pg"

const { Pool } = pkg

export const db = new Pool({
connectionString: process.env.DB_URL
})
EOF



echo "Generating account model"

cat > services/tiktok-uploader/src/models/account.js << 'EOF'
export class Account {

constructor(row){
this.id=row.id
this.username=row.username
this.password=row.password
this.proxy=row.proxy
}

}
EOF



echo "Generating video model"

cat > services/tiktok-uploader/src/models/video.js << 'EOF'
export class Video {

constructor(row){
this.id=row.id
this.file=row.file
this.caption=row.caption
this.status=row.status
}

}
EOF



echo "Generating login automation"

cat > services/tiktok-uploader/src/automation/login.js << 'EOF'
export async function login(page, account){

await page.goto("https://www.tiktok.com/login")

await page.fill('input[name="username"]', account.username)

await page.fill('input[type="password"]', account.password)

await page.click('button[type="submit"]')

await page.waitForTimeout(5000)

}
EOF



echo "Generating upload automation"

cat > services/tiktok-uploader/src/automation/upload.js << 'EOF'
export async function uploadVideo(page, video){

await page.goto("https://www.tiktok.com/upload")

await page.setInputFiles('input[type="file"]', video.file)

await page.fill('[contenteditable="true"]', video.caption)

await page.click('button:has-text("Post")')

await page.waitForTimeout(8000)

}
EOF



echo "Generating browser controller"

cat > services/tiktok-uploader/src/core/browser.js << 'EOF'
import { chromium } from "playwright"

export async function createBrowser(proxy){

return await chromium.launch({
headless:false,
proxy: proxy ? {server:proxy} : undefined
})

}
EOF



echo "Generating uploader service"

cat > services/tiktok-uploader/src/core/uploader.js << 'EOF'
import { createBrowser } from "./browser.js"
import { login } from "../automation/login.js"
import { uploadVideo } from "../automation/upload.js"

export async function runUploader(account, video){

const browser = await createBrowser(account.proxy)

const context = await browser.newContext()

const page = await context.newPage()

await login(page, account)

await uploadVideo(page, video)

await browser.close()

}
EOF



echo "Generating worker"

cat > services/tiktok-uploader/src/core/worker.js << 'EOF'
import { db } from "./database.js"
import { runUploader } from "./uploader.js"

export async function worker(){

const videos = await db.query(
"select * from videos where status='pending' limit 1"
)

if(videos.rows.length === 0) return

const video = videos.rows[0]

const accounts = await db.query(
"select * from accounts order by random() limit 1"
)

await runUploader(accounts.rows[0], video)

await db.query(
"update videos set status='posted' where id=$1",
[video.id]
)

}
EOF



echo "Generating main entry"

cat > services/tiktok-uploader/src/index.js << 'EOF'
import { worker } from "./core/worker.js"

async function main(){

while(true){

try{

await worker()

}catch(e){

console.error(e)

}

await new Promise(r=>setTimeout(r,15000))

}

}

main()
EOF



echo "Generating Dockerfile"

cat > services/tiktok-uploader/docker/Dockerfile << 'EOF'
FROM mcr.microsoft.com/playwright:v1.43.0-jammy

WORKDIR /app

COPY . .

RUN npm install

CMD ["npm","start"]
EOF



echo "STEP 1 COMPLETE"
echo "TikTok Playwright uploader generated"

echo "Generating AI Video Generator..."

mkdir -p services/ai-video-generator
mkdir -p services/ai-video-generator/src
mkdir -p services/ai-video-generator/src/core
mkdir -p services/ai-video-generator/src/render
mkdir -p services/ai-video-generator/src/tts
mkdir -p services/ai-video-generator/src/subtitle
mkdir -p services/ai-video-generator/src/templates
mkdir -p services/ai-video-generator/src/utils
mkdir -p services/ai-video-generator/docker


cat > services/ai-video-generator/package.json << 'EOF'
{
"name": "zlttbots-ai-video-generator",
"version": "1.0.0",
"type": "module",
"scripts": {
"start": "node src/index.js"
},
"dependencies": {
"fluent-ffmpeg": "^2.1.2",
"uuid": "^9.0.0",
"axios": "^1.6.0",
"dotenv": "^16.4.0",
"pg": "^8.11.0"
}
}
EOF


cat > services/ai-video-generator/src/core/database.js << 'EOF'
import pkg from "pg"

const { Pool } = pkg

export const db = new Pool({
connectionString: process.env.DB_URL
})
EOF


cat > services/ai-video-generator/src/tts/voice.js << 'EOF'
import fs from "fs"
import axios from "axios"

export async function generateVoice(text, output){

const url = "https://api.elevenlabs.io/v1/text-to-speech"

const response = await axios.post(
url,
{text},
{responseType:"arraybuffer"}
)

fs.writeFileSync(output,response.data)

}
EOF


cat > services/ai-video-generator/src/subtitle/subtitle.js << 'EOF'
import fs from "fs"

export function generateSubtitle(text, output){

const lines = text.split(". ")

let srt = ""

lines.forEach((l,i)=>{

srt += `${i+1}\n`
srt += `00:00:${String(i*3).padStart(2,"0")},000 --> 00:00:${String((i+1)*3).padStart(2,"0")},000\n`
srt += l + "\n\n"

})

fs.writeFileSync(output,srt)

}
EOF


cat > services/ai-video-generator/src/render/video.js << 'EOF'
import ffmpeg from "fluent-ffmpeg"

export function renderVideo(image, voice, subtitle, output){

return new Promise((resolve,reject)=>{

ffmpeg()

.input(image)
.loop(10)

.input(voice)

.videoFilters([
{
filter:"subtitles",
options:subtitle
}
])

.outputOptions([
"-c:v libx264",
"-c:a aac",
"-shortest",
"-pix_fmt yuv420p"
])

.save(output)

.on("end",resolve)
.on("error",reject)

})

}
EOF



cat > services/ai-video-generator/src/core/generator.js << 'EOF'
import { generateVoice } from "../tts/voice.js"
import { generateSubtitle } from "../subtitle/subtitle.js"
import { renderVideo } from "../render/video.js"

export async function generateVideo(product){

const voiceFile = `voice_${product.id}.mp3`
const subtitleFile = `sub_${product.id}.srt`
const videoFile = `video_${product.id}.mp4`

const script = product.script

await generateVoice(script, voiceFile)

generateSubtitle(script, subtitleFile)

await renderVideo(
product.image,
voiceFile,
subtitleFile,
videoFile
)

return videoFile

}
EOF



cat > services/ai-video-generator/src/core/worker.js << 'EOF'
import { db } from "./database.js"
import { generateVideo } from "./generator.js"

export async function worker(){

const jobs = await db.query(
"select * from video_jobs where status='pending' limit 1"
)

if(jobs.rows.length === 0) return

const job = jobs.rows[0]

const video = await generateVideo(job)

await db.query(
"update video_jobs set status='done', file=$1 where id=$2",
[video,job.id]
)

}
EOF



cat > services/ai-video-generator/src/index.js << 'EOF'
import { worker } from "./core/worker.js"

async function main(){

while(true){

try{

await worker()

}catch(e){

console.error(e)

}

await new Promise(r=>setTimeout(r,10000))

}

}

main()
EOF



cat > services/ai-video-generator/docker/Dockerfile << 'EOF'
FROM node:20

RUN apt update && apt install -y ffmpeg

WORKDIR /app

COPY . .

RUN npm install

CMD ["npm","start"]
EOF


echo "STEP 2 COMPLETE"
echo "AI Video Generator created"

echo "Generating Shopee Affiliate Crawler..."

mkdir -p services/shopee-crawler
mkdir -p services/shopee-crawler/src
mkdir -p services/shopee-crawler/src/core
mkdir -p services/shopee-crawler/src/crawler
mkdir -p services/shopee-crawler/src/parser
mkdir -p services/shopee-crawler/src/models
mkdir -p services/shopee-crawler/src/utils
mkdir -p services/shopee-crawler/docker



cat > services/shopee-crawler/package.json << 'EOF'
{
"name": "zlttbots-shopee-crawler",
"version": "1.0.0",
"type": "module",
"scripts": {
"start": "node src/index.js"
},
"dependencies": {
"axios": "^1.6.0",
"pg": "^8.11.0",
"cheerio": "^1.0.0",
"dotenv": "^16.4.0",
"uuid": "^9.0.0"
}
}
EOF



cat > services/shopee-crawler/src/core/database.js << 'EOF'
import pkg from "pg"

const { Pool } = pkg

export const db = new Pool({
connectionString: process.env.DB_URL
})
EOF



cat > services/shopee-crawler/src/crawler/search.js << 'EOF'
import axios from "axios"

export async function searchProducts(keyword){

const url = "https://shopee.co.th/api/v4/search/search_items"

const res = await axios.get(url,{
params:{
keyword:keyword,
limit:50
}
})

return res.data.items

}
EOF



cat > services/shopee-crawler/src/parser/product.js << 'EOF'
export function parseProduct(raw){

return {
id: raw.itemid,
name: raw.name,
price: raw.price/100000,
sold: raw.sold,
rating: raw.item_rating.rating_star
}

}
EOF



cat > services/shopee-crawler/src/core/affiliate.js << 'EOF'
export function generateAffiliateLink(productId){

return `https://shopee.co.th/product/${productId}?aff_id=ZLTTBOTS`

}
EOF



cat > services/shopee-crawler/src/core/crawler.js << 'EOF'
import { searchProducts } from "../crawler/search.js"
import { parseProduct } from "../parser/product.js"
import { db } from "./database.js"
import { generateAffiliateLink } from "./affiliate.js"

export async function crawl(keyword){

const products = await searchProducts(keyword)

for(const p of products){

const parsed = parseProduct(p)

const link = generateAffiliateLink(parsed.id)

await db.query(
`insert into products
(id,name,price,sold,rating,affiliate_link)
values($1,$2,$3,$4,$5,$6)
on conflict(id) do update
set price=$3,sold=$4`,
[
parsed.id,
parsed.name,
parsed.price,
parsed.sold,
parsed.rating,
link
]
)

}

}
EOF



cat > services/shopee-crawler/src/core/scheduler.js << 'EOF'
import { crawl } from "./crawler.js"

const KEYWORDS = [
"beauty",
"gadget",
"kitchen",
"fitness",
"fashion"
]

export async function scheduler(){

for(const k of KEYWORDS){

try{

await crawl(k)

}catch(e){

console.error(e)

}

}

}
EOF



cat > services/shopee-crawler/src/index.js << 'EOF'
import { scheduler } from "./core/scheduler.js"

async function main(){

while(true){

await scheduler()

await new Promise(r=>setTimeout(r,3600000))

}

}

main()
EOF



cat > services/shopee-crawler/docker/Dockerfile << 'EOF'
FROM node:20

WORKDIR /app

COPY . .

RUN npm install

CMD ["npm","start"]
EOF



echo "STEP 3 COMPLETE"
echo "Shopee Affiliate Crawler created"

echo "Generating TikTok Shop Miner..."

mkdir -p services/tiktok-shop-miner
mkdir -p services/tiktok-shop-miner/src
mkdir -p services/tiktok-shop-miner/src/core
mkdir -p services/tiktok-shop-miner/src/crawler
mkdir -p services/tiktok-shop-miner/src/parser
mkdir -p services/tiktok-shop-miner/src/models
mkdir -p services/tiktok-shop-miner/src/utils
mkdir -p services/tiktok-shop-miner/docker


cat > services/tiktok-shop-miner/package.json << 'EOF'
{
"name": "zlttbots-tiktok-shop-miner",
"version": "1.0.0",
"type": "module",
"scripts": {
"start": "node src/index.js"
},
"dependencies": {
"playwright": "^1.43.0",
"pg": "^8.11.0",
"axios": "^1.6.0",
"dotenv": "^16.4.0",
"uuid": "^9.0.0"
}
}
EOF


cat > services/tiktok-shop-miner/src/core/database.js << 'EOF'
import pkg from "pg"

const { Pool } = pkg

export const db = new Pool({
connectionString: process.env.DB_URL
})
EOF


cat > services/tiktok-shop-miner/src/crawler/search.js << 'EOF'
import axios from "axios"

export async function searchProducts(keyword){

const url = "https://shop.tiktok.com/api/search"

const res = await axios.get(url,{
params:{
keyword:keyword,
limit:50
}
})

return res.data.products || []

}
EOF


cat > services/tiktok-shop-miner/src/parser/product.js << 'EOF'
export function parseProduct(raw){

return {
id: raw.product_id,
name: raw.title,
price: raw.price,
sales: raw.sales,
rating: raw.rating
}

}
EOF


cat > services/tiktok-shop-miner/src/core/trending.js << 'EOF'
export function scoreProduct(p){

return (p.sales * 2) + (p.rating * 100)

}
EOF


cat > services/tiktok-shop-miner/src/core/miner.js << 'EOF'
import { searchProducts } from "../crawler/search.js"
import { parseProduct } from "../parser/product.js"
import { scoreProduct } from "./trending.js"
import { db } from "./database.js"

export async function mine(keyword){

const products = await searchProducts(keyword)

for(const p of products){

const parsed = parseProduct(p)

const score = scoreProduct(parsed)

await db.query(
`insert into tiktok_products
(id,name,price,sales,rating,trend_score)
values($1,$2,$3,$4,$5,$6)
on conflict(id) do update
set price=$3,sales=$4,trend_score=$6`,
[
parsed.id,
parsed.name,
parsed.price,
parsed.sales,
parsed.rating,
score
]
)

}

}
EOF


cat > services/tiktok-shop-miner/src/core/scheduler.js << 'EOF'
import { mine } from "./miner.js"

const KEYWORDS = [
"beauty",
"gadget",
"kitchen",
"fashion",
"fitness"
]

export async function scheduler(){

for(const k of KEYWORDS){

try{

await mine(k)

}catch(e){

console.error(e)

}

}

}
EOF


cat > services/tiktok-shop-miner/src/index.js << 'EOF'
import { scheduler } from "./core/scheduler.js"

async function main(){

while(true){

await scheduler()

await new Promise(r=>setTimeout(r,1800000))

}

}

main()
EOF


cat > services/tiktok-shop-miner/docker/Dockerfile << 'EOF'
FROM mcr.microsoft.com/playwright:v1.43.0-jammy

WORKDIR /app

COPY . .

RUN npm install

CMD ["npm","start"]
EOF


echo "STEP 4 COMPLETE"
echo "TikTok Shop Miner created"

echo "Generating Redirect Click Tracking Server..."

mkdir -p services/click-tracker
mkdir -p services/click-tracker/src
mkdir -p services/click-tracker/src/server
mkdir -p services/click-tracker/src/core
mkdir -p services/click-tracker/src/models
mkdir -p services/click-tracker/src/utils
mkdir -p services/click-tracker/docker


cat > services/click-tracker/package.json << 'EOF'
{
"name": "zlttbots-click-tracker",
"version": "1.0.0",
"type": "module",
"scripts": {
"start": "node src/server/server.js"
},
"dependencies": {
"pg": "^8.11.0",
"uuid": "^9.0.0",
"geoip-lite": "^1.4.7",
"dotenv": "^16.4.0"
}
}
EOF



cat > services/click-tracker/src/core/database.js << 'EOF'
import pkg from "pg"

const { Pool } = pkg

export const db = new Pool({
connectionString: process.env.DB_URL
})
EOF



cat > services/click-tracker/src/utils/fingerprint.js << 'EOF'
export function fingerprint(ip, ua){

return `${ip}_${ua}`

}
EOF



cat > services/click-tracker/src/core/tracker.js << 'EOF'
import { db } from "./database.js"
import geoip from "geoip-lite"
import { fingerprint } from "../utils/fingerprint.js"

export async function trackClick(req, campaign, target){

const ip = req.socket.remoteAddress
const ua = req.headers["user-agent"] || ""

const geo = geoip.lookup(ip)

const fp = fingerprint(ip, ua)

await db.query(
`insert into clicks
(campaign_id,ip,country,user_agent,fingerprint)
values($1,$2,$3,$4,$5)`,
[
campaign,
ip,
geo ? geo.country : null,
ua,
fp
]
)

return target

}
EOF



cat > services/click-tracker/src/server/server.js << 'EOF'
import http from "http"
import { trackClick } from "../core/tracker.js"

const server = http.createServer(async (req,res)=>{

try{

const url = new URL(req.url,"http://localhost")

if(url.pathname.startsWith("/r/")){

const campaign = url.pathname.split("/")[2]

const target = url.searchParams.get("to")

const redirect = await trackClick(req,campaign,target)

res.writeHead(302,{
Location: redirect
})

res.end()

return

}

res.writeHead(404)
res.end()

}catch(e){

console.error(e)

res.writeHead(500)
res.end()

}

})

server.listen(8080)
EOF



cat > services/click-tracker/docker/Dockerfile << 'EOF'
FROM node:20

WORKDIR /app

COPY . .

RUN npm install

EXPOSE 8080

CMD ["npm","start"]
EOF


echo "STEP 5 COMPLETE"
echo "Redirect Click Tracking Server created"

echo "Generating Profit Analytics Backend..."

mkdir -p services/analytics
mkdir -p services/analytics/src
mkdir -p services/analytics/src/api
mkdir -p services/analytics/src/core
mkdir -p services/analytics/src/metrics
mkdir -p services/analytics/src/utils
mkdir -p services/analytics/docker



cat > services/analytics/package.json << 'EOF'
{
"name": "zlttbots-analytics",
"version": "1.0.0",
"type": "module",
"scripts": {
"start": "node src/api/server.js"
},
"dependencies": {
"pg": "^8.11.0",
"express": "^4.19.2",
"dotenv": "^16.4.0"
}
}
EOF



cat > services/analytics/src/core/database.js << 'EOF'
import pkg from "pg"

const { Pool } = pkg

export const db = new Pool({
connectionString: process.env.DB_URL
})
EOF



cat > services/analytics/src/metrics/revenue.js << 'EOF'
import { db } from "../core/database.js"

export async function totalRevenue(){

const r = await db.query(
"select sum(amount) as revenue from orders"
)

return r.rows[0].revenue || 0

}
EOF



cat > services/analytics/src/metrics/conversion.js << 'EOF'
import { db } from "../core/database.js"

export async function conversionRate(){

const clicks = await db.query("select count(*) from clicks")
const orders = await db.query("select count(*) from orders")

const c = Number(clicks.rows[0].count)
const o = Number(orders.rows[0].count)

if(c === 0) return 0

return o / c

}
EOF



cat > services/analytics/src/metrics/campaign.js << 'EOF'
import { db } from "../core/database.js"

export async function campaignROI(){

const r = await db.query(`
select campaign_id,
sum(amount) as revenue,
count(*) as orders
from orders
group by campaign_id
`)

return r.rows

}
EOF



cat > services/analytics/src/metrics/products.js << 'EOF'
import { db } from "../core/database.js"

export async function productPerformance(){

const r = await db.query(`
select product_id,
sum(amount) as revenue,
count(*) as sales
from orders
group by product_id
order by revenue desc
limit 50
`)

return r.rows

}
EOF



cat > services/analytics/src/api/server.js << 'EOF'
import express from "express"

import { totalRevenue } from "../metrics/revenue.js"
import { conversionRate } from "../metrics/conversion.js"
import { campaignROI } from "../metrics/campaign.js"
import { productPerformance } from "../metrics/products.js"

const app = express()


app.get("/analytics/revenue", async(req,res)=>{

const r = await totalRevenue()

res.json({revenue:r})

})


app.get("/analytics/conversion", async(req,res)=>{

const r = await conversionRate()

res.json({conversion:r})

})


app.get("/analytics/campaigns", async(req,res)=>{

const r = await campaignROI()

res.json(r)

})


app.get("/analytics/products", async(req,res)=>{

const r = await productPerformance()

res.json(r)

})


app.listen(9000)
EOF



cat > services/analytics/docker/Dockerfile << 'EOF'
FROM node:20

WORKDIR /app

COPY . .

RUN npm install

EXPOSE 9000

CMD ["npm","start"]
EOF



echo "STEP 6 COMPLETE"
echo "Profit Analytics Backend created"

echo "Generating Multi Account Farm Engine..."

mkdir -p services/account-farm
mkdir -p services/account-farm/src
mkdir -p services/account-farm/src/core
mkdir -p services/account-farm/src/api
mkdir -p services/account-farm/src/scheduler
mkdir -p services/account-farm/src/monitor
mkdir -p services/account-farm/src/models
mkdir -p services/account-farm/docker


cat > services/account-farm/package.json << 'EOF'
{
"name": "zlttbots-account-farm",
"version": "1.0.0",
"type": "module",
"scripts": {
"start": "node src/api/server.js"
},
"dependencies": {
"pg": "^8.11.0",
"express": "^4.19.2",
"axios": "^1.6.0",
"dotenv": "^16.4.0",
"uuid": "^9.0.0"
}
}
EOF


cat > services/account-farm/src/core/database.js << 'EOF'
import pkg from "pg"

const { Pool } = pkg

export const db = new Pool({
connectionString: process.env.DB_URL
})
EOF


cat > services/account-farm/src/core/proxy.js << 'EOF'
import { db } from "./database.js"

export async function getProxy(){

const r = await db.query(
"select * from proxies order by random() limit 1"
)

return r.rows[0]

}
EOF


cat > services/account-farm/src/core/accounts.js << 'EOF'
import { db } from "./database.js"

export async function getAccount(){

const r = await db.query(
"select * from accounts where active=true order by random() limit 1"
)

return r.rows[0]

}
EOF


cat > services/account-farm/src/core/jobs.js << 'EOF'
import { db } from "./database.js"

export async function nextJob(){

const r = await db.query(
"select * from jobs where status='pending' limit 1"
)

return r.rows[0]

}

export async function completeJob(id){

await db.query(
"update jobs set status='done' where id=$1",
[id]
)

}
EOF


cat > services/account-farm/src/scheduler/worker.js << 'EOF'
import axios from "axios"

import { getAccount } from "../core/accounts.js"
import { getProxy } from "../core/proxy.js"
import { nextJob, completeJob } from "../core/jobs.js"

export async function worker(){

const job = await nextJob()

if(!job) return

const account = await getAccount()

const proxy = await getProxy()

await axios.post(
"http://tiktok-uploader:3000/upload",
{
account,
proxy,
video: job.video
}
)

await completeJob(job.id)

}
EOF


cat > services/account-farm/src/scheduler/scheduler.js << 'EOF'
import { worker } from "./worker.js"

export async function scheduler(){

for(let i=0;i<5;i++){

try{

await worker()

}catch(e){

console.error(e)

}

}

}
EOF


cat > services/account-farm/src/monitor/health.js << 'EOF'
import { db } from "../core/database.js"

export async function farmHealth(){

const r = await db.query(
"select count(*) from accounts where active=true"
)

return {
active_accounts: Number(r.rows[0].count)
}

}
EOF


cat > services/account-farm/src/api/server.js << 'EOF'
import express from "express"

import { scheduler } from "../scheduler/scheduler.js"
import { farmHealth } from "../monitor/health.js"

const app = express()

app.use(express.json())


app.get("/farm/health", async(req,res)=>{

const h = await farmHealth()

res.json(h)

})


app.post("/farm/run", async(req,res)=>{

await scheduler()

res.json({status:"ok"})

})


app.listen(7000)
EOF


cat > services/account-farm/docker/Dockerfile << 'EOF'
FROM node:20

WORKDIR /app

COPY . .

RUN npm install

EXPOSE 7000

CMD ["npm","start"]
EOF


echo "STEP 7 COMPLETE"
echo "Multi Account Farm Engine created"

echo "Generating PostgreSQL Production Schema..."

mkdir -p infrastructure/postgres
mkdir -p infrastructure/postgres/migrations



cat > infrastructure/postgres/migrations/001_schema.sql << 'EOF'

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



EOF



cat > infrastructure/postgres/docker-compose.postgres.yml << 'EOF'

services:

postgres:

image: postgres:15

environment:

POSTGRES_DB: zlttbots

POSTGRES_USER: zlttbots

POSTGRES_PASSWORD: zlttbots

ports:

- "5432:5432"

volumes:

- ./data:/var/lib/postgresql/data

EOF



echo "STEP 8 COMPLETE"
echo "PostgreSQL Production Schema created"

echo "Generating React Admin Panel..."

mkdir -p services/admin-panel
mkdir -p services/admin-panel/src
mkdir -p services/admin-panel/src/components
mkdir -p services/admin-panel/src/pages
mkdir -p services/admin-panel/src/api
mkdir -p services/admin-panel/src/layout
mkdir -p services/admin-panel/public
mkdir -p services/admin-panel/docker



cat > services/admin-panel/package.json << 'EOF'
{
"name": "zlttbots-admin-panel",
"version": "1.0.0",
"private": true,
"type": "module",
"scripts": {
"dev": "vite",
"build": "vite build",
"preview": "vite preview"
},
"dependencies": {
"react": "^18.2.0",
"react-dom": "^18.2.0",
"axios": "^1.6.0",
"chart.js": "^4.4.0",
"react-chartjs-2": "^5.2.0"
},
"devDependencies": {
"vite": "^5.0.0"
}
}
EOF



cat > services/admin-panel/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
<title>zlttbots Admin</title>
</head>
<body>

<div id="root"></div>

<script type="module" src="/src/main.jsx"></script>

</body>
</html>
EOF



cat > services/admin-panel/src/main.jsx << 'EOF'
import React from "react"
import ReactDOM from "react-dom/client"

import App from "./App.jsx"

ReactDOM.createRoot(
document.getElementById("root")
).render(<App/>)
EOF



cat > services/admin-panel/src/App.jsx << 'EOF'
import React from "react"

import Dashboard from "./pages/Dashboard.jsx"
import Campaigns from "./pages/Campaigns.jsx"
import Products from "./pages/Products.jsx"

export default function App(){

return(

<div>

<h1>zlttbots Control Panel</h1>

<Dashboard/>

<Campaigns/>

<Products/>

</div>

)

}
EOF



cat > services/admin-panel/src/api/api.js << 'EOF'
import axios from "axios"

export const api = axios.create({

baseURL: "http://localhost"

})
EOF



cat > services/admin-panel/src/pages/Dashboard.jsx << 'EOF'
import React, { useEffect, useState } from "react"
import { api } from "../api/api.js"

export default function Dashboard(){

const [revenue,setRevenue] = useState(0)

useEffect(()=>{

api.get("/analytics/revenue")
.then(r=>setRevenue(r.data.revenue))

},[])

return(

<div>

<h2>Revenue</h2>

<p>{revenue}</p>

</div>

)

}
EOF



cat > services/admin-panel/src/pages/Campaigns.jsx << 'EOF'
import React from "react"

export default function Campaigns(){

return(

<div>

<h2>Campaign Manager</h2>

</div>

)

}
EOF



cat > services/admin-panel/src/pages/Products.jsx << 'EOF'
import React from "react"

export default function Products(){

return(

<div>

<h2>Product Manager</h2>

</div>

)

}
EOF



cat > services/admin-panel/docker/Dockerfile << 'EOF'
FROM node:20

WORKDIR /app

COPY . .

RUN npm install

RUN npm run build

RUN npm install -g serve

EXPOSE 3000

CMD ["serve","-s","dist"]
EOF



echo "STEP 9 COMPLETE"
echo "React Admin Panel created"

echo "Generating Kubernetes deployment..."

mkdir -p infrastructure/k8s
mkdir -p infrastructure/k8s/base
mkdir -p infrastructure/k8s/deployments
mkdir -p infrastructure/k8s/services
mkdir -p infrastructure/k8s/ingress
mkdir -p infrastructure/k8s/config
mkdir -p infrastructure/k8s/autoscale

cat > infrastructure/k8s/config/configmap.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: zlttbots-config
data:
  DB_HOST: postgres
  DB_NAME: zlttbots
EOF

cat > infrastructure/k8s/deployments/postgres.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: zlttbots
        - name: POSTGRES_USER
          value: zlttbots
        - name: POSTGRES_PASSWORD
          value: zlttbots
        ports:
        - containerPort: 5432
EOF

cat > infrastructure/k8s/deployments/analytics.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics
spec:
  replicas: 2
  selector:
    matchLabels:
      app: analytics
  template:
    metadata:
      labels:
        app: analytics
    spec:
      containers:
      - name: analytics
        image: zlttbots/analytics:latest
        ports:
        - containerPort: 9000
EOF

cat > infrastructure/k8s/deployments/click-tracker.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: click-tracker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: click-tracker
  template:
    metadata:
      labels:
        app: click-tracker
    spec:
      containers:
      - name: tracker
        image: zlttbots/click-tracker:latest
        ports:
        - containerPort: 8080
EOF

cat > infrastructure/k8s/deployments/admin-panel.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: admin-panel
spec:
  replicas: 1
  selector:
    matchLabels:
      app: admin-panel
  template:
    metadata:
      labels:
        app: admin-panel
    spec:
      containers:
      - name: admin
        image: zlttbots/admin-panel:latest
        ports:
        - containerPort: 3000
EOF

cat > infrastructure/k8s/services/analytics.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: analytics
spec:
  selector:
    app: analytics
  ports:
  - port: 9000
    targetPort: 9000
EOF

cat > infrastructure/k8s/services/click-tracker.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: click-tracker
spec:
  selector:
    app: click-tracker
  ports:
  - port: 80
    targetPort: 8080
EOF

cat > infrastructure/k8s/autoscale/analytics-hpa.yaml << 'EOF'
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: analytics-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: analytics
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
EOF

cat > infrastructure/k8s/ingress/ingress.yaml << 'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: zlttbots-ingress
spec:
  rules:
  - host: zlttbots.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: admin-panel
            port:
              number: 3000
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: analytics
            port:
              number: 9000
EOF

echo "STEP 10 COMPLETE"
echo "Generating Kubernetes Production Deployment created"

echo "Generating CI/CD pipeline..."

mkdir -p .github/workflows
mkdir -p infrastructure/ci
mkdir -p infrastructure/scripts

cat > .github/workflows/zlttbots-ci.yml << 'EOF'
name: zlttbots CI/CD

on:
  push:
    branches:
      - main

env:
  REGISTRY: docker.io
  IMAGE_PREFIX: zlttbots

jobs:

  build:

    runs-on: ubuntu-latest

    steps:

    - name: Checkout
      uses: actions/checkout@v3

    - name: Setup Docker
      uses: docker/setup-buildx-action@v2

    - name: Login DockerHub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USER }}
        password: ${{ secrets.DOCKER_PASS }}

    - name: Build Images
      run: |

        docker build -t $REGISTRY/$IMAGE_PREFIX/analytics services/analytics
        docker build -t $REGISTRY/$IMAGE_PREFIX/click-tracker services/click-tracker
        docker build -t $REGISTRY/$IMAGE_PREFIX/tiktok-uploader services/tiktok-uploader
        docker build -t $REGISTRY/$IMAGE_PREFIX/ai-video-generator services/ai-video-generator
        docker build -t $REGISTRY/$IMAGE_PREFIX/shopee-crawler services/shopee-crawler
        docker build -t $REGISTRY/$IMAGE_PREFIX/tiktok-shop-miner services/tiktok-shop-miner
        docker build -t $REGISTRY/$IMAGE_PREFIX/account-farm services/account-farm
        docker build -t $REGISTRY/$IMAGE_PREFIX/admin-panel services/admin-panel

    - name: Push Images
      run: |

        docker push $REGISTRY/$IMAGE_PREFIX/analytics
        docker push $REGISTRY/$IMAGE_PREFIX/click-tracker
        docker push $REGISTRY/$IMAGE_PREFIX/tiktok-uploader
        docker push $REGISTRY/$IMAGE_PREFIX/ai-video-generator
        docker push $REGISTRY/$IMAGE_PREFIX/shopee-crawler
        docker push $REGISTRY/$IMAGE_PREFIX/tiktok-shop-miner
        docker push $REGISTRY/$IMAGE_PREFIX/account-farm
        docker push $REGISTRY/$IMAGE_PREFIX/admin-panel

  deploy:

    needs: build

    runs-on: ubuntu-latest

    steps:

    - name: Checkout
      uses: actions/checkout@v3

    - name: Setup kubectl
      uses: azure/setup-kubectl@v3

    - name: Deploy
      run: |

        kubectl apply -f infrastructure/k8s
EOF

cat > infrastructure/scripts/rollback.sh << 'EOF'
#!/usr/bin/env bash

set -euo pipefail

DEPLOYMENT=$1

kubectl rollout undo deployment/$DEPLOYMENT
EOF

cat > infrastructure/ci/build-all.sh << 'EOF'
#!/usr/bin/env bash

set -euo pipefail

services=(
analytics
click-tracker
tiktok-uploader
ai-video-generator
shopee-crawler
tiktok-shop-miner
account-farm
admin-panel
)

for s in "${services[@]}"
do

docker build -t zlttbots/$s services/$s

done
EOF

cat > infrastructure/ci/deploy.sh << 'EOF'
#!/usr/bin/env bash

set -euo pipefail

kubectl apply -f infrastructure/k8s
EOF

echo "STEP 11 COMPLETE"
echo "Generating CI/CD pipeline created"

echo "STEP 12 — Bash Generator (AI Viral Video Predictor)"
echo "Generating AI Viral Video Predictor..."

mkdir -p services/viral-predictor
mkdir -p services/viral-predictor/src
mkdir -p services/viral-predictor/src/api
mkdir -p services/viral-predictor/src/core
mkdir -p services/viral-predictor/src/model
mkdir -p services/viral-predictor/src/features
mkdir -p services/viral-predictor/src/training
mkdir -p services/viral-predictor/docker

# requirements.txt
cat > services/viral-predictor/requirements.txt << 'EOF'
fastapi
uvicorn
pydantic
numpy
pandas
scikit-learn
torch
psycopg2-binary
redis
EOF

# database layer
cat > services/viral-predictor/src/core/database.py << 'EOF'
import psycopg2
import os

def get_db():

    return psycopg2.connect(
        os.environ["DB_URL"]
    )
EOF

# feature extraction
cat > services/viral-predictor/src/features/features.py << 'EOF'
import numpy as np

def extract_features(video):

    views = video["views"]
    likes = video["likes"]
    comments = video["comments"]
    shares = video["shares"]

    engagement = (likes + comments + shares) / max(views,1)

    return np.array([
        views,
        likes,
        comments,
        shares,
        engagement
    ])
EOF

# model loader
cat > services/viral-predictor/src/model/model.py << 'EOF'
import torch
import torch.nn as nn


class ViralNet(nn.Module):

    def __init__(self):

        super().__init__()

        self.net = nn.Sequential(

            nn.Linear(5,64),
            nn.ReLU(),

            nn.Linear(64,32),
            nn.ReLU(),

            nn.Linear(32,1),
            nn.Sigmoid()

        )

    def forward(self,x):

        return self.net(x)


model = ViralNet()

def predict(features):

    x = torch.tensor(features).float()

    with torch.no_grad():

        score = model(x)

    return float(score)
EOF

# training pipeline
cat > services/viral-predictor/src/training/train.py << 'EOF'
import torch
import pandas as pd

from model.model import ViralNet


def train(datafile):

    df = pd.read_csv(datafile)

    X = df[["views","likes","comments","shares","engagement"]].values
    y = df["viral"].values

    model = ViralNet()

    optimizer = torch.optim.Adam(model.parameters())
    loss_fn = torch.nn.BCELoss()

    X = torch.tensor(X).float()
    y = torch.tensor(y).float().unsqueeze(1)

    for epoch in range(100):

        pred = model(X)

        loss = loss_fn(pred,y)

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()

    torch.save(model.state_dict(),"viral_model.pt")
EOF

# prediction API
cat > services/viral-predictor/src/api/server.py << 'EOF'
from fastapi import FastAPI
from pydantic import BaseModel

from features.features import extract_features
from model.model import predict

app = FastAPI()


class Video(BaseModel):

    views:int
    likes:int
    comments:int
    shares:int


@app.post("/predict")

def predict_viral(video:Video):

    features = extract_features(video.dict())

    score = predict(features)

    return {
        "viral_score":score
    }
EOF

# entrypoint
cat > services/viral-predictor/src/main.py << 'EOF'
import uvicorn

uvicorn.run(
"api.server:app",
host="0.0.0.0",
port=9100
)
EOF

# Dockerfile
cat > services/viral-predictor/docker/Dockerfile << 'EOF'
FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python","src/main.py"]
EOF

echo "STEP 12 COMPLETE"
echo "Generating AI Viral Video Predictor created"

echo "STEP 13 — zlttbots **Auto TikTok Posting Farm (1000 Accounts Orchestration)**"
echo "Generating TikTok Posting Farm..."

mkdir -p services/tiktok-farm
mkdir -p services/tiktok-farm/src
mkdir -p services/tiktok-farm/src/api
mkdir -p services/tiktok-farm/src/core
mkdir -p services/tiktok-farm/src/workers
mkdir -p services/tiktok-farm/src/uploader
mkdir -p services/tiktok-farm/src/models
mkdir -p services/tiktok-farm/docker

# package.json
cat > services/tiktok-farm/package.json << 'EOF'
{
"name": "zlttbots-tiktok-farm",
"version": "1.0.0",
"type": "module",
"scripts": {
"start": "node src/api/server.js",
"worker": "node src/workers/worker.js"
},
"dependencies": {
"express": "^4.19.2",
"playwright": "^1.43.0",
"pg": "^8.11.0",
"redis": "^4.6.0",
"axios": "^1.6.0",
"uuid": "^9.0.0"
}
}
EOF

# Redis Queue
cat > services/tiktok-farm/src/core/queue.js << 'EOF'
import { createClient } from "redis"

const client = createClient({
url: process.env.REDIS_URL
})

await client.connect()

export async function enqueue(job){

await client.lPush(
"video_jobs",
JSON.stringify(job)
)

}

export async function dequeue(){

const r = await client.rPop("video_jobs")

if(!r) return null

return JSON.parse(r)

}
EOF

# Database Layer
cat > services/tiktok-farm/src/core/database.js << 'EOF'
import pkg from "pg"

const { Pool } = pkg

export const db = new Pool({
connectionString: process.env.DB_URL
})
EOF

# Account Pool
cat > services/tiktok-farm/src/core/accounts.js << 'EOF'
import { db } from "./database.js"

export async function getAccount(){

const r = await db.query(
"select * from accounts where active=true order by random() limit 1"
)

return r.rows[0]

}
EOF

# Proxy Pool
cat > services/tiktok-farm/src/core/proxies.js << 'EOF'
import { db } from "./database.js"

export async function getProxy(){

const r = await db.query(
"select * from proxies where active=true order by random() limit 1"
)

return r.rows[0]

}
EOF

# Playwright Upload Automation
cat > services/tiktok-farm/src/uploader/uploader.js << 'EOF'
import { chromium } from "playwright"

export async function upload(account, proxy, video){

const browser = await chromium.launch({
proxy: proxy ? { server: proxy.host + ":" + proxy.port } : undefined,
headless: false
})

const context = await browser.newContext()

const page = await context.newPage()

await page.goto("https://www.tiktok.com/login")

await page.fill('input[name="username"]', account.username)
await page.fill('input[type="password"]', account.password)

await page.click('button[type="submit"]')

await page.waitForTimeout(5000)

await page.goto("https://www.tiktok.com/upload")

await page.setInputFiles('input[type="file"]', video.file)

await page.fill('[contenteditable="true"]', video.caption)

await page.click('button:has-text("Post")')

await page.waitForTimeout(8000)

await browser.close()

}
EOF

# Worker Node
cat > services/tiktok-farm/src/workers/worker.js << 'EOF'
import { dequeue } from "../core/queue.js"
import { getAccount } from "../core/accounts.js"
import { getProxy } from "../core/proxies.js"
import { upload } from "../uploader/uploader.js"

async function worker(){

while(true){

const job = await dequeue()

if(!job){

await new Promise(r=>setTimeout(r,5000))
continue

}

const account = await getAccount()
const proxy = await getProxy()

try{

await upload(account, proxy, job.video)

}catch(e){

console.error(e)

}

}

}

worker()
EOF

# Farm Controller API
cat > services/tiktok-farm/src/api/server.js << 'EOF'
import express from "express"
import { enqueue } from "../core/queue.js"

const app = express()

app.use(express.json())

app.post("/farm/job", async(req,res)=>{

await enqueue(req.body)

res.json({status:"queued"})

})

app.get("/farm/status",(req,res)=>{

res.json({
status:"running"
})

})

app.listen(9200)
EOF

# Dockerfile
cat > services/tiktok-farm/docker/Dockerfile << 'EOF'
FROM mcr.microsoft.com/playwright:v1.43.0-jammy

WORKDIR /app

COPY . .

RUN npm install

CMD ["npm","start"]
EOF

echo "STEP 13 COMPLETE"
echo "Generating TikTok Posting Farm created"

echo "STEP 14"
echo "Generating Distributed GPU Video Renderer..."

mkdir -p services/gpu-renderer/src
mkdir -p services/gpu-renderer/src/core
mkdir -p services/gpu-renderer/src/api
mkdir -p services/gpu-renderer/src/worker
mkdir -p services/gpu-renderer/docker

# requirements
cat > services/gpu-renderer/requirements.txt << 'EOF'
fastapi
uvicorn
redis
pydantic
EOF

# Redis queue
cat > services/gpu-renderer/src/core/queue.py << 'EOF'
import os
import json
import redis

r = redis.Redis.from_url(os.environ.get("REDIS_URL","redis://localhost:6379"))

def enqueue(job):
    r.lpush("render_jobs", json.dumps(job))

def dequeue():
    job = r.rpop("render_jobs")
    if not job:
        return None
    return json.loads(job)
EOF

# FFmpeg GPU renderer
cat > services/gpu-renderer/src/core/render.py << 'EOF'
import subprocess

def render(job):

    input_file = job["input"]
    output_file = job["output"]

    cmd = [
        "ffmpeg",
        "-y",
        "-hwaccel","cuda",
        "-i",input_file,
        "-c:v","h264_nvenc",
        "-preset","p4",
        "-b:v","5M",
        output_file
    ]

    subprocess.run(cmd, check=True)
EOF

# Worker
cat > services/gpu-renderer/src/worker/worker.py << 'EOF'
import time
from core.queue import dequeue
from core.render import render

def worker():

    while True:

        job = dequeue()

        if not job:
            time.sleep(3)
            continue

        try:
            render(job)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    worker()
EOF

# API Server
cat > services/gpu-renderer/src/api/server.py << 'EOF'
from fastapi import FastAPI
from pydantic import BaseModel
from core.queue import enqueue

app = FastAPI()

class Job(BaseModel):
    input:str
    output:str

@app.post("/render")

def render_video(job:Job):

    enqueue(job.dict())

    return {"status":"queued"}
EOF

# Entrypoint
cat > services/gpu-renderer/src/main.py << 'EOF'
import uvicorn

uvicorn.run(
    "api.server:app",
    host="0.0.0.0",
    port=9300
)
EOF

# Dockerfile (GPU)
cat > services/gpu-renderer/docker/Dockerfile << 'EOF'
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

RUN apt update && apt install -y \
    ffmpeg \
    python3 \
    python3-pip

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python3","src/main.py"]
EOF

echo "STEP 14 COMPLETE"
echo "Generating Distributed GPU Video Renderer created"

echo "STEP 15 — zlttbots **Multi-Marketplace Product Crawler (Shopee + Lazada + Amazon)**"
echo "Generating Multi Marketplace Crawler..."

mkdir -p services/market-crawler/src/api
mkdir -p services/market-crawler/src/core
mkdir -p services/market-crawler/src/workers
mkdir -p services/market-crawler/src/parsers
mkdir -p services/market-crawler/docker

# requirements
cat > services/market-crawler/requirements.txt << 'EOF'
fastapi
uvicorn
redis
psycopg2-binary
httpx
beautifulsoup4
pydantic
EOF

# Redis queue
cat > services/market-crawler/src/core/queue.py << 'EOF'
import redis
import os
import json

r = redis.Redis.from_url(
    os.environ.get("REDIS_URL","redis://localhost:6379")
)

def enqueue(job):
    r.lpush("crawl_jobs", json.dumps(job))

def dequeue():
    job = r.rpop("crawl_jobs")
    if not job:
        return None
    return json.loads(job)
EOF

# Database
cat > services/market-crawler/src/core/database.py << 'EOF'
import psycopg2
import os

def get_db():
    return psycopg2.connect(
        os.environ["DB_URL"]
    )

def insert_product(p):

    db = get_db()
    cur = db.cursor()

    cur.execute(
    """
    insert into products
    (id,name,price,rating,sold,source)
    values(%s,%s,%s,%s,%s,%s)
    on conflict(id) do update
    set price=excluded.price,
        rating=excluded.rating,
        sold=excluded.sold
    """,
    (
        p["id"],
        p["name"],
        p["price"],
        p["rating"],
        p["sold"],
        p["source"]
    ))

    db.commit()
EOF

# Shopee parser
cat > services/market-crawler/src/parsers/shopee.py << 'EOF'
import httpx

async def crawl_shopee(keyword):

    url = "https://shopee.co.th/api/v4/search/search_items"

    params = {
        "keyword": keyword,
        "limit": 50
    }

    r = httpx.get(url, params=params)

    items = r.json()["items"]

    products = []

    for i in items:

        products.append({
            "id": i["itemid"],
            "name": i["name"],
            "price": i["price"]/100000,
            "rating": i["item_rating"]["rating_star"],
            "sold": i["sold"],
            "source": "shopee"
        })

    return products
EOF

# Lazada parser
cat > services/market-crawler/src/parsers/lazada.py << 'EOF'
import httpx
from bs4 import BeautifulSoup

async def crawl_lazada(keyword):

    url = f"https://www.lazada.co.th/catalog/?q={keyword}"

    r = httpx.get(url)

    soup = BeautifulSoup(r.text,"html.parser")

    products = []

    cards = soup.select(".Bm3ON")

    for c in cards[:20]:

        name = c.select_one(".RfADt").text
        price = c.select_one(".ooOxS").text

        products.append({
            "id": name,
            "name": name,
            "price": price,
            "rating": 0,
            "sold": 0,
            "source": "lazada"
        })

    return products
EOF

# Amazon parser
cat > services/market-crawler/src/parsers/amazon.py << 'EOF'
import httpx
from bs4 import BeautifulSoup

async def crawl_amazon(keyword):

    url = f"https://www.amazon.com/s?k={keyword}"

    r = httpx.get(url)

    soup = BeautifulSoup(r.text,"html.parser")

    products = []

    cards = soup.select(".s-result-item")

    for c in cards[:20]:

        title = c.select_one("h2")

        if not title:
            continue

        products.append({
            "id": title.text,
            "name": title.text,
            "price": 0,
            "rating": 0,
            "sold": 0,
            "source": "amazon"
        })

    return products
EOF

# Worker
cat > services/market-crawler/src/workers/worker.py << 'EOF'
import asyncio

from core.queue import dequeue
from core.database import insert_product

from parsers.shopee import crawl_shopee
from parsers.lazada import crawl_lazada
from parsers.amazon import crawl_amazon

async def process(job):

    keyword = job["keyword"]

    data = []

    data += await crawl_shopee(keyword)
    data += await crawl_lazada(keyword)
    data += await crawl_amazon(keyword)

    for p in data:
        insert_product(p)

async def worker():

    while True:

        job = dequeue()

        if not job:
            await asyncio.sleep(5)
            continue

        try:
            await process(job)
        except Exception as e:
            print(e)

asyncio.run(worker())
EOF

# API Server
cat > services/market-crawler/src/api/server.py << 'EOF'
from fastapi import FastAPI
from pydantic import BaseModel

from core.queue import enqueue

app = FastAPI()

class CrawlJob(BaseModel):
    keyword:str

@app.post("/crawl")

def crawl(job:CrawlJob):

    enqueue(job.dict())

    return {"status":"queued"}
EOF

# Entrypoint
cat > services/market-crawler/src/main.py << 'EOF'
import uvicorn

uvicorn.run(
    "api.server:app",
    host="0.0.0.0",
    port=9400
)
EOF

# Dockerfile
cat > services/market-crawler/docker/Dockerfile << 'EOF'
FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python","src/main.py"]
EOF

echo "STEP 15 COMPLETE"
echo "Generating Multi-Marketplace Product Crawler (Shopee + Lazada + Amazon) created"

echo "STEP 16 — zlttbots **Real-Time Affiliate Arbitrage Engine**"
echo "Generating Affiliate Arbitrage Engine..."

mkdir -p services/arbitrage-engine/src/api
mkdir -p services/arbitrage-engine/src/core
mkdir -p services/arbitrage-engine/src/engine
mkdir -p services/arbitrage-engine/src/workers
mkdir -p services/arbitrage-engine/docker

# requirements
cat > services/arbitrage-engine/requirements.txt << 'EOF'
fastapi
uvicorn
psycopg2-binary
redis
numpy
pydantic
EOF

# database layer
cat > services/arbitrage-engine/src/core/database.py << 'EOF'
import psycopg2
import os

def get_db():
    return psycopg2.connect(os.environ["DB_URL"])

def fetch_products():

    db = get_db()
    cur = db.cursor()

    cur.execute("""
    select id,name,price,source
    from products
    """)

    rows = cur.fetchall()

    data = []

    for r in rows:
        data.append({
            "id": r[0],
            "name": r[1],
            "price": float(r[2]),
            "source": r[3]
        })

    return data

def insert_event(event):

    db = get_db()
    cur = db.cursor()

    cur.execute("""
    insert into arbitrage_events
    (product_name,buy_source,sell_source,buy_price,sell_price,profit)
    values(%s,%s,%s,%s,%s,%s)
    """,
    (
        event["product"],
        event["buy"],
        event["sell"],
        event["buy_price"],
        event["sell_price"],
        event["profit"]
    ))

    db.commit()
EOF

# commission calculator
cat > services/arbitrage-engine/src/engine/commission.py << 'EOF'
def commission_rate(source):

    if source == "shopee":
        return 0.07

    if source == "lazada":
        return 0.08

    if source == "amazon":
        return 0.05

    return 0.05
EOF

# arbitrage detector
cat > services/arbitrage-engine/src/engine/arbitrage.py << 'EOF'
from collections import defaultdict
from engine.commission import commission_rate

def detect(products):

    grouped = defaultdict(list)

    for p in products:
        grouped[p["name"]].append(p)

    opportunities = []

    for name,items in grouped.items():

        if len(items) < 2:
            continue

        for buy in items:

            for sell in items:

                if buy["source"] == sell["source"]:
                    continue

                buy_price = buy["price"]
                sell_price = sell["price"]

                commission = commission_rate(sell["source"])

                revenue = sell_price * commission

                profit = revenue - buy_price

                if profit > 1:

                    opportunities.append({
                        "product": name,
                        "buy": buy["source"],
                        "sell": sell["source"],
                        "buy_price": buy_price,
                        "sell_price": sell_price,
                        "profit": profit
                    })

    return opportunities
EOF

# worker
cat > services/arbitrage-engine/src/workers/worker.py << 'EOF'
import time

from core.database import fetch_products, insert_event
from engine.arbitrage import detect

def worker():

    while True:

        products = fetch_products()

        opportunities = detect(products)

        for o in opportunities:
            insert_event(o)

        time.sleep(30)

if __name__ == "__main__":
    worker()
EOF

# API server
cat > services/arbitrage-engine/src/api/server.py << 'EOF'
from fastapi import FastAPI
import psycopg2
import os

app = FastAPI()

def get_db():
    return psycopg2.connect(os.environ["DB_URL"])

@app.get("/arbitrage")

def list_events():

    db = get_db()
    cur = db.cursor()

    cur.execute("""
    select product_name,buy_source,sell_source,profit
    from arbitrage_events
    order by profit desc
    limit 50
    """)

    rows = cur.fetchall()

    result = []

    for r in rows:

        result.append({
            "product": r[0],
            "buy": r[1],
            "sell": r[2],
            "profit": float(r[3])
        })

    return result
EOF

# entrypoint
cat > services/arbitrage-engine/src/main.py << 'EOF'
import uvicorn

uvicorn.run(
    "api.server:app",
    host="0.0.0.0",
    port=9500
)
EOF

# Dockerfile
cat > services/arbitrage-engine/docker/Dockerfile << 'EOF'
FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python","src/main.py"]
EOF

echo "STEP 16 COMPLETE"
echo "Generating Affiliate Arbitrage Engine created"

echo "STEP 17 — zlttbots Full Project Startup Script"
echo "Generating full project start scripts..."

mkdir -p infrastructure/start

# Environment Generator
cat > infrastructure/start/env.sh << 'EOF'
#!/usr/bin/env bash

export DB_URL=postgresql://zlttbots:zlttbots@localhost:5432/zlttbots
export REDIS_URL=redis://localhost:6379
export GPU_RENDER=true
EOF

# Docker Compose (Full Platform)
cat > docker-compose.yml << 'EOF'
version: "3.9"

services:

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: zlttbots
      POSTGRES_USER: zlttbots
      POSTGRES_PASSWORD: zlttbots
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  viral-predictor:
    build: services/viral-predictor/docker
    environment:
      DB_URL: ${DB_URL}
    ports:
      - "9100:9100"

  gpu-renderer:
    build: services/gpu-renderer/docker
    environment:
      REDIS_URL: ${REDIS_URL}
    ports:
      - "9300:9300"

  market-crawler:
    build: services/market-crawler/docker
    environment:
      DB_URL: ${DB_URL}
      REDIS_URL: ${REDIS_URL}
    ports:
      - "9400:9400"

  arbitrage-engine:
    build: services/arbitrage-engine/docker
    environment:
      DB_URL: ${DB_URL}
    ports:
      - "9500:9500"

EOF

# Worker Startup
cat > infrastructure/start/workers.sh << 'EOF'
#!/usr/bin/env bash

echo "Starting crawler workers..."
python services/market-crawler/src/workers/worker.py &

echo "Starting arbitrage workers..."
python services/arbitrage-engine/src/workers/worker.py &

echo "Starting GPU renderer workers..."
python services/gpu-renderer/src/worker/worker.py &
EOF

# Main Startup Script
cat > start-zlttbots.sh << 'EOF'
# path: start-zlttbots.sh
#!/usr/bin/env bash
#
# Unified launcher for zlttbots
# Combines:
# - permission fix
# - env loader
# - dependency install
# - docker infra startup
# - image build
# - service startup
# - workers
# - DB migration
# - health checks

set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "================================="
echo "zlttbots Bootstrap"
echo "Root: $ROOT"
echo "================================="

################################
# Fix permissions
################################

echo "Fixing shell permissions..."
find "$ROOT" -type f -name "*.sh" -exec chmod +x {} \;

################################
# Load environment
################################

echo "Loading environment..."
if [ -f "$ROOT/infrastructure/start/env.sh" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/infrastructure/start/env.sh"
fi

################################
# Install Node dependencies
################################

echo ""
echo "Installing Node dependencies..."

NODE_PKGS=$(find "$ROOT/services" -maxdepth 2 -name package.json)

for pkg in $NODE_PKGS
do
  dir=$(dirname "$pkg")
  echo "npm install -> $dir"
  (cd "$dir" && npm install --silent)
done

################################
# Install Python dependencies
################################

echo ""
echo "Installing Python dependencies..."

PY_PKGS=$(find "$ROOT/services" -maxdepth 2 -name requirements.txt)

for req in $PY_PKGS
do
  dir=$(dirname "$req")
  echo "pip install -> $dir"
  (cd "$dir" && pip install -r requirements.txt)
done

################################
# Start infrastructure
################################

echo ""
echo "Starting infrastructure..."
docker compose up -d postgres redis

sleep 6

################################
# Build services
################################

echo ""
echo "Building services..."
docker compose build

################################
# Start services
################################

echo ""
echo "Starting services..."
docker compose up -d

################################
# Run DB migrations
################################

echo ""
echo "Running database migrations..."

MIG="$ROOT/infrastructure/postgres/migrations/001_schema.sql"

if [ -f "$MIG" ]; then
  CONTAINER=$(docker ps -qf name=postgres | head -n1 || true)

  if [ -n "$CONTAINER" ]; then
    docker exec -i "$CONTAINER" psql -U postgres -f /dev/stdin < "$MIG" || true
  fi
fi

################################
# Start background workers
################################

echo ""
echo "Starting background workers..."

if [ -f "$ROOT/infrastructure/start/workers.sh" ]; then
  bash "$ROOT/infrastructure/start/workers.sh"
fi

################################
# Health checks
################################

echo ""
echo "Running health checks..."

sleep 5

curl -fs http://localhost:9100/docs || true
curl -fs http://localhost:9400/docs || true
curl -fs http://localhost:9500/arbitrage || true

################################
# Status
################################

echo ""
echo "================================="
echo "zlttbots Started"
echo "================================="

echo ""
echo "Active containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
EOF


echo "================================="
echo "zlttbots Installer Completed"
echo "================================="
echo " # Make Executable"
echo " chmod +x start-zlttbots.sh"
echo " chmod +x infrastructure/start/env.sh"
echo " chmod +x infrastructure/start/workers.sh"
echo " "
echo " # Run Generator"
echo " ./generate-zlttbots.sh"
echo " "
echo " # Start Platform"
echo " ./start-zlttbots.sh"

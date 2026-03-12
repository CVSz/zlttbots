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

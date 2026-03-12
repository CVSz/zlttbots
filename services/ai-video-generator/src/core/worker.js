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

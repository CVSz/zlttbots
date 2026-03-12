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

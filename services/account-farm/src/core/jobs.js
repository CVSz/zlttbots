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

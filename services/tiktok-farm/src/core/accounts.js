import { db } from "./database.js"

export async function getAccount(){

const r = await db.query(
"select * from accounts where active=true order by random() limit 1"
)

return r.rows[0]

}

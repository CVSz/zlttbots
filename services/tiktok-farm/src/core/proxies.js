import { db } from "./database.js"

export async function getProxy(){

const r = await db.query(
"select * from proxies where active=true order by random() limit 1"
)

return r.rows[0]

}

import { db } from "../core/database.js"

export async function totalRevenue(){

const r = await db.query(
"select sum(amount) as revenue from orders"
)

return r.rows[0].revenue || 0

}

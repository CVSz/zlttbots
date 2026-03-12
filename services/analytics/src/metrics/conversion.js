import { db } from "../core/database.js"

export async function conversionRate(){

const clicks = await db.query("select count(*) from clicks")
const orders = await db.query("select count(*) from orders")

const c = Number(clicks.rows[0].count)
const o = Number(orders.rows[0].count)

if(c === 0) return 0

return o / c

}

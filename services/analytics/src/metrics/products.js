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

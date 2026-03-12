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

import { db } from "../core/database.js"

export async function farmHealth(){

const r = await db.query(
"select count(*) from accounts where active=true"
)

return {
active_accounts: Number(r.rows[0].count)
}

}

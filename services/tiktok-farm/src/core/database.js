import pkg from "pg"

const { Pool } = pkg

export const db = new Pool({
connectionString: process.env.DB_URL
})

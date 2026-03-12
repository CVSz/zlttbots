import express from "express"

import { scheduler } from "../scheduler/scheduler.js"
import { farmHealth } from "../monitor/health.js"

const app = express()

app.use(express.json())


app.get("/farm/health", async(req,res)=>{

const h = await farmHealth()

res.json(h)

})


app.post("/farm/run", async(req,res)=>{

await scheduler()

res.json({status:"ok"})

})


app.listen(7000)

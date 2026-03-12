import express from "express"
import { enqueue } from "../core/queue.js"

const app = express()

app.use(express.json())

app.post("/farm/job", async(req,res)=>{

await enqueue(req.body)

res.json({status:"queued"})

})

app.get("/farm/status",(req,res)=>{

res.json({
status:"running"
})

})

app.listen(9200)

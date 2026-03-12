import express from "express"

import { totalRevenue } from "../metrics/revenue.js"
import { conversionRate } from "../metrics/conversion.js"
import { campaignROI } from "../metrics/campaign.js"
import { productPerformance } from "../metrics/products.js"

const app = express()


app.get("/analytics/revenue", async(req,res)=>{

const r = await totalRevenue()

res.json({revenue:r})

})


app.get("/analytics/conversion", async(req,res)=>{

const r = await conversionRate()

res.json({conversion:r})

})


app.get("/analytics/campaigns", async(req,res)=>{

const r = await campaignROI()

res.json(r)

})


app.get("/analytics/products", async(req,res)=>{

const r = await productPerformance()

res.json(r)

})


app.listen(9000)

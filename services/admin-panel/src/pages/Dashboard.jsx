import React, { useEffect, useState } from "react"
import { api } from "../api/api.js"

export default function Dashboard(){

const [revenue,setRevenue] = useState(0)

useEffect(()=>{

api.get("/analytics/revenue")
.then(r=>setRevenue(r.data.revenue))

},[])

return(

<div>

<h2>Revenue</h2>

<p>{revenue}</p>

</div>

)

}

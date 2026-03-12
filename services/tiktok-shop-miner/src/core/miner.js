import { searchProducts } from "../crawler/search.js"
import { parseProduct } from "../parser/product.js"
import { scoreProduct } from "./trending.js"
import { db } from "./database.js"

export async function mine(keyword){

const products = await searchProducts(keyword)

for(const p of products){

const parsed = parseProduct(p)

const score = scoreProduct(parsed)

await db.query(
`insert into tiktok_products
(id,name,price,sales,rating,trend_score)
values($1,$2,$3,$4,$5,$6)
on conflict(id) do update
set price=$3,sales=$4,trend_score=$6`,
[
parsed.id,
parsed.name,
parsed.price,
parsed.sales,
parsed.rating,
score
]
)

}

}

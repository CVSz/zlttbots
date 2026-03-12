import { searchProducts } from "../crawler/search.js"
import { parseProduct } from "../parser/product.js"
import { db } from "./database.js"
import { generateAffiliateLink } from "./affiliate.js"

export async function crawl(keyword){

const products = await searchProducts(keyword)

for(const p of products){

const parsed = parseProduct(p)

const link = generateAffiliateLink(parsed.id)

await db.query(
`insert into products
(id,name,price,sold,rating,affiliate_link)
values($1,$2,$3,$4,$5,$6)
on conflict(id) do update
set price=$3,sold=$4`,
[
parsed.id,
parsed.name,
parsed.price,
parsed.sold,
parsed.rating,
link
]
)

}

}

export function parseProduct(raw){

return {
id: raw.product_id,
name: raw.title,
price: raw.price,
sales: raw.sales,
rating: raw.rating
}

}

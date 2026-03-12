export function parseProduct(raw){

return {
id: raw.itemid,
name: raw.name,
price: raw.price/100000,
sold: raw.sold,
rating: raw.item_rating.rating_star
}

}

import axios from "axios"

export async function searchProducts(keyword){

const url = "https://shop.tiktok.com/api/search"

const res = await axios.get(url,{
params:{
keyword:keyword,
limit:50
}
})

return res.data.products || []

}

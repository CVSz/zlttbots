import axios from "axios"

export async function searchProducts(keyword){

const url = "https://shopee.co.th/api/v4/search/search_items"

const res = await axios.get(url,{
params:{
keyword:keyword,
limit:50
}
})

return res.data.items

}

import { chromium } from "playwright"

export async function createBrowser(proxy){

return await chromium.launch({
headless:false,
proxy: proxy ? {server:proxy} : undefined
})

}

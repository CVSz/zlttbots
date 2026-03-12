import { chromium } from "playwright"

export async function upload(account, proxy, video){

const browser = await chromium.launch({
proxy: proxy ? { server: proxy.host + ":" + proxy.port } : undefined,
headless: false
})

const context = await browser.newContext()

const page = await context.newPage()

await page.goto("https://www.tiktok.com/login")

await page.fill('input[name="username"]', account.username)
await page.fill('input[type="password"]', account.password)

await page.click('button[type="submit"]')

await page.waitForTimeout(5000)

await page.goto("https://www.tiktok.com/upload")

await page.setInputFiles('input[type="file"]', video.file)

await page.fill('[contenteditable="true"]', video.caption)

await page.click('button:has-text("Post")')

await page.waitForTimeout(8000)

await browser.close()

}

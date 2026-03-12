export async function login(page, account){

await page.goto("https://www.tiktok.com/login")

await page.fill('input[name="username"]', account.username)

await page.fill('input[type="password"]', account.password)

await page.click('button[type="submit"]')

await page.waitForTimeout(5000)

}

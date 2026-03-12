export async function uploadVideo(page, video){

await page.goto("https://www.tiktok.com/upload")

await page.setInputFiles('input[type="file"]', video.file)

await page.fill('[contenteditable="true"]', video.caption)

await page.click('button:has-text("Post")')

await page.waitForTimeout(8000)

}

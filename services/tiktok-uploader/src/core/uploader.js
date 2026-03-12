import { createBrowser } from "./browser.js"
import { login } from "../automation/login.js"
import { uploadVideo } from "../automation/upload.js"

export async function runUploader(account, video){

const browser = await createBrowser(account.proxy)

const context = await browser.newContext()

const page = await context.newPage()

await login(page, account)

await uploadVideo(page, video)

await browser.close()

}

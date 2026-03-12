import axios from "axios"

import { getAccount } from "../core/accounts.js"
import { getProxy } from "../core/proxy.js"
import { nextJob, completeJob } from "../core/jobs.js"

export async function worker(){

const job = await nextJob()

if(!job) return

const account = await getAccount()

const proxy = await getProxy()

await axios.post(
"http://tiktok-uploader:3000/upload",
{
account,
proxy,
video: job.video
}
)

await completeJob(job.id)

}

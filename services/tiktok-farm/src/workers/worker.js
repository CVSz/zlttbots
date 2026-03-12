import { dequeue } from "../core/queue.js"
import { getAccount } from "../core/accounts.js"
import { getProxy } from "../core/proxies.js"
import { upload } from "../uploader/uploader.js"

async function worker(){

while(true){

const job = await dequeue()

if(!job){

await new Promise(r=>setTimeout(r,5000))
continue

}

const account = await getAccount()
const proxy = await getProxy()

try{

await upload(account, proxy, job.video)

}catch(e){

console.error(e)

}

}

}

worker()

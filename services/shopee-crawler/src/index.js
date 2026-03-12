import { scheduler } from "./core/scheduler.js"

async function main(){

while(true){

await scheduler()

await new Promise(r=>setTimeout(r,3600000))

}

}

main()

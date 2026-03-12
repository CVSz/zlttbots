import { worker } from "./core/worker.js"

async function main(){

while(true){

try{

await worker()

}catch(e){

console.error(e)

}

await new Promise(r=>setTimeout(r,10000))

}

}

main()

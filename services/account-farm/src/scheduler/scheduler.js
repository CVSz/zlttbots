import { worker } from "./worker.js"

export async function scheduler(){

for(let i=0;i<5;i++){

try{

await worker()

}catch(e){

console.error(e)

}

}

}

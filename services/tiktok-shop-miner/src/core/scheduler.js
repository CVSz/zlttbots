import { mine } from "./miner.js"

const KEYWORDS = [
"beauty",
"gadget",
"kitchen",
"fashion",
"fitness"
]

export async function scheduler(){

for(const k of KEYWORDS){

try{

await mine(k)

}catch(e){

console.error(e)

}

}

}

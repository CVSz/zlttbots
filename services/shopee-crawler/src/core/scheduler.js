import { crawl } from "./crawler.js"

const KEYWORDS = [
"beauty",
"gadget",
"kitchen",
"fitness",
"fashion"
]

export async function scheduler(){

for(const k of KEYWORDS){

try{

await crawl(k)

}catch(e){

console.error(e)

}

}

}

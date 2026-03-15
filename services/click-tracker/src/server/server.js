import http from "http"
import { trackClick } from "../core/tracker.js"

function isLocalUrl(path) {

try{
  const base = "http://localhost"
  const parsed = new URL(path, base)
  return parsed.origin === base && parsed.pathname.startsWith("/")
}catch(e){
  return false
}

}

const server = http.createServer(async (req,res)=>{

try{

const url = new URL(req.url,"http://localhost")

if(url.pathname.startsWith("/r/")){

const campaign = url.pathname.split("/")[2]

const target = url.searchParams.get("to")

const redirect = await trackClick(req,campaign,target)

const location = isLocalUrl(redirect) ? redirect : "/"

res.writeHead(302,{
Location: location
})

res.end()

return

}

res.writeHead(404)
res.end()

}catch(e){

console.error(e)

res.writeHead(500)
res.end()

}

})

server.listen(8080)

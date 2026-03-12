import { db } from "./database.js"
import geoip from "geoip-lite"
import { fingerprint } from "../utils/fingerprint.js"

export async function trackClick(req, campaign, target){

const ip = req.socket.remoteAddress
const ua = req.headers["user-agent"] || ""

const geo = geoip.lookup(ip)

const fp = fingerprint(ip, ua)

await db.query(
`insert into clicks
(campaign_id,ip,country,user_agent,fingerprint)
values($1,$2,$3,$4,$5)`,
[
campaign,
ip,
geo ? geo.country : null,
ua,
fp
]
)

return target

}

import { db } from "./database.js"
import geoip from "geoip-lite"
import { fingerprint } from "../utils/fingerprint.js"

function normalizeRedirectTarget(target) {
  if (!target) return null

  try {
    const parsed = new URL(target)
    return parsed.toString()
  } catch (error) {
    return null
  }
}

export async function trackClick(req, campaign, target) {
  const ip = req.socket.remoteAddress
  const ua = req.headers["user-agent"] || ""
  const geo = geoip.lookup(ip)
  const fp = fingerprint(ip, ua)
  const redirectTarget = normalizeRedirectTarget(target)

  await db.query(
    `insert into clicks
    (campaign_id, ip, country, user_agent, fingerprint, target_url)
    values($1, $2, $3, $4, $5, $6)`,
    [campaign, ip, geo ? geo.country : null, ua, fp, redirectTarget]
  )

  return redirectTarget
}

export async function resolveProductRedirect(productId) {
  const result = await db.query(
    `select affiliate_link
     from products
     where id = $1
     limit 1`,
    [productId]
  )

  return result.rows[0]?.affiliate_link || null
}

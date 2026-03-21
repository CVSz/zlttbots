import http from "http"
import { trackClick, resolveProductRedirect } from "../core/tracker.js"

const allowedHosts = (process.env.CLICK_TRACKER_ALLOWED_HOSTS || "")
  .split(",")
  .map((value) => value.trim())
  .filter(Boolean)

function isAllowedRedirect(target) {
  if (!target) return false

  try {
    const parsed = new URL(target)

    if (allowedHosts.length === 0) {
      return parsed.protocol === "https:"
    }

    return allowedHosts.includes(parsed.hostname)
  } catch (error) {
    return false
  }
}

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, { "Content-Type": "application/json" })
  res.end(JSON.stringify(payload))
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, "http://localhost")

    if (url.pathname === "/healthz") {
      return sendJson(res, 200, { ok: true })
    }

    if (url.pathname.startsWith("/r/")) {
      const campaign = url.pathname.split("/")[2]
      const target = url.searchParams.get("to")
      const redirect = await trackClick(req, campaign, target)

      if (!isAllowedRedirect(redirect)) {
        return sendJson(res, 400, { error: "redirect target is not allowed" })
      }

      res.writeHead(302, { Location: redirect })
      res.end()
      return
    }

    if (url.pathname.startsWith("/go/")) {
      const [, , campaign, productId] = url.pathname.split("/")

      if (!campaign || !productId) {
        return sendJson(res, 400, { error: "campaign and product id are required" })
      }

      const target = await resolveProductRedirect(productId)
      const redirect = await trackClick(req, campaign, target)

      if (!isAllowedRedirect(redirect)) {
        return sendJson(res, 404, { error: "approved affiliate link not found" })
      }

      res.writeHead(302, { Location: redirect })
      res.end()
      return
    }

    sendJson(res, 404, { error: "not found" })
  } catch (error) {
    console.error(error)
    sendJson(res, 500, { error: "internal server error" })
  }
})

server.listen(8080)

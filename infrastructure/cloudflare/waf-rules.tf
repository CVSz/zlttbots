terraform {
  required_version = ">= 1.5.0"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.37"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

resource "cloudflare_ruleset" "zttato_waf" {
  zone_id = var.cloudflare_zone_id
  name    = "zlttbots-waf"
  kind    = "zone"
  phase   = "http_request_firewall_custom"

  rules {
    action      = "block"
    expression  = "(cf.threat_score gt 15)"
    description = "Block high threat score traffic"
    enabled     = true
  }

  rules {
    action      = "challenge"
    expression  = "(http.request.uri.path contains \"/auth/token\" and ip.geoip.country in {\"CN\" \"RU\"})"
    description = "Challenge sensitive auth endpoint from high-risk geos"
    enabled     = true
  }

  rules {
    action      = "block"
    expression  = "(http.request.uri.path contains \"/wp-admin\" or http.request.uri.path contains \"/.env\")"
    description = "Block common bot reconnaissance paths"
    enabled     = true
  }

  rules {
    action      = "managed_challenge"
    expression  = "(http.request.uri.path matches \"^/api/\" and not cf.client.bot)"
    description = "Apply managed challenge to API traffic by default"
    enabled     = true
  }
}

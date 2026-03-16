variable "cloudflare_api_token" {
  type        = string
  sensitive   = true
  description = "Cloudflare API token with Zone WAF edit permissions"
}

variable "cloudflare_zone_id" {
  type        = string
  description = "Cloudflare zone ID"
}

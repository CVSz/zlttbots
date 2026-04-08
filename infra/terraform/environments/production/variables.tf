variable "kubeconfig_path" {
  type        = string
  description = "Path to kubeconfig for target cluster"
}

variable "namespace" {
  type        = string
  default     = "zlttbots"
  description = "Namespace for deployed workloads"
}

variable "image_tag" {
  type        = string
  description = "Container image tag for arbitrage engine"
}

variable "db_url" {
  type        = string
  description = "Database URL for application"
  sensitive   = true
}

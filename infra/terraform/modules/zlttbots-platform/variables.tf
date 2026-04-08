variable "namespace" {
  type        = string
  description = "Kubernetes namespace for zlttbots workloads"
  default     = "zlttbots"
}

variable "chart_path" {
  type        = string
  description = "Path to the Helm chart"
}

variable "image_tag" {
  type        = string
  description = "Arbitrage engine image tag"
}

variable "db_url" {
  type        = string
  description = "Database URL for arbitrage engine"
  sensitive   = true
}

variable "argocd_namespace" {
  type        = string
  description = "Namespace where Argo CD is deployed"
  default     = "argocd"
}

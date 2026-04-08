output "namespace" {
  value       = kubernetes_namespace.zlttbots.metadata[0].name
  description = "Namespace where zlttbots is deployed"
}

output "release_name" {
  value       = helm_release.zlttbots.name
  description = "Helm release name"
}

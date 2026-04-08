resource "kubernetes_namespace" "zlttbots" {
  metadata {
    name = var.namespace
  }
}

resource "kubernetes_secret" "zlttbots_secrets" {
  metadata {
    name      = "zlttbots-secrets"
    namespace = kubernetes_namespace.zlttbots.metadata[0].name
  }

  data = {
    DB_URL = var.db_url
  }

  type = "Opaque"
}

resource "helm_release" "zlttbots" {
  name             = "zlttbots"
  namespace        = kubernetes_namespace.zlttbots.metadata[0].name
  create_namespace = false
  chart            = var.chart_path

  values = [yamlencode({
    namespace = var.namespace
    image = {
      tag = var.image_tag
    }
  })]

  depends_on = [kubernetes_secret.zlttbots_secrets]
}

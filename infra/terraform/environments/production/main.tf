terraform {
  required_version = ">= 1.7.0"

  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.14"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}

module "zlttbots_platform" {
  source      = "../../modules/zlttbots-platform"
  namespace   = var.namespace
  chart_path  = "${path.root}/../../../../deploy/helm/zlttbots"
  image_tag   = var.image_tag
  db_url      = var.db_url
}

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

resource "google_compute_instance" "vm" {
  name         = "zttato-free"
  machine_type = "e2-micro"
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  tags = ["http-server"]

  metadata_startup_script = <<-EOF
    #!/bin/bash
    set -eux
    apt update
    apt install -y docker.io docker-compose-v2 git
    systemctl enable docker
    systemctl start docker
    cd /opt
    rm -rf zlttbots
    git clone https://github.com/cvsz/zlttbots.git
    cd zlttbots
    docker compose -f infra/docker-compose.yml up -d
  EOF
}

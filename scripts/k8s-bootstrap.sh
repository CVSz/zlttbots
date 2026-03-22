#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must run as root." >&2
  exit 1
fi

apt-get update
apt-get install -y containerd kubeadm kubelet kubectl curl

mkdir -p /etc/containerd
containerd config default >/etc/containerd/config.toml
systemctl restart containerd
systemctl enable containerd

kubeadm init --pod-network-cidr=10.244.0.0/16

export KUBECONFIG=/etc/kubernetes/admin.conf
mkdir -p "${HOME}/.kube"
cp /etc/kubernetes/admin.conf "${HOME}/.kube/config"
chown "$(id -u):$(id -g)" "${HOME}/.kube/config"

kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml

echo "Worker join command:"
kubeadm token create --print-join-command

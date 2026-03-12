#!/usr/bin/env bash

set -e

DEPLOYMENT=$1

kubectl rollout undo deployment/$DEPLOYMENT

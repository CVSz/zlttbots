#!/usr/bin/env bash

set -e

services=(
analytics
click-tracker
tiktok-uploader
ai-video-generator
shopee-crawler
tiktok-shop-miner
account-farm
admin-panel
)

for s in "${services[@]}"
do

docker build -t zlttbots/$s services/$s

done

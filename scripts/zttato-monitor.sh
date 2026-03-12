#!/usr/bin/env bash

clear

while true
do

clear

echo "=============================="
echo "zTTato Platform Monitor"
echo "=============================="

echo
echo "Docker"

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}"

echo
echo "CPU / Memory"

top -bn1 | head -5

echo
echo "API Latency"

curl -o /dev/null -s -w "viral %{time_total}s\n" http://localhost:9100/docs
curl -o /dev/null -s -w "crawler %{time_total}s\n" http://localhost:9400/docs
curl -o /dev/null -s -w "arbitrage %{time_total}s\n" http://localhost:9500/docs
curl -o /dev/null -s -w "renderer %{time_total}s\n" http://localhost:9300/docs

echo
echo "Edge"

curl -o /dev/null -s -w "api edge %{time_total}s\n" https://api.zeaz.dev

sleep 5

echo
echo "Node Services"

ps aux | grep node | grep -v grep | head

echo
echo "Node Memory"

ps -o pid,%mem,%cpu,cmd -C node

done

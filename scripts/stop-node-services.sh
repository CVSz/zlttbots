#!/usr/bin/env bash

echo "Stopping Node services..."

pkill -f "npm run start" || true
pkill -f "npm run dev" || true
pkill -f "node" || true

echo "Done."

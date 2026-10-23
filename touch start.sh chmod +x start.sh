#!/usr/bin/env bash
set -e

echo "[start] installing system deps..."
apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl ca-certificates || true

echo "[start] installing python deps..."
pip install --no-cache-dir -r requirements.txt

echo "[start] launching bot..."
exec python bot.py

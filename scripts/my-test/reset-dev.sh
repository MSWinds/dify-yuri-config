#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../docker"
docker-compose down
sudo rm -rf ./volumes/db/data ./volumes/weaviate ./volumes/redis/data
docker-compose up -d
echo "Reset done."

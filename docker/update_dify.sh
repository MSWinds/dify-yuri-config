#!/bin/bash

# 1. Pull the latest code
echo "📥 Pulling latest code..."
git pull

# 2. Update and restart containers with the latest images
echo "🚀 Updating and restarting Docker containers..."
docker-compose up -d --pull always

# 3. Clean up old/unused images to save space
echo "🧹 Cleaning up unused images..."
docker image prune -f

echo "✅ Dify update complete!"

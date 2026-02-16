#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "=== Dify Upgrade Script ==="
echo ""

# 0. Pre-flight: backup
echo "[0/6] Backing up .env and docker-compose.yaml ..."
cp .env ".env.backup.$(date +%Y-%m-%d)" 2>/dev/null || true
cp docker-compose.yaml "docker-compose.yaml.backup.$(date +%Y-%m-%d)" 2>/dev/null || true

# 1. Pull the latest code
echo "[1/6] Pulling latest code ..."
cd ..
git pull
cd docker

# 2. Check for entrypoint queue drift (the #1 silent failure source)
echo "[2/6] Checking Celery queue drift ..."
REPO_QUEUES=$(grep 'DEFAULT_QUEUES=' ../api/docker/entrypoint.sh | grep -v CLOUD | grep -v '#' | head -1 | sed 's/.*DEFAULT_QUEUES="//' | sed 's/"//')
COMPOSE_QUEUES=$(grep 'CELERY_QUEUES:' docker-compose.yaml | head -1 | sed 's/.*CELERY_QUEUES: *//' | tr -d '"' | tr -d "'" || echo "")

if [ -z "$COMPOSE_QUEUES" ]; then
    echo "  WARNING: CELERY_QUEUES is NOT set in docker-compose.yaml."
    echo "  The worker will use the image's built-in queue list, which may be outdated."
    echo "  Repo expects: $REPO_QUEUES"
    echo ""
    echo "  ACTION REQUIRED: Add CELERY_QUEUES to worker service in docker-compose.yaml"
    echo "  Press Enter to continue anyway, or Ctrl+C to abort."
    read -r
elif [ "$COMPOSE_QUEUES" != "$REPO_QUEUES" ]; then
    echo "  MISMATCH detected!"
    echo "  docker-compose.yaml: $COMPOSE_QUEUES"
    echo "  api/docker/entrypoint.sh: $REPO_QUEUES"
    echo ""
    echo "  ACTION REQUIRED: Update CELERY_QUEUES in docker-compose.yaml to match."
    echo "  Press Enter to continue anyway, or Ctrl+C to abort."
    read -r
else
    echo "  OK - queues are in sync."
fi

# 3. Check for new .env variables
echo "[3/6] Checking for new .env variables ..."
if [ -f .env.example ]; then
    NEW_VARS=$(diff <(grep -oP '^[A-Z_]+=' .env 2>/dev/null | sort) \
                    <(grep -oP '^[A-Z_]+=' .env.example | sort) \
               | grep '^>' | sed 's/^> //' || true)
    if [ -n "$NEW_VARS" ]; then
        echo "  New variables in .env.example (may need to add to .env):"
        echo "$NEW_VARS" | sed 's/^/    /'
    else
        echo "  OK - no new variables."
    fi
fi

# 4. Update containers
echo "[4/6] Updating containers (docker compose up -d) ..."
docker compose up -d --pull always

# 5. Run DB migrations
echo "[5/6] Running database migrations ..."
docker compose exec api flask db upgrade

# 6. Smoke test
echo "[6/6] Quick smoke test ..."
sleep 5

# Check worker queues
ACTUAL_QUEUES=$(docker compose logs worker --tail 20 2>&1 | grep "Starting Celery worker with queues" | tail -1 | sed 's/.*queues: //')
if echo "$ACTUAL_QUEUES" | grep -q "workflow_based_app_execution"; then
    echo "  Worker queues: OK (includes workflow_based_app_execution)"
else
    echo "  WARNING: Worker may be missing workflow_based_app_execution queue!"
    echo "  Actual queues: $ACTUAL_QUEUES"
fi

# Health check
API_HEALTH=$(curl -s --max-time 5 http://localhost:5001/health 2>/dev/null || echo "FAILED")
if echo "$API_HEALTH" | grep -q '"status": "ok"'; then
    echo "  API health: OK"
else
    echo "  WARNING: API health check failed: $API_HEALTH"
fi

echo ""
echo "=== Upgrade complete ==="
echo "REMINDER: Test chatflow, agent, and workflow apps manually!"
echo "See docs/yuri-config/OUR_FORK_OVERVIEW.md for full checklist."

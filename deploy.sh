#!/bin/sh
set -u

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR" || exit 1

API_PORT="${API_PORT:-9000}"

# Stop/remove previous stack if any, regardless of state
docker compose down -v 2>/dev/null || true

# Build + bring up
docker compose build --no-cache
docker compose up -d

echo "Waiting for db health..."
docker compose ps --format '{{.Name}} {{.Health}}'

# Wait max ~120s for api healthy
for i in $(seq 1 40); do
  if [ "$(docker compose ps -q api | xargs -I{} docker inspect -f '{{.State.Health.Status}}' {} 2>/dev/null || echo starting)" = "healthy" ]; then
    break
  fi
  if [ "$i" -eq 40 ]; then
    echo "api did not reach healthy state"
    docker compose logs api --tail 100 || true
    exit 1
  fi
  sleep 3
done

echo "Stack is up. Port: ${API_PORT}"
docker compose ps

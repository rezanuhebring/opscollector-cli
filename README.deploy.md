# OpsCollector Sync Server — Docker Deploy

## Prereqs
- Docker / Docker Compose
- Linux VPS with internet egress to pull images

## Files
- `Dockerfile`
- `docker-compose.yml`
- `deploy.sh`
- `server/requirements.txt`

## Quickstart
1) `cp .env.example .env` and edit creds if needed (defaults are fine for internal).
2) `chmod +x deploy.sh && ./deploy.sh`
3) Wait for healthy:
   docker compose ps
4) Base URL for clients:
   http://<vps-lan-ip>:${API_PORT:-9000}/api/v1

## Env
- `API_PORT` host port mapped to api container `8000`.
- Internals: db on 5432 internal only; bearer auth enforced by FastAPI.

## Notes
- No TLS; intended for internal/LAN or VPN.
- Bearer token issued via `/api/v1/register`.

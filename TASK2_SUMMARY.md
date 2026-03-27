# Task 2 — Deploy Agent and Add Web Client

## Summary

Deployed nanobot as a Docker service with WebSocket channel for web clients.

## Changes

- Added nanobot-websocket-channel as git submodule
- Installed webchat plugin into nanobot
- Enabled Flutter web client in docker-compose.yml
- Configured Caddy routes for /ws/chat and /flutter
- Updated nanobot config with webchat channel

## Architecture

```
Flutter Web → Caddy (/flutter) → WebSocket
                              ↓
Caddy (/ws/chat) → nanobot webchat channel → Agent
```

## Access

- Flutter UI: http://localhost:42002/flutter
- WebSocket: ws://localhost:42002/ws/chat?access_key=KEY

## Testing

```bash
docker compose --env-file .env.docker.secret ps
# All services should be running
```

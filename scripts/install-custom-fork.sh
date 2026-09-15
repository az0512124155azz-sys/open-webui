#!/usr/bin/env bash
set -euo pipefail

printf 'Open WebUI Custom Fork v1 installer\n'

if ! command -v docker >/dev/null 2>&1; then
  printf 'Docker was not found. Install Docker Engine/Desktop and try again.\n' >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  printf 'Docker is installed but is not running. Start Docker and try again.\n' >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  printf 'Created .env from .env.example.\n'
fi

compose=(docker compose)
case "${OPEN_WEBUI_GPU:-}" in
  nvidia) compose+=(-f docker-compose.yaml -f docker-compose.gpu.yaml) ;;
  amd) compose+=(-f docker-compose.yaml -f docker-compose.amdgpu.yaml) ;;
  '') ;;
  *) printf 'Unknown OPEN_WEBUI_GPU=%s (use nvidia or amd).\n' "$OPEN_WEBUI_GPU" >&2; exit 1 ;;
esac

compose+=(up -d --build)
printf 'Building and starting Open WebUI, Ollama and LibreTranslate...\n'
"${compose[@]}"

printf '\nInstallation complete.\n'
printf 'Open WebUI:       http://localhost:3000\n'
printf 'LibreTranslate:   http://127.0.0.1:5000\n'
printf '\nOptional: OPEN_WEBUI_GPU=nvidia or OPEN_WEBUI_GPU=amd before running this script.\n'

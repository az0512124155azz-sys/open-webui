#!/usr/bin/env bash
set -euo pipefail

OPEN_WEBUI_BASE="${OPEN_WEBUI_BASE:-http://localhost:3000}"
OLLAMA_BASE="${OLLAMA_BASE:-http://localhost:11434}"
LIBRETRANSLATE_BASE="${LIBRETRANSLATE_BASE:-http://localhost:5000}"

pass() { printf 'PASS: %s\n' "$1"; }
warn() { printf 'WARN: %s\n' "$1" >&2; }

if command -v docker >/dev/null 2>&1; then
  docker compose config >/dev/null
  pass 'docker compose configuration'
else
  warn 'docker not installed; compose validation skipped'
fi

if curl -fsS "${OPEN_WEBUI_BASE}/health" >/dev/null; then
  pass 'Open WebUI health endpoint'
else
  warn "Open WebUI is not reachable at ${OPEN_WEBUI_BASE}; runtime health check skipped"
fi

if curl -fsS "${OLLAMA_BASE}/api/ps" >/dev/null; then
  pass 'Ollama /api/ps'
else
  warn "Ollama is not reachable at ${OLLAMA_BASE}; Ollama runtime check skipped"
fi

if curl -fsS "${LIBRETRANSLATE_BASE}/languages" >/dev/null; then
  pass 'LibreTranslate languages endpoint'

  HE_TO_EN="$(curl -fsS -X POST "${LIBRETRANSLATE_BASE}/translate" \
    -H 'Content-Type: application/json' \
    -d '{"q":"שלום","source":"he","target":"en","format":"text"}')"
  EN_TO_HE="$(curl -fsS -X POST "${LIBRETRANSLATE_BASE}/translate" \
    -H 'Content-Type: application/json' \
    -d '{"q":"hello","source":"en","target":"he","format":"text"}')"

  [[ "${HE_TO_EN}" == *translatedText* ]] && pass 'LibreTranslate Hebrew to English'
  [[ "${EN_TO_HE}" == *translatedText* ]] && pass 'LibreTranslate English to Hebrew'
else
  warn "LibreTranslate is not reachable at ${LIBRETRANSLATE_BASE}; translation runtime checks skipped"
fi

printf 'Custom fork smoke checks completed.\n'

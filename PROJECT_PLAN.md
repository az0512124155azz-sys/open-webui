# Project Plan — Open WebUI Custom Fork v1

## Vision
Production-ready, privacy/local-first fork of Open WebUI (keep original UI/UX; extend with Ollama, translation, files/3D, plugins, skills, model intelligence, projects, offline-first).

## Repository
- Fork: https://github.com/az0512124155azz-sys/open-webui
- Upstream: https://github.com/open-webui/open-webui
- Branch: `feature/custom-fork-v1`
- PR: #1 (Draft — do not merge without explicit approval)

## Core rules
- Do not restart, redesign, or replace Open WebUI UI.
- Do not remove upstream features.
- Integrate new features into existing Settings/Chat/Admin components.
- Do not weaken CI (no continue-on-error, no removing checks).
- Duplicate Model Detector: informational only.
- Safe Mode: disable integrations, never delete config.
- Temporary Chats: no history/memory unless converted.
- Compare Models / Auto Merge: opt-in per chat.

## Implemented areas (audit in Stage 2)
Ollama performance, Hebrew↔English translation + LibreTranslate, chat-linked memory, extended file preview, 3D (STL/OBJ), downloads, Docker/GPU/AMD, Hebrew i18n, install scripts, README.

## Stages
1. Stabilize CI (current)
2. Existing feature audit
3. Plugins platform
4. Skills platform
5. Create Skill with AI
6. Model intelligence (router, fallback, benchmark, health, warmup, update checker, duplicate detector)
7. Advanced chat (context optimizer, compare, merge, prompt versions, snapshots)
8. Temporary / Safe Mode / Audit / Recovery
9. Files & Projects
10. Global search + offline-first
11. Queue + orchestration
12. Production hardening
13. Final QA

## Stage 1 DoD
Tests, Python CI, Frontend Build, Custom Fork QA all green without disabling checks or bypassing TypeScript/Svelte for custom code.

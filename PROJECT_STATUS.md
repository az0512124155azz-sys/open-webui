# Custom Fork – Project Status

Branch: `feature/custom-fork-v1`
Repo: `az0512124155azz-sys/open-webui`

| Stage | Name | Status |
|------:|------|--------|
| 1 | CI stabilization | Done |
| 2 | Feature audit | Done |
| 3 | Plugins Foundation | Done |
| 4 | Skills Foundation | Done |
| 5 | AI Skill creation | Done |
| 6 | Model Intelligence | Done |
| 7 | Advanced Chat Intelligence | Done |
| 8 | Temporary / Privacy / Recovery | Done |
| 9 | Files & Projects | Done |
| 10 | Global Search + Offline-first | Done |
| 11 | Queue + Orchestration | Done |
| 12 | Production Hardening | Done |
| 13 | Final QA | Done |

## main.py routers (required)

```
skills_ai          /api/v1/skills
plugins            /api/v1/plugins
model_intelligence /api/v1/model-intelligence
chat_intelligence  /api/v1/chat-intelligence
privacy_recovery   /api/v1/privacy
files_projects     /api/v1/files-projects
search_offline     /api/v1/search
job_queue          /api/v1/jobs
production_hardening /api/v1/hardening
```

## Notes

- Process-local stores are intentional for this phase.
- Do not redesign core Open WebUI UI/architecture.
- Do not run `npm audit fix --force` without full check/build validation.

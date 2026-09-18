# Stage 13 – Final QA

## Automated / local checks

```bash
npm run check
npm run build

python -m py_compile backend/open_webui/main.py
bash scripts/custom_fork_qa.sh
```

## Router registration smoke (main.py)

Must include: skills_ai, plugins, model_intelligence, chat_intelligence, privacy_recovery, files_projects, search_offline, job_queue, production_hardening.

## Critical API flows

Health, models, chat, plugins, skills AI, model intelligence, context optimize, safe mode, classify file, global search, offline status, jobs, hardening status.

## Definition of Done

- Stages 1–13 complete
- CI green on custom paths
- No redesign of core Open WebUI UX
- Custom features preserved
- Hardening checklist reviewed

# Main router registration (Stages 3–6)

Apply these edits to `backend/open_webui/main.py` if not already present.

## 1. Imports (`from open_webui.routers import (`)

Add:

```python
    plugins,
    skills_ai,
    model_intelligence,
```

(near `pipelines` / `skills` / `tasks`)

## 2. Router includes (after skills router)

```python
app.include_router(skills_ai.router, prefix='/api/v1/skills', tags=['skills'])
app.include_router(plugins.router, prefix='/api/v1/plugins', tags=['plugins'])
app.include_router(model_intelligence.router, prefix='/api/v1/model-intelligence', tags=['model-intelligence'])
```

After this, endpoints are live:

- `/api/v1/plugins/`
- `/api/v1/skills/generate`
- `/api/v1/skills/id/{id}/duplicate`
- `/api/v1/model-intelligence/health|route|fallback|duplicates|warmup|benchmark|updates`

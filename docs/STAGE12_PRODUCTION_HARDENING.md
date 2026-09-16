# Stage 12 – Production Hardening Checklist

Custom fork (`feature/custom-fork-v1`). Do **not** run `npm audit fix --force` blindly.

## Security

| Area | Status / guidance |
|------|-------------------|
| Auth | All new routers use `get_verified_user` / `get_admin_user` |
| Authorization | Chat/project/job ownership checks; admin bypass only where intentional |
| Secrets | Audit log redacts password/token/api_key fields |
| File access | `safe_filename` + basename-only for download plans; cache route has path-traversal guard upstream |
| Plugin permissions | Plugins foundation validates manifests; SAFE_MODE deactivates functions |
| Path traversal | Download package plan never joins user paths server-side |
| SSRF | No new outbound URL fetches from user input in stages 7–11 |
| XSS | No new HTML render of user content in backend APIs |
| Command execution | No shell/`subprocess` in stage 7–11 modules |
| Local integrations | Offline status prefers Ollama/LibreTranslate without crashing |

## Database

- New stage stores (projects, jobs, prompt versions, snapshots, audit) are **process-local** by design for this phase — no breaking migrations required for existing installs.
- When promoting to durable storage: add Alembic migrations with nullable fields and upgrade-only paths.
- Existing users/chats/models/settings remain untouched by custom routers.

## Backward compatibility

- Original Open WebUI routes and UI preserved.
- Custom routers are additive (`/api/v1/...` prefixes).
- Temporary chat convert creates **new** saved chats; does not mutate foreign rows.

## Performance

- Search limited to recent chat list + message sample caps.
- Job queue: max concurrent 4, max retries 2 (no infinite retries).
- Context optimizer is a view only — does not rewrite history.

## Error handling

| Failure | Expected behavior |
|---------|-------------------|
| Ollama down | Offline status message; core API still serves |
| Plugin crash | SAFE_MODE / disable plugin; config not deleted |
| LibreTranslate down | Fallback chain (existing fork feature) |
| Unsupported file | Classifier returns kind=binary + safe actions |
| Job fail | Finite retry then `failed` status |

## Platforms

- Linux primary; Docker CPU / NVIDIA / AMD overlays remain as in fork docs.
- Mobile/responsive: no custom UI breakage intended (shell pages only where added).

## Dependencies (npm)

Observed historically ~33 vulnerabilities (mix of transitive). Policy:

1. Classify direct vs transitive.
2. Prefer upstream Open WebUI bumps over force-fix.
3. Never `npm audit fix --force` without testing `npm run check` + `npm run build`.

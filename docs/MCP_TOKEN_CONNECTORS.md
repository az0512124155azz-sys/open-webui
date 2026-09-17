# MCP connectors with Personal Access Token (no Google OAuth)

| Service | Auth |
|---------|------|
| GitHub | PAT `ghp_...` → `Authorization: Bearer ghp_...` |
| GitLab | PAT |
| Notion | Integration secret |
| Linear | API key |
| Slack | `xoxb-` bot token |
| Hugging Face | `hf_...` |
| OpenAI / Groq / OpenRouter | API key |

Admin → Tools/MCP → add server URL + Bearer token header.

Never commit tokens to git. Prefer minimal scopes.

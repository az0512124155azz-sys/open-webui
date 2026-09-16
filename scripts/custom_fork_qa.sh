#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "== py_compile custom modules =="
find backend/open_webui -type f \( -name '*plugin*' -o -name '*skills_ai*' -o -name '*model_intelligence*' -o -name '*chat_intelligence*' -o -name '*privacy*' -o -name '*files_projects*' -o -name '*search_offline*' -o -name '*job_queue*' -o -name '*production_hardening*' \) 2>/dev/null | while read -r f; do
  python3 -m py_compile "$f" && echo "ok $f" || echo "fail $f"
done
echo "== main.py router markers =="
MAIN="backend/open_webui/main.py"
if [[ -f "$MAIN" ]]; then
  for s in skills_ai.router plugins.router model_intelligence.router chat_intelligence.router privacy_recovery.router files_projects.router search_offline.router job_queue.router production_hardening.router; do
    if grep -q "$s" "$MAIN"; then echo "ok $s"; else echo "MISSING $s"; fi
  done
else
  echo "main.py not in tree"
fi
echo "QA script finished."

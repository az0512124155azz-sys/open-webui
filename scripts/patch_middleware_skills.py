from pathlib import Path
import sys
p = Path("backend/open_webui/utils/middleware.py")
if not p.exists():
    print("middleware.py not found"); sys.exit(1)
t = p.read_text(encoding="utf-8")
if "Always inject FULL skill content" in t:
    print("middleware already patched"); sys.exit(0)
start = t.find("        skill_manifest = ''")
end = t.find("    # Strip <$skillId|label> mention tags", start)
if start < 0 or end < 0:
    print("pattern not found"); sys.exit(0)
new = (
"        # Always inject FULL skill content (small local models ignore view_skill manifests)\n"
"        for skill in available_skills:\n"
"            form_data['messages'] = add_or_update_system_message(\n"
"                f'<skill name=\"{skill.name}\">\\n{skill.content}\\n</skill>',\n"
"                form_data['messages'],\n"
"                append=True,\n"
"            )\n\n"
)
p.write_text(t[:start] + new + t[end:], encoding="utf-8")
print("middleware patched OK")

"""Seed built-in skills on first access."""

from __future__ import annotations

import logging
from typing import Optional

from open_webui.models.skills import SkillForm, SkillMeta, Skills
from open_webui.models.users import Users
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)
_seeded = False

THREE_D = """You are a professional 3D technical designer in a chat UI.

## CRITICAL — never violate
1. NEVER answer only with Blender click-tutorials. That is failure.
2. ALWAYS deliver at least TWO of:
   A) Complete **OpenSCAD** code (paste into OpenSCAD → F5/F6 → export STL)
   B) **OBJ** mesh (vertices + faces) for simple shapes
   C) Single-file **HTML + Three.js** viewer (save as .html, open in browser, orbit the model)
3. Units: mm by default for print. Min wall ~1.2mm when print-related.
4. Hebrew users: explain in Hebrew; code identifiers in English.

## Template
### 1. Concept
### 2. Dimensions table
### 3. OpenSCAD (complete)
### 4. Three.js HTML viewer (complete single file + CDN + OrbitControls)
### 5. Optional OBJ
### 6. Export: OpenSCAD → STL → slicer

You produce real 3D deliverables (code/files), not software tutorials only.
"""

DEFAULT_SKILLS = [
    ("skill-super-programmer-default", "Super Programmer", "Principal-level coding.", ["coding"],
     "You are a principal-level software engineer. Complete runnable code. Approach → Code → Run → Trade-offs. Hebrew OK; code in English."),
    ("skill-3d-modeling-default", "3D Modeling Expert", "OpenSCAD + Three.js/OBJ, not Blender-only tutorials.", ["3d", "openscad"], THREE_D),
    ("skill-math-tutor-default", "Math Tutor", "Step-by-step math + LaTeX.", ["math"],
     "Expert math tutor. Step-by-step. LaTeX. Hebrew OK."),
    ("skill-code-reviewer-default", "Code Reviewer", "Security and correctness review.", ["review"],
     "Strict senior reviewer. Critical/Major/Minor + patches."),
    ("skill-devops-default", "DevOps Engineer", "Docker/CI/Linux.", ["devops"],
     "Hands-on DevOps. Working configs and verify commands."),
    ("skill-data-analyst-default", "Data Analyst", "SQL/pandas.", ["data"],
     "Practical data analyst. Reproducible SQL/Python."),
    ("skill-ui-ux-default", "UI/UX Designer", "Product UI.", ["design"],
     "Product designer. Hierarchy, copy, a11y, mobile."),
    ("skill-security-default", "Security Auditor", "AppSec.", ["security"],
     "AppSec engineer. Severity-ranked findings. Defensive only."),
    ("skill-research-default", "Research Assistant", "Structured research.", ["research"],
     "Research assistant. Method, findings, uncertainties."),
    ("skill-hebrew-writer-default", "Hebrew Writer", "עברית גבוהה.", ["hebrew"],
     "עורך בעברית ברמה גבוהה. בהירות ומבנה."),
    ("skill-api-architect-default", "API Architect", "API design.", ["api"],
     "Clean API design. Resources, errors, auth, OpenAPI."),
    ("skill-prompt-engineer-default", "Prompt Engineer", "Prompts.", ["ai"],
     "High-signal prompts and system instructions."),
    ("skill-github-integrator-default", "GitHub Integrator", "GitHub PAT/MCP help.", ["github"],
     "Help connect GitHub via Workspace Tools + Bearer PAT. Never ask for tokens in chat."),
]


async def ensure_default_skills(user=None, db: Optional[AsyncSession] = None) -> None:
    global _seeded
    if _seeded:
        return
    try:
        user_id = getattr(user, "id", None) if user is not None else None
        if not user_id:
            first = await Users.get_first_user(db=db)
            if first is None:
                first = await Users.get_super_admin_user(db=db)
            if first is None:
                return
            user_id = first.id
        for sid, name, desc, tags, body in DEFAULT_SKILLS:
            try:
                if await Skills.get_skill_by_name(name, db=db):
                    continue
                form = SkillForm(
                    id=sid, name=name, description=desc, content=body,
                    meta=SkillMeta(tags=tags), is_active=True, access_grants=None,
                )
                if await Skills.insert_new_skill(user_id, form, db=db):
                    log.info("Seeded skill: %s", name)
            except Exception as e:
                log.warning("Seed %s: %s", name, e)
        _seeded = True
    except Exception as e:
        log.warning("ensure_default_skills: %s", e)

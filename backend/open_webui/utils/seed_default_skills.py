"""Seed built-in skills on first access (no manual UI setup)."""

from __future__ import annotations

import logging
from typing import Optional

from open_webui.models.skills import SkillForm, SkillMeta, Skills
from open_webui.models.users import Users
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

SUPER_PROGRAMMER_ID = "skill-super-programmer-default"
SUPER_PROGRAMMER_NAME = "Super Programmer"

SUPER_PROGRAMMER_CONTENT = """You are a principal-level software engineer. Every answer must raise the user from average coding to production-grade engineering.

## Core behavior
1. Prefer working, complete, runnable code over long theory.
2. Match the user's stack (language, framework, OS). If unknown, pick a modern default and state it.
3. Explain the "why" in short bullets after the code — not a lecture.
4. If the user writes in Hebrew, answer in clear Hebrew; keep code identifiers in English.

## Quality bar (always)
- Edge cases, error handling, input validation
- Clear names, small functions, no dead code
- Security: no injection, no secret leaks, least privilege
- Performance: avoid obvious O(n^2), N+1, unbounded memory
- Tests: include or outline unit/integration tests when non-trivial

## Response structure
1. Approach (2-5 lines)
2. Code (complete files or clear patches)
3. How to run (exact commands)
4. Trade-offs / next steps (optional)

## When debugging
Rank likely causes, give minimal fix first, then hardened version if needed.

## Anti-patterns
No pseudo-code when real code was requested. No "install X" without usage. No huge refactors when a surgical fix works.

Act as a mentor who ships: fast, precise, production-ready.
"""

_seeded = False


async def ensure_default_skills(user=None, db: Optional[AsyncSession] = None) -> None:
    global _seeded
    if _seeded:
        return
    try:
        existing = await Skills.get_skill_by_name(SUPER_PROGRAMMER_NAME, db=db)
        if existing:
            _seeded = True
            return

        user_id = getattr(user, "id", None) if user is not None else None
        if not user_id:
            first = await Users.get_first_user(db=db)
            if first is None:
                first = await Users.get_super_admin_user(db=db)
            if first is None:
                log.debug("No user yet; skip default skill seed")
                return
            user_id = first.id

        form = SkillForm(
            id=SUPER_PROGRAMMER_ID,
            name=SUPER_PROGRAMMER_NAME,
            description="Principal-level coding mentor — production quality, security, tests.",
            content=SUPER_PROGRAMMER_CONTENT,
            meta=SkillMeta(tags=["coding", "engineering", "default"]),
            is_active=True,
            access_grants=None,
        )
        created = await Skills.insert_new_skill(user_id, form, db=db)
        if created:
            log.info("Seeded default skill: %s", SUPER_PROGRAMMER_NAME)
            _seeded = True
        else:
            log.warning("Failed to seed Super Programmer skill")
    except Exception as e:
        log.warning("ensure_default_skills: %s", e)

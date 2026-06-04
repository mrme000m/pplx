---
name: plugin-dev validation workflow
description: How to audit and fix/improve a Claude Code plugin using plugin-dev tools
type: feedback
---

**Why:** User wanted thorough audit and fix of pplx-plugin using plugin-dev skills/tools.

**How to apply:** When asked to validate or improve a plugin:
1. Run plugin-validator agent for structural/component audit
2. Run skill-reviewer agent on individual skills
3. Fix all CRITICAL and WARNING issues identified
4. Run ctx_batch_execute with Python syntax checks on all .py files
5. Fix any syntax errors found (like the IndentationError in login.py)
6. Re-validate with plugin-validator to confirm fixes

**Key issues found and fixed:**
- All 7 skill descriptions changed from "Use this skill when..." to "This skill should be used when..."
- All 3 agent descriptions changed from "Use this agent when..." to third-person format
- All 3 agents now have `capabilities` field in frontmatter
- stale-doc-detector agent now has `<example>` blocks (was missing)
- CONSOLIDATION_SUMMARY.md removed (development artifact)
- thread-workflows SKILL.md expanded (was 182 words, now 499)
- perplexity-auth SKILL.md expanded (453→953 words with architecture overview, storage model, decision guide)
- login.py IndentationError fixed (def launch_browser missing class-level indentation)

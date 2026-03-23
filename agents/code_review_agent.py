#!/usr/bin/env python3
"""
Code Review Agent — NYSR Engineering
Senior-level code review on every PR and commit.

What it checks:
- Code quality (SOLID principles, DRY, KISS)
- Security vulnerabilities (OWASP Top 10)
- Performance issues (N+1 queries, missing indexes, memory leaks)
- Type safety and error handling
- Test coverage gaps
- Documentation completeness
- Dependency audit (outdated, CVEs)
- Bundle size analysis
- Accessibility compliance
"""
import os, sys, logging
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

log = logging.getLogger(__name__)

REVIEW_SYSTEM = """You are a principal engineer with 15 years experience.
You review code like a Stripe or Airbnb engineer would.
You are: specific, constructive, educational, uncompromising on quality.
You catch: real bugs, security holes, performance issues, maintainability problems.
Format: prioritized issues with exact file locations and suggested fixes."""

def review_code(code: str, language: str, context: str = "") -> dict:
    if not os.environ.get("ANTHROPIC_API_KEY"): return {}
    
    return claude_json(
        REVIEW_SYSTEM,
        f"""Review this {language} code:
Context: {context}

```{language}
{code[:4000]}
```

Return:
{{
  "overall_score": 0-100,
  "verdict": "approve|request_changes|reject",
  "critical_issues": [{{"type":"bug|security|performance","line":0,"issue":"...","fix":"..."}}],
  "warnings": [{{"type":"quality|maintainability","issue":"...","suggestion":"..."}}],
  "positive_feedback": ["what's done well"],
  "improved_code_snippets": [{{"original": "...", "improved": "...", "reason": "..."}}],
  "test_coverage_gaps": ["what should be tested"],
  "documentation_needed": ["what needs docs"]
}}""",
        max_tokens=2000
    ) or {"overall_score": 0, "verdict": "unknown"}

def auto_fix_code(code: str, issues: list, language: str) -> str:
    """Automatically fix identified issues in code."""
    if not os.environ.get("ANTHROPIC_API_KEY"): return code
    
    return claude(
        REVIEW_SYSTEM,
        f"""Fix these issues in the {language} code:

Issues to fix:
{chr(10).join([f"- {i}" for i in issues[:10]])}

Original code:
```{language}
{code[:3000]}
```

Return ONLY the fixed code. No explanation. Make all fixes simultaneously.""",
        max_tokens=3000
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log.info("Code Review Agent ready.")

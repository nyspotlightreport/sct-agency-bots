#!/usr/bin/env python3
"""
QA & Testing Agent — NYSR Engineering
Commercial-grade quality assurance on every project.

Generates: Unit tests, Integration tests, E2E tests,
Security audits, Performance benchmarks, Accessibility checks.
Coverage target: 80%+ on all projects.
"""
import os, sys, json, logging
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except:
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

log = logging.getLogger(__name__)

QA_SYSTEM = """You are a senior QA engineer and security specialist.
You write comprehensive tests that catch real bugs.
Standards: TDD approach, 80%+ coverage, security-first mindset.
Always include: happy paths, edge cases, error states, security boundaries."""

def generate_tests(code: str, framework: str = "pytest", file_type: str = "api") -> dict:
    """Generate comprehensive test suite for given code."""
    if not os.environ.get("ANTHROPIC_API_KEY"): return {}
    
    return claude_json(
        QA_SYSTEM,
        f"""Generate a complete test suite for this {file_type} code.
Framework: {framework}

Code to test:
```
{code[:3000]}
```

Return JSON:
{{
  "test_file": {{
    "filename": "test_[appropriate_name].py",
    "content": "COMPLETE test file with all tests"
  }},
  "coverage_estimate": "X%",
  "test_count": 0,
  "security_tests": ["list of security scenarios tested"],
  "edge_cases_covered": ["list of edge cases"]
}}""",
        max_tokens=3000
    ) or {}

def security_audit(code: str) -> dict:
    """Run security audit on code."""
    if not os.environ.get("ANTHROPIC_API_KEY"): return {}
    
    return claude_json(
        "You are a security engineer specializing in OWASP Top 10 and secure code review.",
        f"""Audit this code for security vulnerabilities:
```
{code[:2000]}
```
Check for: SQL injection, XSS, CSRF, insecure auth, secrets exposure, input validation,
improper error handling, insecure dependencies, path traversal, command injection.

Return JSON:
{{
  "risk_level": "low|medium|high|critical",
  "vulnerabilities": [{{"type": "...", "severity": "...", "line": 0, "fix": "..."}}],
  "security_score": 0-100,
  "recommendations": ["recommendation 1", "recommendation 2"]
}}""",
        max_tokens=1500
    ) or {"risk_level": "unknown", "security_score": 0}

def generate_e2e_tests(app_url: str, user_flows: list) -> str:
    """Generate Playwright E2E tests for user flows."""
    if not os.environ.get("ANTHROPIC_API_KEY"): return ""
    
    return claude(
        "You write Playwright E2E tests. Production quality. Full page object model.",
        f"""Write Playwright E2E tests for: {app_url}
User flows to test: {user_flows}

Write complete test file using:
- Page Object Model pattern
- Fixtures for test data
- Parallel execution where possible
- Screenshots on failure
- Custom matchers""",
        max_tokens=3000
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log.info("QA Agent ready. Provide code to test.")

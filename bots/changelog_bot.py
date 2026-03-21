#!/usr/bin/env python3
"""
Changelog Bot — Auto-generates changelogs from Git commits.
Runs weekly. Categorizes commits by type (feat/fix/refactor/docs).
Publishes to CHANGELOG.md and site/changelog/index.html.
"""
import os, sys, json, logging, base64
from datetime import datetime, timedelta
sys.path.insert(0, ".")

import urllib.request

log = logging.getLogger(__name__)
GH_TOKEN = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN","")
REPO     = os.environ.get("GITHUB_REPOSITORY","nyspotlightreport/sct-agency-bots")

COMMIT_TYPES = {
    "feat":     ("✨ New Features",      "#22D3A0"),
    "fix":      ("🐛 Bug Fixes",         "#EF4444"),
    "refactor": ("♻️ Improvements",      "#3B82F6"),
    "docs":     ("📚 Documentation",     "#F59E0B"),
    "perf":     ("⚡ Performance",       "#A855F7"),
    "security": ("🔒 Security",          "#EF4444"),
    "chore":    ("🔧 Maintenance",       "#6B7280"),
}

def gh(path):
    if not GH_TOKEN: return None
    try:
        req = urllib.request.Request(f"https://api.github.com{path}",
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"})
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read())
    except: return None

def get_commits(since_days: int = 7) -> list:
    since = (datetime.utcnow()-timedelta(days=since_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    commits = gh(f"/repos/{REPO}/commits?since={since}&per_page=100")
    result = []
    for c in (commits or []):
        msg = c.get("commit",{}).get("message","").split("\n")[0]
        sha = c.get("sha","")[:7]
        result.append({"sha":sha,"message":msg,"author":c.get("commit",{}).get("author",{}).get("name","?")})
    return result

def categorize_commits(commits: list) -> dict:
    categorized = {k:[] for k in COMMIT_TYPES}
    categorized["other"] = []
    for c in commits:
        msg = c["message"]
        matched = False
        for prefix in COMMIT_TYPES:
            if msg.lower().startswith(prefix):
                categorized[prefix].append(c)
                matched = True
                break
        if not matched:
            categorized["other"].append(c)
    return categorized

def generate_changelog_md(categorized: dict, period: str) -> str:
    lines = [f"# Changelog — {period}\n"]
    for ctype, (label, color) in COMMIT_TYPES.items():
        commits = categorized.get(ctype,[])
        if commits:
            lines.append(f"\n## {label}\n")
            for c in commits:
                lines.append(f"- `{c['sha']}` {c['message']} ({c['author']})")
    if categorized.get("other"):
        lines.append("\n## Other Changes\n")
        for c in categorized["other"]:
            lines.append(f"- `{c['sha']}` {c['message']}")
    return "\n".join(lines)

def push_changelog(content: str):
    path = "CHANGELOG.md"
    existing = gh(f"/repos/{REPO}/contents/{path}")
    sha = existing.get("sha","") if existing and isinstance(existing,dict) else ""
    payload = {"message":"docs: Weekly changelog update","content":base64.b64encode(content.encode()).decode()}
    if sha: payload["sha"] = sha
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",
        data=json.dumps(payload).encode(),
        headers={"Authorization":f"token {GH_TOKEN}","Content-Type":"application/json","Accept":"application/vnd.github+json"},
        method="PUT")
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            return r.status in [200,201]
    except: return False

def run():
    log.info("Changelog Bot generating weekly changelog...")
    commits = get_commits(7)
    period = f"Week of {(datetime.utcnow()-timedelta(days=7)).strftime('%b %d')} — {datetime.utcnow().strftime('%b %d, %Y')}"
    categorized = categorize_commits(commits)
    changelog = generate_changelog_md(categorized, period)
    pushed = push_changelog(changelog) if GH_TOKEN else False
    log.info(f"Changelog: {len(commits)} commits | Pushed: {pushed}")
    return {"commits_processed":len(commits),"pushed":pushed}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Changelog] %(message)s")
    run()

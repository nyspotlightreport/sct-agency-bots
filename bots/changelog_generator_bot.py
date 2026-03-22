#!/usr/bin/env python3
# Changelog Generator Bot - Auto-generates changelogs from Git commits.
import os, sys, json, logging
from datetime import datetime
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except:
    def claude(s,u,**k): return ""
log = logging.getLogger(__name__)

GH_TOKEN = os.environ.get("GH_PAT","")
REPO     = "nyspotlightreport/sct-agency-bots"
import urllib.request

def get_recent_commits(n=20):
    if not GH_TOKEN: return []
    url = f"https://api.github.com/repos/{REPO}/commits?per_page={n}"
    req = urllib.request.Request(url,headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            commits = json.loads(r.read())
            return [{"sha":c["sha"][:7],"message":c["commit"]["message"],"date":c["commit"]["author"]["date"][:10],"author":c["commit"]["author"]["name"]} for c in commits]
    except Exception as e:
        log.warning(f"Could not fetch commits: {e}")
        return []

def categorize_commits(commits):
    cats = {"feat":[],"fix":[],"refactor":[],"docs":[],"chore":[],"other":[]}
    for c in commits:
        msg = c["message"]
        if msg.startswith("feat"): cats["feat"].append(c)
        elif msg.startswith("fix"): cats["fix"].append(c)
        elif msg.startswith("refactor"): cats["refactor"].append(c)
        elif msg.startswith("docs"): cats["docs"].append(c)
        elif msg.startswith("chore"): cats["chore"].append(c)
        else: cats["other"].append(c)
    return cats

def generate_changelog(version="latest"):
    commits = get_recent_commits(30)
    cats = categorize_commits(commits)
    date = datetime.utcnow().strftime("%B %d, %Y")
    lines = [f"# Changelog - {version}","",f"**Released:** {date}",""]
    if cats["feat"]: lines += ["## New Features",*[f"- {c['message'][:80]}" for c in cats["feat"][:10]],""]
    if cats["fix"]:  lines += ["## Bug Fixes",*[f"- {c['message'][:80]}" for c in cats["fix"][:10]],""]
    if cats["refactor"]: lines += ["## Improvements",*[f"- {c['message'][:80]}" for c in cats["refactor"][:5]],""]
    lines += [f"**{len(commits)} commits** from {len(set(c['author'] for c in commits))} contributors"]
    return "
".join(lines)

def run():
    changelog = generate_changelog()
    log.info(f"Generated changelog: {len(changelog)} chars, {changelog.count(chr(10))} lines")
    return changelog

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

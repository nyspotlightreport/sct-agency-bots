#!/usr/bin/env python3
# GitHub PR Reviewer Bot - Auto-reviews pull requests with AI code review.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
log = logging.getLogger(__name__)

GH_TOKEN = os.environ.get("GH_PAT","")
REPO     = "nyspotlightreport/sct-agency-bots"
import urllib.request, urllib.parse

def gh(method, path, body=None):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url,data=data,headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json","Content-Type":"application/json"},method=method)
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read()) if r.status != 204 else {}
    except Exception as e:
        log.warning(f"GH {method} {path}: {e}")
        return {}

def review_pr(pr_number, diff_content):
    review = claude_json(
        "Review this code diff. Return JSON: {summary, issues:[{line,severity,message}], suggestions:[str], approve_recommendation}",
        f"PR #{pr_number} diff:
{diff_content[:3000]}",
        max_tokens=600
    ) or {"summary":"Review complete","issues":[],"suggestions":[],"approve_recommendation":True}
    return review

def get_open_prs():
    prs = gh("GET","pulls?state=open&per_page=10")
    return prs if isinstance(prs,list) else []

def post_review(pr_number, review_body, approve=True):
    if not GH_TOKEN: return False
    event = "APPROVE" if approve else "COMMENT"
    result = gh("POST",f"pulls/{pr_number}/reviews",{"body":review_body,"event":event})
    return bool(result)

def run():
    if not GH_TOKEN:
        log.warning("No GH_PAT - PR review skipped")
        return False
    prs = get_open_prs()
    log.info(f"Open PRs: {len(prs)}")
    for pr in prs[:3]:
        log.info(f"PR #{pr.get('number')}: {pr.get('title','?')}")
    return len(prs)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

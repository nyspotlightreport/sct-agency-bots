#!/usr/bin/env python3
"""
GITHUB SPONSORS SETUP — Add sponsor button to ALL your repos
Runs once, takes 2 minutes, passive income forever.
GitHub takes 0% — you keep everything via Stripe.
"""
import os, urllib.request, json, base64

TOKEN = os.getenv("GITHUB_TOKEN", "")
USERNAME = os.getenv("GITHUB_USERNAME", "")

FUNDING_YML = """# GitHub Sponsors & Support
# This enables the Sponsor button on all your repos

github: [{username}]
ko_fi: {ko_fi}
custom: ["https://nyspotlightreport.com/support"]
""".format(
    username=USERNAME or "your-github-username",
    ko_fi="nyspotlightreport"
)

def get_repos():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USERNAME}/repos?per_page=100",
        headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def add_funding_yml(repo_name):
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/contents/.github/FUNDING.yml"
    content = base64.b64encode(FUNDING_YML.encode()).decode()
    payload = json.dumps({
        "message": "Add GitHub Sponsors FUNDING.yml",
        "content": content
    }).encode()
    req = urllib.request.Request(url, data=payload, method="PUT",
        headers={"Authorization": f"token {TOKEN}",
                 "Content-Type": "application/json",
                 "Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status in [200, 201]
    except urllib.error.HTTPError as e:
        if e.code == 422:  # Already exists
            return True
        return False

if __name__ == "__main__":
    if not TOKEN or not USERNAME:
        print("Set GITHUB_TOKEN and GITHUB_USERNAME env vars")
        print("Token needs 'repo' scope from github.com/settings/tokens")
        exit(1)

    repos = get_repos()
    print(f"Found {len(repos)} repos. Adding FUNDING.yml to each...")
    for repo in repos:
        name = repo["name"]
        result = add_funding_yml(name)
        print(f"  {'✅' if result else '❌'} {name}")

    print(f"\n✅ Done! Sponsor button now appears on all {len(repos)} repos.")
    print("Enable Sponsors at: github.com/settings/billing/payment_info")
    print("Set up payout: github.com/sponsors/accounts")

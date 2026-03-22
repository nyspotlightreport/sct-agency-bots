#!/usr/bin/env python3
"""
WEB MONITOR AGENT v1.0 — S.C. Thomas Internal Agency
Monitors competitor sites + target pages for changes.
Uses HTTP HEAD + content hash (no browser needed).
Detects price changes, new pages, content updates.
Alerts Chairman with diff summary.
Schedule: Daily 6:00 AM ET.
"""

import os, sys, json, hashlib, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, ClaudeClient, AlertSystem, with_retry

class WebMonitorAgent(BaseBot):
    VERSION = "1.0.0"

    # Sites to monitor — customize these
    MONITOR_TARGETS = [
        # {"name": "Competitor Blog", "url": "https://competitor.com/blog", "type": "content"},
        # {"name": "Competitor Pricing", "url": "https://competitor.com/pricing", "type": "price"},
    ]

    def __init__(self):
        super().__init__("web-monitor")
        # Load targets from env or state
        env_targets = os.getenv("MONITOR_URLS", "")
        if env_targets:
            for url in env_targets.split(","):
                url = url.strip()
                if url:
                    self.MONITOR_TARGETS.append({
                        "name": url.split("//")[-1].split("/")[0],
                        "url":  url,
                        "type": "content"
                    })
        # Merge with any saved targets
        saved = self.state.get("monitor_targets", [])
        if saved:
            self.MONITOR_TARGETS.extend(saved)

    @with_retry(max_retries=2, delay=3.0)
    def fetch_page_hash(self, url: str) -> dict:
        """Fetch page and return hash + metadata"""
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (WebMonitorBot/1.0; +https://nyspotlightreport.com)",
            "Accept": "text/html,application/xhtml+xml"
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                content = r.read()
                headers = dict(r.headers)
                return {
                    "hash":          hashlib.md5(content).hexdigest(),
                    "size":          len(content),
                    "status":        r.status,
                    "content_type":  headers.get("Content-Type", ""),
                    "last_modified": headers.get("Last-Modified", ""),
                    "fetched_at":    datetime.now().isoformat(),
                    "snippet":       content[:500].decode("utf-8", errors="ignore"),
                }
        except urllib.error.HTTPError as e:
            return {"hash": "", "status": e.code, "error": str(e)}
        except Exception as e:
            return {"hash": "", "status": 0, "error": str(e)}

    def analyze_change(self, target: dict, old: dict, new: dict) -> str:
        """Use Claude to summarize what changed"""
        system = "You analyze website changes for a media company. Be brief and actionable."
        prompt = f"""Website change detected:
Site: {target['name']} ({target['url']})
Type: {target['type']}
Old size: {old.get('size', 0)} bytes | New size: {new.get('size', 0)} bytes
Old snippet: {old.get('snippet', '')[:200]}
New snippet: {new.get('snippet', '')[:200]}

In 2-3 sentences: What likely changed and why does it matter?"""

        return ClaudeClient.complete_safe(
            system=system, user=prompt, max_tokens=150,
            fallback=f"Content changed on {target['name']}. Size: {old.get('size',0)} → {new.get('size',0)} bytes."
        )

    def execute(self) -> dict:
        if not self.MONITOR_TARGETS:
            self.logger.info("No monitor targets configured. Set MONITOR_URLS env var.")
            return {"items_processed": 0}

        previous = self.state.get("page_hashes", {})
        current  = {}
        changes  = []

        for target in self.MONITOR_TARGETS:
            url  = target["url"]
            name = target["name"]
            self.logger.info(f"Checking: {name}")

            result = self.fetch_page_hash(url)
            current[url] = result

            if result.get("error"):
                self.logger.warning(f"Error fetching {name}: {result['error']}")
                continue

            prev = previous.get(url, {})
            if prev and prev.get("hash") and prev["hash"] != result["hash"]:
                # Change detected
                analysis = self.analyze_change(target, prev, result)
                changes.append({
                    "name":     name,
                    "url":      url,
                    "type":     target["type"],
                    "analysis": analysis,
                    "old_size": prev.get("size", 0),
                    "new_size": result.get("size", 0),
                })
                self.logger.info(f"CHANGE DETECTED: {name}")

        # Save current state
        self.state.set("page_hashes", {**previous, **current})

        if changes:
            # Build alert
            changes_html = "".join([f"""
<div style="border-left:4px solid #ff9800;padding:10px;margin-bottom:10px;background:#fff8e1;">
  <strong><a href="{c['url']}">{c['name']}</a></strong> [{c['type'].upper()}]<br>
  <span style="font-size:13px;">{c['analysis']}</span><br>
  <span style="color:#888;font-size:12px;">Size: {c['old_size']:,} → {c['new_size']:,} bytes</span>
</div>""" for c in changes])

            AlertSystem.send(
                subject  = f"🔍 {len(changes)} Site Change(s) Detected — {datetime.now().strftime('%b %d')}",
                body_html= f"<h3>Web Monitor Report</h3>{changes_html}",
                severity = "WARNING"
            )

        self.log_summary(sites_checked=len(self.MONITOR_TARGETS), changes=len(changes))
        return {"items_processed": len(self.MONITOR_TARGETS), "changes": len(changes)}


def add_target(url: str, name: str = "", target_type: str = "content"):
    """Add a URL to monitor"""
    bot = WebMonitorAgent()
    saved = bot.state.get("monitor_targets", [])
    saved.append({
        "name": name or url.split("//")[-1].split("/")[0],
        "url":  url,
        "type": target_type
    })
    bot.state.set("monitor_targets", saved)
    print(f"✅ Added monitor target: {url}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--add",  type=str, help="Add URL to monitor")
    p.add_argument("--name", type=str, default="", help="Name for the target")
    p.add_argument("--type", type=str, default="content",
                   choices=["content", "price", "news"])
    args = p.parse_args()

    if args.add:
        add_target(args.add, args.name, args.type)
    else:
        WebMonitorAgent().run()

# USAGE:
# Add targets: python web_monitor_agent.py --add https://competitor.com/blog --name "Competitor Blog"
# Run check:   python web_monitor_agent.py
# Env var:     MONITOR_URLS=https://site1.com,https://site2.com/pricing

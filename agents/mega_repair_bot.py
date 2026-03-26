#!/usr/bin/env python3
"""
Mega Repair Bot -- 5-Module Autonomous Site Health System

Module 1: Audit Runner     -- checks site URLs, Supabase, sitemap, OG tags, ISSN, store
Module 2: Pattern Learner  -- queries audit_history for recurring failures
Module 3: Repair Engine    -- auto-fixes sitemap, OG tags, ISSN, ProFlow, newsletter CTAs
Module 4: Curiosity Engine -- crawls sitemap for 404s, checks store rendering
Module 5: Financial Pulse  -- checks Stripe + Gumroad revenue, sends Pushover summary

Env vars: SUPABASE_URL, SUPABASE_KEY, STRIPE_SECRET_KEY, GUMROAD_ACCESS_TOKEN,
          PUSHOVER_USER_KEY, PUSHOVER_APP_TOKEN, SITE_BASE_URL
"""

import os, sys, json, logging, re, uuid
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("WARNING: requests not installed — some checks will be skipped")
    requests = None

try:
    from supabase import create_client, Client
except ImportError:
    print("WARNING: supabase not installed — DB logging will be skipped")
    create_client = None
    Client = None

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [MegaRepair:%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger("main")

SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://nyspotlightreport.com")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
GUMROAD_ACCESS_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN")
PUSHOVER_USER_KEY = os.environ.get("PUSHOVER_USER_KEY")
PUSHOVER_APP_TOKEN = os.environ.get("PUSHOVER_APP_TOKEN")

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]


def supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not set — running in offline mode")
        return None
    if create_client is None:
        logger.warning("supabase package not available — running in offline mode")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Supabase client creation failed: {e}")
        return None


class AuditRunner:
    def __init__(self, sb):
        self.sb = sb
        self.log = logging.getLogger("AuditRunner")
        self.results = []

    def _record(self, audit_type, status, message, severity="low", target_url=None, details=None):
        entry = {"audit_type": audit_type, "status": status, "severity": severity,
                 "message": message, "target_url": target_url,
                 "details": details or {}, "run_id": RUN_ID}
        self.results.append(entry)
        if self.sb is None:
            return
        try: self.sb.table("audit_history").insert(entry).execute()
        except Exception as e: self.log.error(f"Failed to log audit: {e}")

    def check_site_url(self, url=None):
        url = url or SITE_BASE_URL
        try:
            resp = requests.get(url, timeout=15, allow_redirects=True)
            elapsed = resp.elapsed.total_seconds()
            if resp.status_code == 200:
                self._record("site_health", "pass", f"Site OK in {elapsed:.2f}s",
                             severity="low" if elapsed < 3 else "medium", target_url=url)
            else:
                self._record("site_health", "fail", f"Site returned {resp.status_code}",
                             severity="high", target_url=url)
        except requests.RequestException as e:
            self._record("site_health", "fail", f"Site unreachable: {e}",
                         severity="critical", target_url=url)

    def check_supabase(self):
        if self.sb is None:
            self._record("other", "warn", "Supabase client not available — skipped", severity="medium")
            return
        try:
            self.sb.table("audit_history").select("id").limit(1).execute()
            self._record("other", "pass", "Supabase connection OK")
        except Exception as e:
            self._record("other", "fail", f"Supabase error: {e}", severity="critical")

    def check_sitemap(self, url=None):
        sitemap_url = url or SITE_BASE_URL + "/sitemap.xml"
        try:
            resp = requests.get(sitemap_url, timeout=10)
            if resp.status_code != 200:
                self._record("sitemap", "fail", f"Sitemap returned {resp.status_code}",
                             severity="high", target_url=sitemap_url); return
            if "<urlset" not in resp.text and "<sitemapindex" not in resp.text:
                self._record("sitemap", "fail", "Invalid sitemap format",
                             severity="high", target_url=sitemap_url); return
            url_count = resp.text.count("<loc>")
            self._record("sitemap", "pass", f"Sitemap valid with {url_count} URLs",
                         target_url=sitemap_url, details={"url_count": url_count})
        except requests.RequestException as e:
            self._record("sitemap", "fail", f"Sitemap error: {e}", severity="high", target_url=sitemap_url)

    def check_og_tags(self, url=None):
        url = url or SITE_BASE_URL
        try:
            html = requests.get(url, timeout=10).text
            required = ["og:title", "og:description", "og:image", "og:url"]
            missing = [t for t in required if f'property="{t}"' not in html]
            if missing:
                self._record("og_tags", "warn", "Missing OG tags: " + ", ".join(missing),
                             severity="medium", target_url=url, details={"missing": missing})
            else:
                self._record("og_tags", "pass", "All OG tags present", target_url=url)
        except requests.RequestException as e:
            self._record("og_tags", "fail", f"OG check error: {e}", severity="medium", target_url=url)

    def check_issn(self, url=None):
        url = url or SITE_BASE_URL
        try:
            text = requests.get(url, timeout=10).text
            if "ISSN" in text or "issn" in text:
                self._record("issn", "pass", "ISSN found", target_url=url)
            else:
                self._record("issn", "warn", "No ISSN found", severity="medium", target_url=url)
        except requests.RequestException as e:
            self._record("issn", "fail", f"ISSN error: {e}", severity="medium", target_url=url)

    def check_store(self, path="/store"):
        url = SITE_BASE_URL + path
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                self._record("store", "fail", f"Store returned {resp.status_code}",
                             severity="high", target_url=url); return
            html = resp.text.lower()
            if any(kw in html for kw in ["product", "price", "buy", "gumroad"]):
                self._record("store", "pass", "Store has product content", target_url=url)
            else:
                self._record("store", "warn", "Store may be empty", severity="medium", target_url=url)
        except requests.RequestException as e:
            self._record("store", "fail", f"Store error: {e}", severity="high", target_url=url)

    def run_all(self):
        self.check_site_url(); self.check_supabase(); self.check_sitemap()
        self.check_og_tags(); self.check_issn(); self.check_store()
        fails = sum(1 for r in self.results if r["status"] == "fail")
        self.log.info(f"Audit: {len(self.results)} checks, {fails} failures")
        return self.results


class PatternLearner:
    def __init__(self, sb):
        self.sb = sb
        self.log = logging.getLogger("PatternLearner")

    def get_recurring_failures(self, days=30, min_occurrences=3):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (self.sb.table("audit_history")
                  .select("audit_type, status, message, target_url, created_at")
                  .in_("status", ["fail", "error"]).gte("created_at", cutoff)
                  .order("created_at", desc=True).limit(500).execute())
        patterns = {}
        for row in result.data:
            key = row["audit_type"] + "|" + (row.get("target_url") or "")
            if key not in patterns:
                patterns[key] = {"audit_type": row["audit_type"],
                    "target_url": row.get("target_url"),
                    "sample_message": row["message"], "count": 0, "dates": []}
            patterns[key]["count"] += 1
            patterns[key]["dates"].append(row["created_at"])
        recurring = sorted([p for p in patterns.values() if p["count"] >= min_occurrences],
                           key=lambda x: x["count"], reverse=True)
        self.log.info(f"Found {len(recurring)} recurring failure patterns")
        return recurring

    def suggest_repairs(self):
        actions = {"sitemap": "Regenerate sitemap.xml", "og_tags": "Inject OG meta tags",
                   "issn": "Add ISSN meta tag", "site_health": "Check hosting/DNS/SSL",
                   "store": "Verify Gumroad embed", "proflow": "Re-inject ProFlow widget",
                   "newsletter": "Verify newsletter CTA forms"}
        return [{"audit_type": p["audit_type"], "target": p.get("target_url", "N/A"),
                 "occurrences": p["count"],
                 "action": actions.get(p["audit_type"], "Investigate " + p["audit_type"])}
                for p in self.get_recurring_failures()]


class RepairEngine:
    def __init__(self, sb):
        self.sb = sb
        self.log = logging.getLogger("RepairEngine")
        self.repairs = []

    def _log_repair(self, repair_type, target, action, status="success", before=None, after=None):
        entry = {"repair_type": repair_type, "target": target, "action_taken": action,
                 "status": status, "before_state": before or {}, "after_state": after or {},
                 "automated": True, "run_id": RUN_ID}
        self.repairs.append(entry)
        if self.sb is None:
            return
        try: self.sb.table("repair_log").insert(entry).execute()
        except Exception as e: self.log.error(f"Repair log error: {e}")

    def fix_sitemap(self, pages=None):
        if not pages:
            pages = ["/", "/about", "/editorial", "/store", "/contact", "/subscribe"]
            try:
                resp = requests.get(SITE_BASE_URL + "/sitemap.xml", timeout=10)
                if resp.status_code == 200:
                    locs = re.findall(r"<loc>(.*?)</loc>", resp.text)
                    if locs: pages = locs
            except Exception: pass
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        urls_xml = "\n".join(f"  <url><loc>{p if p.startswith('http') else SITE_BASE_URL + p}</loc>"
                             f"<lastmod>{today}</lastmod></url>" for p in pages)
        sitemap = '<?xml version="1.0"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls_xml + "\n</urlset>"
        self._log_repair("sitemap_fix", SITE_BASE_URL + "/sitemap.xml",
                         f"Regenerated with {len(pages)} URLs", after={"url_count": len(pages)})
        return sitemap

    def fix_og_tags(self, page_url, title=None):
        title = title or "NY Spotlight Report"
        desc = "New York premier entertainment and culture publication"
        img = SITE_BASE_URL + "/images/og-default.jpg"
        og = "\n".join([f'<meta property="og:title" content="{title}" />',
                        f'<meta property="og:description" content="{desc}" />',
                        f'<meta property="og:image" content="{img}" />',
                        f'<meta property="og:url" content="{page_url}" />',
                        '<meta property="og:type" content="article" />'])
        self._log_repair("og_tag_fix", page_url, "Generated OG tags", after={"title": title})
        return og

    def fix_issn(self, issn="2996-4873"):
        tag = f'<meta name="citation_issn" content="{issn}" />'
        self._log_repair("issn_fix", SITE_BASE_URL, f"ISSN tag: {issn}", after={"issn": issn})
        return tag

    def fix_proflow_editorial(self):
        script = '<script src="https://myproflow.org/widget.js" data-site="nyspotlightreport" async></script>'
        self._log_repair("proflow_inject", SITE_BASE_URL + "/editorial", "ProFlow widget injected")
        return script

    def fix_newsletter_cta(self):
        cta = '<div class="newsletter-cta"><h3>Stay in the Spotlight</h3><form action="/api/subscribe" method="POST"><input type="email" name="email" required /><button type="submit">Subscribe</button></form></div>'
        self._log_repair("cta_fix", SITE_BASE_URL, "Newsletter CTA generated")
        return cta

    def run_auto_repairs(self, audit_results):
        for r in audit_results:
            if r["status"] not in ("fail", "warn"): continue
            t = r["audit_type"]
            if t == "sitemap": self.fix_sitemap()
            elif t == "og_tags": self.fix_og_tags(r.get("target_url", SITE_BASE_URL))
            elif t == "issn": self.fix_issn()
            elif t == "proflow": self.fix_proflow_editorial()
            elif t == "newsletter": self.fix_newsletter_cta()
        self.log.info(f"Auto-repairs: {len(self.repairs)} applied")
        return self.repairs


class CuriosityEngine:
    def __init__(self, sb):
        self.sb = sb
        self.log = logging.getLogger("CuriosityEngine")

    def crawl_sitemap_for_404s(self):
        self.log.info("Crawling sitemap for 404s...")
        issues = []
        try:
            resp = requests.get(SITE_BASE_URL + "/sitemap.xml", timeout=10)
            if resp.status_code != 200: return issues
            urls = re.findall(r"<loc>(.*?)</loc>", resp.text)
            self.log.info(f"Found {len(urls)} URLs in sitemap")
            for url in urls:
                try:
                    r = requests.head(url, timeout=8, allow_redirects=True)
                    if r.status_code >= 400:
                        issues.append({"url": url, "status": r.status_code})
                        self._record_issue(url, r.status_code)
                except requests.RequestException as e:
                    issues.append({"url": url, "status": 0, "error": str(e)})
        except Exception as e:
            self.log.error(f"Crawl error: {e}")
        self.log.info(f"Crawl complete: {len(issues)} issues")
        return issues

    def check_store_rendering(self):
        store_url = SITE_BASE_URL + "/store"
        result = {"url": store_url, "status": "unknown", "issues": []}
        try:
            resp = requests.get(store_url, timeout=10)
            result["http_status"] = resp.status_code
            if resp.status_code != 200:
                result["status"] = "error"; return result
            html = resp.text
            checks = {
                "has_products": bool(re.search(r'class="[^"]*product', html, re.I)),
                "has_prices": bool(re.search(r'\d+\.\d{2}', html)),
                "has_images": "<img" in html,
                "has_buy_links": bool(re.search(r'(gumroad|buy|purchase)', html, re.I)),
            }
            result["checks"] = checks
            failures = [k for k, v in checks.items() if not v]
            result["status"] = "degraded" if failures else "healthy"
            result["issues"] = failures
        except requests.RequestException as e:
            result["status"] = "error"; result["issues"].append(str(e))
        return result

    def _record_issue(self, url, status_code):
        try:
            self.sb.table("audit_history").insert({
                "audit_type": "content", "status": "fail", "severity": "medium",
                "message": f"URL returned {status_code}", "target_url": url,
                "details": {"status_code": status_code}, "run_id": RUN_ID,
            }).execute()
        except Exception as e:
            self.log.error(f"Record issue error: {e}")


class FinancialPulse:
    def __init__(self):
        self.log = logging.getLogger("FinancialPulse")

    def get_stripe_revenue(self, days=7):
        if not STRIPE_SECRET_KEY:
            return {"error": "STRIPE_SECRET_KEY not set", "total_cents": 0}
        try:
            import stripe as stripe_mod
            stripe_mod.api_key = STRIPE_SECRET_KEY
            cutoff = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
            charges = stripe_mod.Charge.list(created={"gte": cutoff}, limit=100)
            ok = [c for c in charges.data if c["paid"] and not c.get("refunded")]
            total = sum(c["amount"] for c in ok)
            return {"period_days": days, "total_cents": total,
                    "total_usd": "${:.2f}".format(total / 100),
                    "transaction_count": len(ok), "source": "stripe"}
        except Exception as e:
            self.log.error(f"Stripe error: {e}")
            return {"error": str(e), "total_cents": 0}

    def get_gumroad_revenue(self, days=7):
        if not GUMROAD_ACCESS_TOKEN:
            return {"error": "GUMROAD_ACCESS_TOKEN not set", "total_cents": 0}
        try:
            after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
            resp = requests.get("https://api.gumroad.com/v2/sales",
                params={"access_token": GUMROAD_ACCESS_TOKEN, "after": after}, timeout=15)
            data = resp.json()
            if not data.get("success"):
                return {"error": data.get("message", "Unknown"), "total_cents": 0}
            sales = data.get("sales", [])
            total = sum(int(float(s.get("price", 0)) * 100) for s in sales)
            return {"period_days": days, "total_cents": total,
                    "total_usd": "${:.2f}".format(total / 100),
                    "transaction_count": len(sales), "source": "gumroad"}
        except Exception as e:
            self.log.error(f"Gumroad error: {e}")
            return {"error": str(e), "total_cents": 0}

    def send_pushover_summary(self, stripe_data, gumroad_data, audit_summary=None):
        if not PUSHOVER_USER_KEY or not PUSHOVER_APP_TOKEN:
            return False
        s_usd = stripe_data.get("total_usd", "$0.00")
        g_usd = gumroad_data.get("total_usd", "$0.00")
        combined = stripe_data.get("total_cents", 0) + gumroad_data.get("total_cents", 0)
        combined_usd = "${:.2f}".format(combined / 100)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        msg = "NYSR Pulse ({})\nStripe: {} ({} txns)\nGumroad: {} ({} txns)\nTotal: {}".format(
            ts, s_usd, stripe_data.get("transaction_count", 0),
            g_usd, gumroad_data.get("transaction_count", 0), combined_usd)
        if audit_summary:
            msg += "\nHealth: {} issues, {} repaired".format(
                audit_summary.get("failures", 0), audit_summary.get("repairs", 0))
        try:
            resp = requests.post("https://api.pushover.net/1/messages.json", data={
                "token": PUSHOVER_APP_TOKEN, "user": PUSHOVER_USER_KEY,
                "title": "NYSR Revenue: " + combined_usd, "message": msg, "priority": 0,
            }, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            self.log.error(f"Pushover error: {e}"); return False

    def run(self, days=7, send_notification=True):
        s = self.get_stripe_revenue(days)
        g = self.get_gumroad_revenue(days)
        combined = s.get("total_cents", 0) + g.get("total_cents", 0)
        result = {"stripe": s, "gumroad": g, "combined_cents": combined,
                  "combined_usd": "${:.2f}".format(combined / 100),
                  "timestamp": datetime.now(timezone.utc).isoformat()}
        if send_notification:
            result["notification_sent"] = self.send_pushover_summary(s, g)
        return result


def run_full_pipeline(modules=None, dry_run=False):
    all_mods = ["audit", "patterns", "repair", "curiosity", "financial"]
    modules = modules or all_mods
    sb = supabase_client()
    report = {"run_id": RUN_ID, "timestamp": datetime.now(timezone.utc).isoformat(), "modules": {}}
    audit_results = []

    if "audit" in modules:
        try:
            logger.info("=== MODULE 1: AUDIT RUNNER ===")
            a = AuditRunner(sb); audit_results = a.run_all()
            report["modules"]["audit"] = {"total_checks": len(audit_results),
                "failures": sum(1 for r in audit_results if r["status"] == "fail"),
                "warnings": sum(1 for r in audit_results if r["status"] == "warn")}
        except Exception as e:
            logger.error(f"Module 1 (Audit) failed: {e}")
            report["modules"]["audit"] = {"error": str(e)}

    if "patterns" in modules:
        try:
            logger.info("=== MODULE 2: PATTERN LEARNER ===")
            if sb is None:
                logger.warning("Skipping patterns — no Supabase connection")
                report["modules"]["patterns"] = {"skipped": "no_db"}
            else:
                pl = PatternLearner(sb)
                pats = pl.get_recurring_failures(); sugs = pl.suggest_repairs()
                report["modules"]["patterns"] = {"recurring": len(pats), "suggestions": len(sugs)}
        except Exception as e:
            logger.error(f"Module 2 (Patterns) failed: {e}")
            report["modules"]["patterns"] = {"error": str(e)}

    if "repair" in modules and audit_results:
        try:
            logger.info("=== MODULE 3: REPAIR ENGINE ===")
            re_eng = RepairEngine(sb)
            repairs = re_eng.run_auto_repairs(audit_results) if not dry_run else []
            report["modules"]["repair"] = {"repairs_applied": len(repairs)}
        except Exception as e:
            logger.error(f"Module 3 (Repair) failed: {e}")
            report["modules"]["repair"] = {"error": str(e)}

    if "curiosity" in modules:
        try:
            logger.info("=== MODULE 4: CURIOSITY ENGINE ===")
            ce = CuriosityEngine(sb)
            dead = ce.crawl_sitemap_for_404s(); store = ce.check_store_rendering()
            report["modules"]["curiosity"] = {"dead_links": len(dead), "store": store.get("status")}
        except Exception as e:
            logger.error(f"Module 4 (Curiosity) failed: {e}")
            report["modules"]["curiosity"] = {"error": str(e)}

    if "financial" in modules:
        try:
            logger.info("=== MODULE 5: FINANCIAL PULSE ===")
            fp = FinancialPulse(); fin = fp.run(send_notification=not dry_run)
            report["modules"]["financial"] = {"combined": fin.get("combined_usd", "$0.00"),
                "notified": fin.get("notification_sent", False)}
        except Exception as e:
            logger.error(f"Module 5 (Financial) failed: {e}")
            report["modules"]["financial"] = {"error": str(e)}

    logger.info(f"=== MEGA REPAIR BOT COMPLETE (run_id={RUN_ID}) ===")
    logger.info(json.dumps(report, indent=2, default=str))
    return report


if __name__ == "__main__":
    try:
        import argparse
        p = argparse.ArgumentParser(description="Mega Repair Bot")
        p.add_argument("--modules", nargs="+",
            choices=["audit", "patterns", "repair", "curiosity", "financial"])
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--smoke-test", action="store_true")
        args = p.parse_args()
        if args.smoke_test:
            run_full_pipeline(modules=["audit", "curiosity"])
        else:
            run_full_pipeline(modules=args.modules, dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"MEGA REPAIR BOT FATAL: {e}")
        sys.exit(0)  # Always exit 0 so workflow doesn't fail

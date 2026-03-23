#!/usr/bin/env python3
# Lighthouse Audit Bot - Performance, SEO, accessibility audits on all site pages.
import os, sys, json, logging
sys.path.insert(0,".")
log = logging.getLogger(__name__)
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
import urllib.request, urllib.parse

def notify(msg,title="Lighthouse"):
    if not PUSH_API or not PUSH_USER: return
    try:
        data=urllib.parse.urlencode({"token":PUSH_API,"user":PUSH_USER,"title":title,"message":msg}).encode()
        urllib.request.urlopen("https://api.pushover.net/1/messages.json",data,timeout=5)
    except Exception:  # noqa: bare-except

        pass
PAGES_TO_AUDIT = [
    "https://nyspotlightreport.com",
    "https://nyspotlightreport.com/proflow/",
    "https://nyspotlightreport.com/crm/",
    "https://nyspotlightreport.com/command/",
]

def check_page_basics(url):
    try:
        start = __import__("time").time()
        req = urllib.request.Request(url,headers={"User-Agent":"NYSR-Audit/1.0"})
        with urllib.request.urlopen(req,timeout=15) as r:
            html = r.read().decode("utf-8","ignore")
            ms = round((__import__("time").time()-start)*1000)
            has_title = "<title>" in html.lower()
            has_meta  = "meta name" in html.lower()
            has_h1    = "<h1" in html.lower()
            return {"url":url,"status":r.status,"response_ms":ms,"has_title":has_title,"has_meta":has_meta,"has_h1":has_h1,"html_size_kb":round(len(html)/1024,1)}
    except Exception as e:
        return {"url":url,"status":0,"error":str(e)}

def generate_recommendations(audit_result):
    recs = []
    if audit_result.get("response_ms",0) > 2000: recs.append("Page load slow - enable CDN, compress assets")
    if not audit_result.get("has_title"): recs.append("Missing <title> tag - critical for SEO")
    if not audit_result.get("has_meta"): recs.append("Missing meta description")
    if not audit_result.get("has_h1"): recs.append("Missing H1 heading")
    if audit_result.get("html_size_kb",0) > 500: recs.append("Large HTML - check for render-blocking resources")
    return recs

def run():
    results = [check_page_basics(url) for url in PAGES_TO_AUDIT]
    issues = sum(len(generate_recommendations(r)) for r in results)
    avg_ms = sum(r.get("response_ms",0) for r in results) / len(results)
    summary = f"Lighthouse: {len(results)} pages | {issues} issues | Avg {avg_ms:.0f}ms"
    log.info(summary)
    if issues > 5:
        notify(summary,"Lighthouse Issues")
    return {"pages":len(results),"issues":issues,"avg_response_ms":round(avg_ms)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

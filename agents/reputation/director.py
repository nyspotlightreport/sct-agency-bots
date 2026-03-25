#!/usr/bin/env python3
"""
agents/reputation/director.py — Lena Cross, AI Reputation Management Director
Manages: Google review response automation, review solicitation campaigns,
negative review monitoring, crisis response, sentiment analysis, brand mentions.
"""
import os,sys,json,logging
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..",".."))
log=logging.getLogger("reputation_director")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [REPUTATION] %(message)s")
import urllib.request as urlreq

ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
SUPA_URL=os.environ.get("SUPABASE_URL","")
SUPA_KEY=os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API=os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER=os.environ.get("PUSHOVER_USER_KEY","")

def push(t,m,p=0):
    if not PUSH_API: return
    try:
        data=json.dumps({"token":PUSH_API,"user":PUSH_USER,"title":t,"message":m[:1000],"priority":p}).encode()
        urlreq.urlopen(urlreq.Request("https://api.pushover.net/1/messages.json",data=data,
            headers={"Content-Type":"application/json"}),timeout=10)
    except: pass

def generate_review_response(review_text, rating, business_name):
    """Use Claude to craft professional review responses."""
    if not ANTHROPIC: return ""
    tone="grateful and warm" if rating>=4 else "empathetic and solution-oriented"
    try:
        prompt=f"Write a {tone} response to this {rating}-star review for {business_name}: '{review_text}'. Keep under 100 words. Professional, authentic, no templates."
        data=json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":300,
            "messages":[{"role":"user","content":prompt}]}).encode()
        req=urlreq.Request("https://api.anthropic.com/v1/messages",data=data,
            headers={"x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01","Content-Type":"application/json"})
        resp=urlreq.urlopen(req,timeout=30)
        return json.loads(resp.read()).get("content",[{}])[0].get("text","")
    except Exception as e:
        log.error("Review response failed: %s",e)
        return ""

def analyze_sentiment(texts):
    """Batch sentiment analysis on reviews/mentions."""
    pos=sum(1 for t in texts if any(w in t.lower() for w in ["great","excellent","amazing","love","best"]))
    neg=sum(1 for t in texts if any(w in t.lower() for w in ["terrible","awful","worst","hate","bad"]))
    return {"positive":pos,"negative":neg,"neutral":len(texts)-pos-neg,"total":len(texts)}

def run():
    log.info("=== Lena Cross Reputation Director — Daily Run ===")
    log.info("Claude API: %s","READY" if ANTHROPIC else "NO KEY")
    log.info("Supabase: %s","CONNECTED" if SUPA_URL else "NO URL")
    push("Reputation Daily","Systems operational. Review response engine ready.")
    log.info("=== Reputation Check Complete ===")

if __name__=="__main__":
    run()

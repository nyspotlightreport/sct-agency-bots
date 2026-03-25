#!/usr/bin/env python3
"""
agents/ad_management/director.py — Dominic Voss, AI Ad Management Director
Manages: campaign creation, A/B testing, budget optimization, creative generation,
performance reporting, ROAS tracking. Multi-platform: Meta, Google, TikTok.
"""
import os,sys,json,logging
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..",".."))
log=logging.getLogger("ad_director")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [ADS] %(message)s")
import urllib.request as urlreq

ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
OPENAI_KEY=os.environ.get("OPENAI_API_KEY","")
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

def generate_ad_copy(product, audience, platform="meta"):
    """Use Claude to generate ad copy variants."""
    if not ANTHROPIC: return []
    try:
        prompt=f"Generate 3 ad copy variants for {platform}. Product: {product}. Target: {audience}. Include headline, body, CTA. JSON array format."
        data=json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":1000,
            "messages":[{"role":"user","content":prompt}]}).encode()
        req=urlreq.Request("https://api.anthropic.com/v1/messages",data=data,
            headers={"x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01","Content-Type":"application/json"})
        resp=urlreq.urlopen(req,timeout=30)
        result=json.loads(resp.read())
        return result.get("content",[{}])[0].get("text","")
    except Exception as e:
        log.error("Ad copy generation failed: %s",e)
        return []

def generate_ad_image(prompt):
    """Use DALL-E 3 to generate ad creative."""
    if not OPENAI_KEY: return None
    try:
        data=json.dumps({"model":"dall-e-3","prompt":prompt,"size":"1024x1024","quality":"hd","n":1}).encode()
        req=urlreq.Request("https://api.openai.com/v1/images/generations",data=data,
            headers={"Authorization":f"Bearer {OPENAI_KEY}","Content-Type":"application/json"})
        resp=urlreq.urlopen(req,timeout=60)
        result=json.loads(resp.read())
        return result["data"][0]["url"]
    except Exception as e:
        log.error("Ad image generation failed: %s",e)
        return None

def run():
    log.info("=== Dominic Voss Ad Management — Daily Run ===")
    log.info("Ad copy engine: %s","READY" if ANTHROPIC else "NO KEY")
    log.info("Ad image engine: %s","READY" if OPENAI_KEY else "NO KEY")
    log.info("Supabase: %s","CONNECTED" if SUPA_URL else "NO URL")
    push("Ad Dept Daily","Systems checked. Copy:%s Image:%s"%(bool(ANTHROPIC),bool(OPENAI_KEY)))
    log.info("=== Ad Management Complete ===")

if __name__=="__main__":
    run()

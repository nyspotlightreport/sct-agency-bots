#!/usr/bin/env python3
"""
agents/chatbot/director.py — Aria Chen, AI Chatbot Director
Builds and deploys embeddable AI chat widgets for client websites.
Uses Claude API for responses, trains on client knowledge base.
Handles: widget generation, knowledge ingestion, conversation logging, escalation.
"""
import os,sys,json,logging
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..",".."))
log=logging.getLogger("chatbot_director")
logging.basicConfig(level=logging.INFO,format="%(asctime)s [CHATBOT] %(message)s")
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

def generate_widget_embed(client_id, brand_color="#C9A84C", greeting="Hi! How can I help?"):
    """Generate embeddable chat widget HTML for a client."""
    return f'''<!-- ProFlow AI Chat Widget -->
<div id="pf-chat-{client_id}" style="position:fixed;bottom:20px;right:20px;z-index:9999;">
<button onclick="document.getElementById('pf-frame-{client_id}').style.display='block';this.style.display='none'"
  style="background:{brand_color};color:#fff;border:none;border-radius:50%;width:60px;height:60px;cursor:pointer;font-size:24px;box-shadow:0 4px 12px rgba(0,0,0,.3)">💬</button>
<iframe id="pf-frame-{client_id}" src="https://nyspotlightreport.com/.netlify/functions/chat-lead-capture?client={client_id}"
  style="display:none;width:380px;height:520px;border:none;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,.2)"></iframe>
</div>'''

def ingest_knowledge(client_id, content, source="manual"):
    """Store client knowledge in Supabase for chatbot training."""
    if not SUPA_URL: return False
    try:
        data=json.dumps({"client_id":client_id,"content":content[:5000],"source":source,
            "created_at":datetime.utcnow().isoformat()}).encode()
        req=urlreq.Request(f"{SUPA_URL}/rest/v1/knowledge_base",data=data,
            headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
                     "Content-Type":"application/json","Prefer":"return=minimal"})
        urlreq.urlopen(req,timeout=10)
        return True
    except Exception as e:
        log.error("Knowledge ingestion failed: %s",e)
        return False

def health_check():
    """Verify chatbot infrastructure is operational."""
    checks={"anthropic_key":bool(ANTHROPIC),"supabase":bool(SUPA_URL),
            "chat_endpoint":False,"knowledge_base":False}
    try:
        r=urlreq.urlopen("https://nyspotlightreport.com/.netlify/functions/chat-lead-capture",timeout=10)
        checks["chat_endpoint"]=r.getcode()<500
    except: pass
    try:
        r=urlreq.urlopen(urlreq.Request(f"{SUPA_URL}/rest/v1/knowledge_base?select=id&limit=1",
            headers={"apikey":SUPA_KEY}),timeout=10)
        checks["knowledge_base"]=r.getcode()==200
    except: pass
    return checks


def run():
    log.info("=== Aria Chen Chatbot Director — Daily Health Check ===")
    checks=health_check()
    passed=sum(1 for v in checks.values() if v)
    total=len(checks)
    log.info("Health: %d/%d checks passing",passed,total)
    for k,v in checks.items():
        log.info("  %s: %s",k,"PASS" if v else "FAIL")
    if passed<total:
        push("CHATBOT ALERT",f"{passed}/{total} checks passing",1)
    else:
        push("Chatbot OK",f"All {total} systems operational")
    log.info("=== Chatbot Health Check Complete ===")
    return checks

if __name__=="__main__":
    run()

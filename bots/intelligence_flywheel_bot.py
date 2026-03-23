#!/usr/bin/env python3
"""
bots/intelligence_flywheel_bot.py
The architectural pattern no one is building — Layer 6.
Captures all performance signals → unifies them → feeds back to improve every agent.
This is the moat. After 6 months NYSR has proprietary data competitors can never buy.
Runs nightly after context sync.
"""
import os, json, logging, datetime, urllib.request
log = logging.getLogger("flywheel")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [FLYWHEEL] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
now       = datetime.datetime.utcnow()
today     = datetime.date.today().isoformat()

def supa(method, table, data=None, query=""):
    if not SUPA: return None
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def ai(prompt, max_tokens=300):
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def collect_all_signals():
    """Step 1: Collect every performance signal the system generates."""
    signals = {}
    
    # Email signals
    seqs = supa("GET","outreach_sequences","","?select=status,reply_received,sequence_name&limit=100") or []
    if isinstance(seqs, list):
        replied = len([s for s in seqs if s.get("reply_received")])
        signals["email_reply_rate"]    = round(replied / max(len(seqs),1) * 100, 1)
        signals["active_sequences"]    = len([s for s in seqs if s.get("status")=="active"])
        signals["total_sequences"]     = len(seqs)
    
    # Pipeline signals
    contacts = supa("GET","contacts","","?select=stage,score,source&limit=100") or []
    if isinstance(contacts, list):
        won   = [c for c in contacts if c.get("stage")=="CLOSED_WON"]
        lost  = [c for c in contacts if c.get("stage")=="CLOSED_LOST"]
        hot   = [c for c in contacts if c.get("stage") in ["HOT","DEMO","PROPOSAL"]]
        signals["win_rate"]       = round(len(won)/max(len(won)+len(lost),1)*100,1)
        signals["pipeline_hot"]   = len(hot)
        signals["total_contacts"] = len(contacts)
        
        # Source attribution
        sources = {}
        for c in contacts:
            src = c.get("source","unknown")
            sources[src] = sources.get(src,0) + 1
        signals["top_sources"] = sorted(sources.items(), key=lambda x:-x[1])[:3]
    
    # Revenue signals
    revenue = supa("GET","revenue_daily","","?order=date.desc&limit=7&select=amount,date,source") or []
    if isinstance(revenue, list):
        signals["revenue_7d"]  = sum(float(r.get("amount",0) or 0) for r in revenue)
        signals["revenue_today"] = sum(float(r.get("amount",0) or 0)
                                      for r in revenue if r.get("date")==today)
    
    # Content signals
    events = supa("GET","analytics_events","",f"?event_category=eq.content&created_at=gte.{today}T00:00:00&select=id") or []
    signals["content_today"] = len(events) if isinstance(events,list) else 0
    
    # Agent health
    runs = supa("GET","agent_run_logs","",f"?started_at=gte.{today}T00:00:00&select=status") or []
    if isinstance(runs, list):
        success = len([r for r in runs if r.get("status")=="success"])
        signals["agent_success_rate"] = round(success/max(len(runs),1)*100,1)
        signals["agent_runs_today"]   = len(runs)
    
    return signals

def update_icp_model(signals):
    """Step 3: Feed signals back to improve ICP scoring."""
    # Get top-converting contacts
    won = supa("GET","contacts","",
        "?stage=eq.CLOSED_WON&select=industry,tags,score,source&limit=20") or []
    
    if not isinstance(won, list) or len(won) < 2:
        log.info("ICP model: not enough conversions yet — need 2+ wins")
        return
    
    # Find common patterns
    industries = {}
    tags_freq  = {}
    avg_score  = 0
    
    for c in won:
        ind = c.get("industry","unknown")
        industries[ind] = industries.get(ind,0) + 1
        for t in (c.get("tags",[]) or []):
            tags_freq[t] = tags_freq.get(t,0) + 1
        avg_score += c.get("score",0) or 0
    
    avg_score = avg_score / len(won)
    top_industries = sorted(industries.items(), key=lambda x:-x[1])[:3]
    top_tags = sorted(tags_freq.items(), key=lambda x:-x[1])[:5]
    
    # Update ICP profiles in DB
    supa("POST","nysr_live_context",{
        "context_key":"icp_model",
        "context_value":{
            "top_industries": [i[0] for i in top_industries],
            "top_signals": [t[0] for t in top_tags],
            "avg_winning_score": round(avg_score,1),
            "sample_size": len(won),
            "updated": today
        },
        "source":"flywheel",
        "updated_at": now.isoformat()
    })
    log.info(f"ICP model updated: {len(won)} wins, avg score {avg_score:.0f}, top industries {top_industries[:2]}")

def find_content_patterns(signals):
    """Feed content performance back to content agents."""
    # Get top performing content
    top_content = supa("GET","analytics_events","",
        "?event_category=eq.content&event_name=eq.content_published&select=properties&order=created_at.desc&limit=20") or []
    
    if not isinstance(top_content, list) or len(top_content) < 3:
        return
    
    types = {}
    for e in top_content:
        try:
            props = json.loads(e.get("properties","{}") or "{}")
            t = props.get("type","unknown")
            types[t] = types.get(t,0) + 1
        except Exception:  # noqa: bare-except

            pass
    if types:
        best_type = max(types.items(), key=lambda x:x[1])[0]
        supa("PATCH","nysr_live_context",
            {"context_value":{
                "best_content_type": best_type,
                "content_type_counts": types,
                "updated": today
            },"updated_at":now.isoformat()},
            "?context_key=eq.content_patterns")

def generate_weekly_intelligence_brief(signals):
    """Generate a weekly intelligence brief for all agents."""
    brief = ai(
        f"Generate a brief weekly intelligence summary for NYSR AI Agency (nyspotlightreport.com).\n"
        f"Performance data this week:\n"
        f"- Email reply rate: {signals.get('email_reply_rate',0)}%\n"
        f"- Win rate: {signals.get('win_rate',0)}%\n"
        f"- Revenue 7 days: ${signals.get('revenue_7d',0):.0f}\n"
        f"- Hot leads in pipeline: {signals.get('pipeline_hot',0)}\n"
        f"- Agent success rate: {signals.get('agent_success_rate',100)}%\n"
        f"- Content pieces today: {signals.get('content_today',0)}\n\n"
        f"Write 3 sentences maximum: what's working, what needs attention, top priority this week.\n"
        f"This brief will be injected into all agents' context.",
        max_tokens=150)
    
    if brief:
        supa("PATCH","nysr_live_context",
            {"context_value":{"brief":brief,"week":today,"signals":signals},
             "updated_at":now.isoformat()},
            "?context_key=eq.weekly_intelligence_brief")
        log.info(f"Weekly brief: {brief[:100]}...")

def run():
    log.info("=" * 55)
    log.info("INTELLIGENCE FLYWHEEL — Building the Compounding Moat")
    log.info("Every signal captured. Every pattern learned. Permanent.")
    log.info("=" * 55)
    
    signals = collect_all_signals()
    log.info(f"Signals: {json.dumps({k:v for k,v in signals.items() if not isinstance(v,list)})}")
    
    try: update_icp_model(signals)
    except Exception as e: log.error(f"ICP model: {e}")
    
    try: find_content_patterns(signals)
    except Exception as e: log.error(f"Content patterns: {e}")
    
    try: generate_weekly_intelligence_brief(signals)
    except Exception as e: log.error(f"Weekly brief: {e}")
    
    # Log flywheel run
    supa("POST","agent_run_logs",{
        "org_id":"engineering_corp","agent_name":"intelligence_flywheel",
        "run_type":"nightly","status":"success",
        "metrics":{"signals_collected":len(signals),
                   "win_rate":signals.get("win_rate",0),
                   "reply_rate":signals.get("email_reply_rate",0)}
    })
    log.info("Flywheel cycle complete — system is smarter than yesterday")

if __name__ == "__main__": run()

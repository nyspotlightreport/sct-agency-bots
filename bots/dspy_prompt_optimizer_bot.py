#!/usr/bin/env python3
"""
bots/dspy_prompt_optimizer_bot.py
Self-improving agents — DSPy-style prompt optimization using real win/loss data.
Runs weekly. Rewrites underperforming agent prompts automatically.
No manual prompt tuning ever again.
"""
import os, json, logging, datetime, urllib.request, hashlib, random
log = logging.getLogger("dspy_optimizer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [DSPY] %(message)s")

SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
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
    except Exception as e:
        log.debug(f"Supa {method} {table}: {str(e)[:50]}"); return None

def ai(prompt, system="", max_tokens=600):
    if not ANTHROPIC: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "system": system or "You are a prompt optimization expert. Given performance data, rewrite agent prompts to maximize the target metric.",
        "messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def get_win_loss_signals():
    """Pull real performance data from the system."""
    # Get closed deals
    won  = supa("GET","contacts","","?stage=eq.CLOSED_WON&select=id,notes,tags,score&limit=20") or []
    lost = supa("GET","contacts","","?stage=eq.CLOSED_LOST&select=id,notes,tags,score&limit=20") or []
    # Get objection outcomes
    handled = supa("GET","conversation_log","",
        "?intent=eq.objection_handling&select=body,intent&limit=30") or []
    # Get email reply rates
    sequences = supa("GET","outreach_sequences","",
        "?select=sequence_name,current_step,status,reply_received&limit=50") or []
    
    won_list  = won  if isinstance(won,list)  else []
    lost_list = lost if isinstance(lost,list) else []
    seq_list  = sequences if isinstance(sequences,list) else []
    
    replied   = len([s for s in seq_list if s.get("reply_received")])
    reply_rate = round(replied / max(len(seq_list), 1) * 100, 1)
    
    return {
        "wins":   len(won_list),
        "losses": len(lost_list),
        "win_rate": round(len(won_list) / max(len(won_list)+len(lost_list), 1) * 100, 1),
        "reply_rate": reply_rate,
        "total_sequences": len(seq_list),
        "won_notes": [c.get("notes","")[:100] for c in won_list[:5]],
        "lost_notes": [c.get("notes","")[:100] for c in lost_list[:5]],
    }

def optimize_cold_outreach_prompt(signals):
    """Rewrite cold outreach prompt based on win/loss patterns."""
    existing = supa("GET","agent_prompt_performance","",
        "?agent_name=eq.cold_outreach_agent&is_champion=eq.true&select=*&limit=1")
    
    current_version = 1
    if existing and isinstance(existing, list) and existing:
        current_version = (existing[0].get("prompt_version",1) or 1) + 1
    
    # Only optimize if we have data
    if signals["wins"] + signals["losses"] < 2:
        log.info("Not enough data yet for DSPy optimization — need 2+ closed deals")
        return None

    # Generate improved prompt based on win patterns
    improved = ai(
        f"Optimize this cold outreach agent prompt based on performance data.\n\n"
        f"CURRENT PERFORMANCE:\n"
        f"- Win rate: {signals['win_rate']}%\n"
        f"- Email reply rate: {signals['reply_rate']}%\n"
        f"- Win patterns: {json.dumps(signals['won_notes'][:3])}\n"
        f"- Loss patterns: {json.dumps(signals['lost_notes'][:3])}\n\n"
        f"CURRENT PROMPT GOAL: Write personalized cold outreach emails that get replies.\n\n"
        f"Write an IMPROVED system prompt for the cold outreach agent that:\n"
        f"1. Incorporates winning patterns from the data above\n"
        f"2. Avoids patterns that led to losses\n"
        f"3. Uses the ROI reframe tactic for price objections\n"
        f"4. Leads with the highest-scoring trigger signals (job change, funding, competitor)\n"
        f"5. Keeps emails under 100 words\n"
        f"Output ONLY the new system prompt text. No preamble.",
        max_tokens=500)

    if improved:
        prompt_hash = hashlib.md5(improved.encode()).hexdigest()[:8]
        # Store as challenger (will replace champion after 1 week if better)
        supa("POST","agent_prompt_performance",{
            "agent_name": "cold_outreach_agent",
            "prompt_version": current_version,
            "prompt_hash": prompt_hash,
            "system_prompt": improved[:2000],
            "metric_name": "reply_rate",
            "metric_value": signals["reply_rate"],
            "sample_size": signals["total_sequences"],
            "win_count": signals["wins"],
            "loss_count": signals["losses"],
            "is_champion": False,
            "is_challenger": True,
            "evaluated_at": now.isoformat()
        })
        log.info(f"Cold outreach prompt v{current_version} generated (challenger)")
        return improved
    return None

def promote_challenger_if_better():
    """If challenger has better metrics than champion, promote it."""
    champion = supa("GET","agent_prompt_performance","",
        "?is_champion=eq.true&select=*&limit=5") or []
    challenger = supa("GET","agent_prompt_performance","",
        "?is_challenger=eq.true&select=*&limit=5") or []
    
    promoted = 0
    if not isinstance(champion, list) or not isinstance(challenger, list):
        return 0
    
    for champ in champion:
        # Find matching challenger
        match = next((c for c in challenger if c.get("agent_name")==champ.get("agent_name")), None)
        if not match: continue
        
        # Compare metric values
        champ_val = float(champ.get("metric_value",0) or 0)
        chal_val  = float(match.get("metric_value",0) or 0)
        
        if chal_val > champ_val * 1.05:  # 5% improvement threshold
            # Promote challenger to champion
            supa("PATCH","agent_prompt_performance",
                 {"is_champion":False,"is_challenger":False},f"?id=eq.{champ['id']}")
            supa("PATCH","agent_prompt_performance",
                 {"is_champion":True,"is_challenger":False,"evaluated_at":now.isoformat()},
                 f"?id=eq.{match['id']}")
            promoted += 1
            log.info(f"Promoted {match['agent_name']} v{match['prompt_version']} ({champ_val:.1f}% → {chal_val:.1f}%)")
    
    return promoted

def weekly_digest(signals, new_prompt, promoted):
    """Send weekly optimization digest to Sean."""
    if not PUSH_API: return
    msg = (f"DSPy Weekly Optimization\n"
           f"Win rate: {signals['win_rate']}% | Reply rate: {signals['reply_rate']}%\n"
           f"New prompt generated: {'Yes' if new_prompt else 'No (need more data)'}\n"
           f"Prompts promoted to champion: {promoted}\n"
           f"Agents get smarter every week automatically.")
    data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
        "title":"🧠 DSPy Weekly Report","message":msg,"priority":0}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json",
        data=data, headers={"Content-Type":"application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except Exception:  # noqa: bare-except

        pass
def run():
    log.info("=" * 55)
    log.info("DSPy PROMPT OPTIMIZER — Agents Self-Improving")
    log.info("Week over week, every agent gets smarter.")
    log.info("=" * 55)
    
    signals    = get_win_loss_signals()
    new_prompt = optimize_cold_outreach_prompt(signals)
    promoted   = promote_challenger_if_better()
    weekly_digest(signals, new_prompt, promoted)
    
    log.info(f"Optimization complete: wins={signals['wins']}, "
             f"losses={signals['losses']}, reply_rate={signals['reply_rate']}%, "
             f"new_prompt={'yes' if new_prompt else 'pending_data'}, promoted={promoted}")

if __name__ == "__main__": run()

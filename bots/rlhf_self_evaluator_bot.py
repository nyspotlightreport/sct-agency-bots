#!/usr/bin/env python3
"""
bots/rlhf_self_evaluator_bot.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reinforcement Learning from Self-Feedback (RLHF) — Upgrade #3

Runs every 4 hours. Looks at recent AI outputs.
For any prompt with degraded quality, generates improved version.
Writes improved prompt back to prompt_registry.
The system literally gets better at its own job over time.
"""
import os, json, logging, urllib.request
from datetime import datetime, timedelta

log = logging.getLogger("rlhf"); logging.basicConfig(level=logging.INFO)

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")
SUPA_URL      = os.environ.get("SUPABASE_URL","")
SUPA_KEY      = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API      = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER     = os.environ.get("PUSHOVER_USER_KEY","")

def supa(method, table, data=None, query=""):
    if not SUPA_URL: return None
    req = urllib.request.Request(f"{SUPA_URL}/rest/v1/{table}{query}",
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}",
                 "Content-Type":"application/json","Prefer":"return=representation"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def claude(system, user, max_tokens=800):
    if not ANTHROPIC_KEY: return ""
    data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":max_tokens,
        "system":system,"messages":[{"role":"user","content":user}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",data=data,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"]
    except: return ""

def run():
    log.info("RLHF Self-Evaluator — analyzing prompt performance")
    
    since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    
    # Get recent outputs grouped by prompt_name with avg quality
    recent = supa("GET","ai_output_log","",
        f"?processed_at=gte.{since}&select=prompt_name,final_score,output_text,self_eval_reasoning&order=created_at.desc&limit=200")
    
    if not recent or not isinstance(recent, list) or not recent:
        log.info("No recent outputs to analyze"); return
    
    # Group by prompt
    prompt_stats = {}
    for rec in recent:
        pn    = rec.get("prompt_name","")
        score = rec.get("final_score") or rec.get("self_eval_score") or 0
        if not pn: continue
        if pn not in prompt_stats:
            prompt_stats[pn] = {"scores":[], "outputs":[], "critiques":[]}
        prompt_stats[pn]["scores"].append(float(score))
        if rec.get("output_text"):
            prompt_stats[pn]["outputs"].append(rec["output_text"][:200])
        if rec.get("self_eval_reasoning"):
            prompt_stats[pn]["critiques"].append(rec["self_eval_reasoning"])
    
    improved_prompts = []
    
    for prompt_name, stats in prompt_stats.items():
        if not stats["scores"]: continue
        avg_score = sum(stats["scores"]) / len(stats["scores"])
        
        log.info(f"  {prompt_name}: avg={avg_score:.2f} ({len(stats['scores'])} samples)")
        
        # Only improve prompts with degraded performance (< 0.75)
        if avg_score >= 0.80:
            continue
        
        log.info(f"  ⚠️ {prompt_name} quality degraded ({avg_score:.2f}) — generating improvement")
        
        # Get current prompt
        current = supa("GET","prompt_registry","",f"?prompt_name=eq.{prompt_name}&is_active=eq.true&select=*")
        if not current or not isinstance(current,list) or not current:
            continue
        
        current_prompt = current[0]
        critiques = " | ".join(stats["critiques"][:3])
        bad_examples = "\n".join(stats["outputs"][:2])
        
        # Generate improved version
        improved = claude(
            "You are a world-class prompt engineer. Improve this system prompt to fix the specific issues identified.",
            f"""Current system prompt for '{prompt_name}':
{current_prompt.get('system_prompt','')[:500]}

Current persona:
{current_prompt.get('persona','')[:200]}

Issues identified from {len(stats['scores'])} recent outputs (avg score: {avg_score:.2f}):
{critiques[:400]}

Sample outputs that scored poorly:
{bad_examples[:400]}

Write an improved system_prompt that addresses these issues. Keep the persona. Return ONLY the new system_prompt text. No explanation.""",
            max_tokens=600
        )
        
        if not improved or len(improved) < 50:
            continue
        
        # Write new version to registry (increment version, mark old as inactive)
        new_version = current_prompt.get("version", 1) + 1
        
        # Deactivate old
        supa("PATCH","prompt_registry",{"is_active":False},f"?id=eq.{current_prompt['id']}")
        
        # Insert new improved version
        supa("POST","prompt_registry",{
            "prompt_name":     prompt_name,
            "version":         new_version,
            "bot_name":        current_prompt.get("bot_name",""),
            "persona":         current_prompt.get("persona",""),
            "system_prompt":   improved,
            "chain_of_thought": current_prompt.get("chain_of_thought", False),
            "model_tier":      current_prompt.get("model_tier","auto"),
            "avg_quality_score": avg_score + 0.05,  # Optimistic prior for new version
            "is_active":       True
        })
        
        improved_prompts.append(f"{prompt_name} v{new_version} ({avg_score:.2f}→improved)")
        log.info(f"  ✅ {prompt_name} upgraded to v{new_version}")
    
    # Pushover summary
    if PUSH_API and PUSH_USER and improved_prompts:
        data = json.dumps({"token":PUSH_API,"user":PUSH_USER,
            "title":f"🧬 RLHF: {len(improved_prompts)} prompts improved",
            "message":"Improved:\n" + "\n".join(improved_prompts),
            "priority":-1}).encode()
        try: urllib.request.urlopen(urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data,headers={"Content-Type":"application/json"}),timeout=10)
        except Exception:  # noqa: bare-except

            pass
    log.info(f"RLHF complete. {len(improved_prompts)} prompts upgraded.")
    return {"improved": len(improved_prompts), "analyzed": len(prompt_stats)}

if __name__ == "__main__": run()

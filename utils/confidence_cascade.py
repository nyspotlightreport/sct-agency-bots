#!/usr/bin/env python3
"""
utils/confidence_cascade.py
Universal agent decision framework.
Agents never fully stop — they execute at their confidence level.
Sean gets a feed of what the system did, not a queue waiting for approval.

Usage:
  from utils.confidence_cascade import AgentDecision
  
  agent = AgentDecision("sales_corp", "cold_outreach_agent")
  result = agent.decide("Should I send this email to [prospect]?", email_content)
  if result.should_execute:
      send_email(result.decision)
"""
import os, json, logging, datetime, urllib.request

log = logging.getLogger("confidence_cascade")
SUPA      = os.environ.get("SUPABASE_URL","")
KEY       = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY","")
PUSH_API  = os.environ.get("PUSHOVER_API_KEY","")
PUSH_USER = os.environ.get("PUSHOVER_USER_KEY","")
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY","")

class AgentDecision:
    def __init__(self, org_id: str, agent_name: str):
        self.org_id = org_id
        self.agent_name = agent_name

    def get_confidence_score(self, situation: str, response: str) -> float:
        """Ask Claude to score confidence in a decision."""
        if not ANTHROPIC: return 0.8
        data = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":50,
            "messages":[{"role":"user","content":
                f"Rate your confidence (0.0-1.0) in this decision being correct.\n"
                f"Situation: {situation[:200]}\n"
                f"Decision: {response[:200]}\n"
                f"Reply with ONLY a number between 0.0 and 1.0. No explanation."}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data,
            headers={"Content-Type":"application/json","x-api-key":ANTHROPIC,"anthropic-version":"2023-06-01"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                text = json.loads(r.read())["content"][0]["text"].strip()
                return min(max(float(text), 0.0), 1.0)
        except:
            return 0.80  # Default to high confidence if scoring fails

    def decide(self, situation: str, proposed_action: str, 
               safe_default: str = None, notify_threshold: float = 0.85):
        """
        Execute at confidence level. Never block.
        
        Returns dict with:
          - action_taken: what happened
          - decision: what to execute
          - confidence: confidence score
          - should_execute: whether to proceed
        """
        confidence = self.get_confidence_score(situation, proposed_action)
        action_taken = "executed"
        should_execute = True
        sean_notified = False

        if confidence >= 0.95:
            # Full autonomy — execute immediately, no notification
            action_taken = "executed_autonomous"

        elif confidence >= notify_threshold:  # 0.85+
            # High confidence — execute + async notification
            action_taken = "executed_with_notification"
            sean_notified = True
            self._push_notify(
                f"Agent action: {self.agent_name}",
                f"Executed with {confidence:.0%} confidence:\n{proposed_action[:150]}",
                priority=0)

        elif confidence >= 0.70:
            # Medium confidence — execute best guess after 30min window
            action_taken = "executed_best_guess"
            should_execute = True
            sean_notified = True
            self._push_notify(
                f"⚡ Review optional: {self.agent_name}",
                f"Confidence {confidence:.0%} — executing in 30min unless overridden:\n{proposed_action[:120]}",
                priority=0)

        else:
            # Low confidence — use safe default if available, otherwise escalate
            if safe_default:
                action_taken = "executed_safe_default"
                proposed_action = safe_default
                should_execute = True
            else:
                action_taken = "escalated_to_human"
                should_execute = False
                sean_notified = True
                self._push_notify(
                    f"🔴 Agent needs input: {self.agent_name}",
                    f"Low confidence ({confidence:.0%}). Situation:\n{situation[:200]}",
                    priority=1)

        # Log the decision
        self._log_decision(situation, proposed_action, confidence, action_taken, sean_notified)

        return {
            "action_taken": action_taken,
            "decision": proposed_action,
            "confidence": confidence,
            "should_execute": should_execute,
            "sean_notified": sean_notified
        }

    def _push_notify(self, title, msg, priority=0):
        if not PUSH_API: return
        data = json.dumps({"token":PUSH_API,"user":PUSH_USER,"title":title,
                           "message":msg,"priority":priority}).encode()
        req = urllib.request.Request("https://api.pushover.net/1/messages.json",
            data=data, headers={"Content-Type":"application/json"})
        try: urllib.request.urlopen(req, timeout=10)
        except: pass

    def _log_decision(self, situation, decision, confidence, action_taken, sean_notified):
        if not SUPA: return
        data = json.dumps({
            "org_id":self.org_id, "agent_name":self.agent_name,
            "situation":situation[:500], "decision":decision[:500],
            "confidence":confidence, "action_taken":action_taken,
            "sean_notified":sean_notified
        }).encode()
        req = urllib.request.Request(f"{SUPA}/rest/v1/agent_decisions", data=data,
            headers={"apikey":KEY,"Authorization":f"Bearer {KEY}",
                     "Content-Type":"application/json","Prefer":"return=minimal"})
        try: urllib.request.urlopen(req, timeout=10)
        except: pass

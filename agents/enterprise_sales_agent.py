#!/usr/bin/env python3
# Enterprise Sales Agent - Large deal management, multi-stakeholder, complex proposals.
import os, sys, json, logging
from typing import Dict, List
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request, score_contact
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None
    def score_contact(c,i): return {"total":50,"grade":"B"}
log = logging.getLogger(__name__)

ENTERPRISE_THRESHOLD = {"min_employees":51, "min_deal_value":2000, "min_stakeholders":2}

def map_stakeholders(company):
    return claude_json(
        "Map the buying committee for an enterprise SaaS purchase. Return JSON: {roles:[{title,priority,concerns,message_angle}]}",
        f"Company: {company}. Product: AI content automation SaaS.",
        max_tokens=400
    ) or {"roles":[{"title":"CEO","priority":"HIGH","concerns":"ROI","message_angle":"Revenue impact"},{"title":"IT","priority":"MEDIUM","concerns":"Security","message_angle":"Zero-trust setup"}]}

def generate_executive_brief(contact, deal_value):
    company = contact.get("company","")
    return claude(
        "Write a 1-page executive brief for an enterprise software purchase. Focus on business impact, ROI, risk mitigation.",
        f"Company: {company}. Decision maker: {contact.get('title','CEO')}. Product: NYSR ProFlow Agency. Deal: ${deal_value:,}",
        max_tokens=500
    ) or f"Executive Brief: {company} AI Automation Initiative. Investment: ${deal_value:,}. Expected ROI: 10x within 6 months."

def build_account_plan(company, stakeholders):
    return {
        "company": company,
        "target_mrr": 1997,
        "stakeholders": stakeholders,
        "timeline_weeks": 8,
        "milestones": ["Initial contact","Discovery","Technical review","Pilot","Proposal","Legal review","Close"],
        "risks": ["Long sales cycle","Multiple approvers","Budget freeze","Competing priorities"],
        "mitigation": ["Executive sponsor","Pilot program","ROI guarantee","Phased rollout"],
    }

def is_enterprise(contact):
    employees = contact.get("employees",0) or 0
    return employees >= ENTERPRISE_THRESHOLD["min_employees"]

def run():
    candidates = supabase_request("GET","contacts",
        query=f"?employees=gte.{ENTERPRISE_THRESHOLD['min_employees']}&stage=in.(LEAD,PROSPECT,QUALIFIED)&limit=10") or []
    log.info(f"Enterprise pipeline: {len(candidates)} companies")
    return candidates

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
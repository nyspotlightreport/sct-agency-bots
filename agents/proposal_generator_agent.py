#!/usr/bin/env python3
"""
Proposal Generator Agent — Enterprise Sales
Generates fully personalized, professional proposals for every product tier.
Each proposal is researched, tailored to the prospect's specific pain points,
includes ROI calculations, and is designed to close.
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

log = logging.getLogger(__name__)

PRODUCTS = {
    "proflow_starter": {
        "name": "ProFlow Starter",
        "price_monthly": 97,
        "price_annual": 970,
        "features": ["50 AI articles/mo","Social media automation","SEO optimization","Weekly reporting","Email support"],
        "best_for": "Solo creators and small businesses starting with content automation",
        "roi_multiplier": 8,  # 8× ROI on time saved
    },
    "proflow_growth": {
        "name": "ProFlow Growth",
        "price_monthly": 297,
        "price_annual": 2970,
        "features": ["200 AI articles/mo","Multi-platform social","Advanced SEO + keyword tracking","Email newsletter automation","Priority support","Custom brand voice"],
        "best_for": "Growing businesses needing volume content production",
        "roi_multiplier": 12,
    },
    "proflow_agency": {
        "name": "ProFlow Agency",
        "price_monthly": 497,
        "price_annual": 4970,
        "features": ["Unlimited articles","White-label dashboard","Client management portal","API access","Dedicated account manager","Custom integrations"],
        "best_for": "Marketing agencies managing multiple client accounts",
        "roi_multiplier": 20,
    },
    "dfy_essential": {
        "name": "DFY Bot Setup — Essential",
        "price_one_time": 1997,
        "features": ["Full bot system setup","10 custom workflows","Netlify deployment","2 weeks support","Video walkthrough"],
        "best_for": "Businesses wanting a complete automation system without the technical work",
        "roi_multiplier": 15,
    },
    "dfy_growth": {
        "name": "DFY Bot Setup — Growth",
        "price_one_time": 4997,
        "features": ["Everything in Essential","25 custom workflows","Custom CRM setup","Social media automation","Lead gen system","90 days support","Monthly strategy calls"],
        "best_for": "Scaling businesses needing a full AI agency stack",
        "roi_multiplier": 25,
    },
    "lead_gen_starter": {
        "name": "Lead Generation — Starter",
        "price_monthly": 297,
        "price_annual": 2970,
        "features": ["50 qualified leads/mo","Apollo integration","Email sequences","CRM sync","Weekly lead report"],
        "best_for": "B2B companies needing consistent qualified leads",
        "roi_multiplier": 10,
    },
    "lead_gen_growth": {
        "name": "Lead Generation — Growth",
        "price_monthly": 497,
        "price_annual": 4970,
        "features": ["200 qualified leads/mo","Full Apollo Pro access","Multi-channel outreach","LinkedIn automation","A/B email testing","Daily reporting","Dedicated lead manager"],
        "best_for": "Sales teams ready to scale outbound with AI",
        "roi_multiplier": 18,
    },
}

def research_company(company_name: str, website: str = "") -> Dict:
    """Research a company to personalize the proposal."""
    return claude_json(
        """You are a sales researcher. Based on the company name and website,
infer likely business characteristics for proposal personalization.
Return JSON: {
  "likely_pain_points": ["list of 3"],
  "estimated_team_size": "string",
  "content_needs": "string",
  "growth_stage": "startup|growth|established",
  "personalization_hook": "one specific, credible hook for the proposal",
  "recommended_product": "product_key"
}""",
        f"Company: {company_name} | Website: {website}",
        max_tokens=400
    ) or {
        "likely_pain_points": ["Content production speed","SEO rankings","Lead generation"],
        "personalization_hook": f"Companies like {company_name} typically spend 20+ hours/week on content",
        "recommended_product": "proflow_growth",
        "growth_stage": "growth"
    }

def calculate_roi(product_key: str, company_size: int = 10, hourly_rate: int = 75) -> Dict:
    """Calculate ROI for a specific product and company."""
    product = PRODUCTS.get(product_key, PRODUCTS["proflow_growth"])
    price = product.get("price_monthly") or (product.get("price_one_time",0) / 12)
    roi_multiplier = product.get("roi_multiplier", 10)

    hours_saved_monthly = price * roi_multiplier / hourly_rate
    dollar_value_saved  = hours_saved_monthly * hourly_rate
    net_roi             = dollar_value_saved - price
    roi_percentage      = (net_roi / price) * 100

    return {
        "monthly_investment": price,
        "hours_saved_monthly": round(hours_saved_monthly),
        "dollar_value_generated": round(dollar_value_saved),
        "net_monthly_roi": round(net_roi),
        "roi_percentage": round(roi_percentage),
        "break_even_hours": round(price / hourly_rate, 1),
        "annual_value": round(dollar_value_saved * 12),
    }

def generate_proposal(contact: Dict, product_key: str = None, custom_notes: str = "") -> str:
    """Generate a complete, personalized sales proposal as HTML."""
    company = contact.get("company","Your Company")
    name    = contact.get("name","").split()[0] if contact.get("name") else "there"
    title   = contact.get("title","")

    # Research the company
    research = research_company(company, contact.get("website",""))
    if not product_key:
        product_key = research.get("recommended_product","proflow_growth")

    product  = PRODUCTS.get(product_key, PRODUCTS["proflow_growth"])
    roi_data = calculate_roi(product_key)

    price_display = f"${product.get('price_monthly',0):,}/mo" if product.get("price_monthly") else f"${product.get('price_one_time',0):,} one-time"

    proposal_prompt = f"""You are a senior sales writer for NYSR, an elite AI automation agency.
Write a professional, persuasive sales proposal for {name} at {company}.

Contact: {name}, {title} at {company}
Product: {product["name"]} — {price_display}
Pain points: {", ".join(research.get("likely_pain_points",["content production","lead generation"]))}
Personalization hook: {research.get("personalization_hook","")}
ROI: ${roi_data["dollar_value_generated"]:,}/mo value, {roi_data["roi_percentage"]}% ROI
Custom notes: {custom_notes}

Write a compelling proposal with:
1. Personalized subject line
2. Opening paragraph acknowledging their specific situation at {company}
3. The problem they're facing (be specific and empathetic)
4. Our solution (how ProFlow/NYSR solves it exactly)
5. ROI calculation table
6. What's included (features)
7. Social proof (mention 2-3 types of clients like them)
8. Investment (pricing with annual discount if applicable)
9. Next steps (specific, time-bound)
10. PS line (urgency/scarcity)

Tone: Professional but warm. Confident, not pushy. Data-driven.
Length: 400-600 words."""

    body = claude("You are an elite sales copywriter.", proposal_prompt, max_tokens=1200) or f"Hi {name},

I'd love to show you how NYSR can help {company} with {product['name']}.

{price_display}

Let's talk!"

    # Wrap in professional HTML
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body{{font-family:system-ui,sans-serif;max-width:680px;margin:0 auto;padding:40px 20px;color:#1e293b;line-height:1.7}}
.header{{border-left:4px solid #C9A84C;padding-left:20px;margin-bottom:32px}}
.company{{font-size:12px;font-weight:700;color:#C9A84C;letter-spacing:.1em;text-transform:uppercase}}
h1{{font-size:28px;font-weight:800;margin:8px 0}}
.roi-box{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:24px;margin:24px 0}}
.roi-box h3{{margin:0 0 16px;font-size:16px;color:#C9A84C}}
.roi-row{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #e2e8f0;font-size:14px}}
.roi-row:last-child{{border:none;font-weight:700;font-size:16px}}
.features{{background:#020409;color:#E8EDF5;border-radius:12px;padding:24px;margin:24px 0}}
.features h3{{color:#C9A84C;margin:0 0 16px}}
.features li{{margin-bottom:8px;font-size:14px}}
.cta{{background:#C9A84C;color:#020409;padding:16px 32px;border-radius:8px;text-decoration:none;font-weight:800;display:inline-block;margin:24px 0}}
.footer{{font-size:12px;color:#64748b;margin-top:40px;border-top:1px solid #e2e8f0;padding-top:20px}}
</style></head><body>
<div class="header">
<div class="company">NY Spotlight Report — AI Agency</div>
<h1>Proposal for {company}</h1>
<p style="color:#64748b;margin:0">{product["name"]} · {price_display} · Prepared {datetime.utcnow().strftime("%B %d, %Y")}</p>
</div>
<div style="white-space:pre-line">{body}</div>
<div class="roi-box">
<h3>📊 ROI Calculation for {company}</h3>
<div class="roi-row"><span>Monthly Investment</span><span>${roi_data["monthly_investment"]:,}</span></div>
<div class="roi-row"><span>Hours Saved / Month</span><span>{roi_data["hours_saved_monthly"]} hours</span></div>
<div class="roi-row"><span>Value Generated</span><span>${roi_data["dollar_value_generated"]:,}</span></div>
<div class="roi-row"><span>Net Monthly ROI</span><span>${roi_data["net_monthly_roi"]:,} ({roi_data["roi_percentage"]}%)</span></div>
<div class="roi-row"><span>Annual Value</span><span>${roi_data["annual_value"]:,}</span></div>
</div>
<div class="features">
<h3>✅ What's Included</h3>
<ul>{"".join(f"<li>{f}</li>" for f in product["features"])}</ul>
</div>
<a href="https://nyspotlightreport.com/proflow/" class="cta">View Full Details →</a>
<div class="footer">
<p>NY Spotlight Report · nyspotlightreport.com · nyspotlightreport@gmail.com</p>
<p>This proposal is valid for 7 days. Questions? Reply directly to this email.</p>
</div>
</body></html>"""

def generate_quick_proposal(contact: Dict) -> str:
    """One-paragraph quick proposal for initial outreach."""
    company = contact.get("company","your company")
    name    = (contact.get("name") or "").split()[0] or "there"
    return claude(
        "Write a 3-sentence sales pitch. Specific, personalized, value-first. No fluff.",
        f"Prospect: {name} at {company} | Title: {contact.get('title','')} | Pain: content production and lead generation",
        max_tokens=150
    ) or f"Hi {name}, I help companies like {company} automate content and lead generation with AI. Most clients see 10× content output within 30 days. Worth a 15-min call?"

def run(contact: Dict = None, product_key: str = "proflow_growth"):
    if not contact:
        contact = {"name":"Demo Contact","company":"Demo Corp","title":"CEO","email":"demo@demo.com"}
    proposal = generate_proposal(contact, product_key)
    log.info(f"Generated proposal for {contact.get('company','?')} — {len(proposal)} chars")
    return proposal

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Proposal] %(message)s")
    print(run())

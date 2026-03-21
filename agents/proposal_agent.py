#!/usr/bin/env python3
"""
Proposal Agent — NYSR Auto-Proposal Generator
Creates custom, compelling sales proposals based on contact data and deal context.
Generates HTML + PDF-ready proposals with NYSR branding.

Proposal sections:
  1. Executive Summary (personalized pain + solution)
  2. About NYSR (social proof, credibility)
  3. Solution Overview (tailored to their specific needs)
  4. Investment & Pricing (clear tiers, value framing)
  5. Timeline & Deliverables
  6. ROI Calculator (their numbers, our solution)
  7. Next Steps (clear CTA with Stripe link)
  8. Terms & Conditions (brief)
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
    from agents.crm_core_agent import supabase_request, ICPS
except Exception as e:
    print(f"Import partial: {e}")
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def supabase_request(m,t,**k): return None

log = logging.getLogger(__name__)

STRIPE_LINKS = {
    "proflow_starter":  "https://buy.stripe.com/proflow_starter",
    "proflow_growth":   "https://buy.stripe.com/proflow_growth",
    "dfy_essential":    "https://buy.stripe.com/dfy_essential",
    "dfy_agency":       "https://buy.stripe.com/dfy_agency",
    "lead_gen_starter": "https://buy.stripe.com/lead_gen_starter",
}

PACKAGES = {
    "proflow_starter": {
        "name": "ProFlow AI Starter",
        "price": 97,
        "billing": "monthly",
        "headline": "AI-Powered Content Engine",
        "features": [
            "Automated blog + SEO articles (10/month)",
            "Social media content across 5 platforms",
            "Email newsletter automation",
            "Keyword research & optimization",
            "24/7 content publishing bot",
            "Monthly performance report",
        ],
        "guarantee": "30-day money-back guarantee",
        "setup_time": "48 hours",
    },
    "proflow_growth": {
        "name": "ProFlow AI Growth",
        "price": 297,
        "billing": "monthly",
        "headline": "Full-Stack AI Marketing System",
        "features": [
            "Everything in Starter",
            "Unlimited content generation",
            "Lead generation automation (200 leads/day)",
            "Custom AI agents for your workflow",
            "HubSpot CRM integration",
            "Weekly strategy call",
            "Priority support",
        ],
        "guarantee": "30-day money-back guarantee",
        "setup_time": "72 hours",
    },
    "dfy_essential": {
        "name": "DFY Bot Setup — Essential",
        "price": 1497,
        "billing": "one-time",
        "headline": "Done-For-You AI Automation System",
        "features": [
            "Full system audit & strategy session",
            "5 custom AI bots built for your workflow",
            "Automated lead generation pipeline",
            "Content creation automation",
            "30-day post-launch support",
            "Training & documentation",
        ],
        "guarantee": "100% satisfaction guarantee",
        "setup_time": "5-7 business days",
    },
    "dfy_agency": {
        "name": "DFY Agency Automation — Complete",
        "price": 4997,
        "billing": "one-time",
        "headline": "Complete AI Agency Operating System",
        "features": [
            "Everything in DFY Essential",
            "20+ custom AI agents and bots",
            "Full sales automation (outreach → close)",
            "Client reporting automation",
            "Multi-platform content engine",
            "Passive income streams setup (5+)",
            "60-day post-launch support",
            "Direct access to senior engineer",
        ],
        "guarantee": "100% satisfaction guarantee",
        "setup_time": "10-14 business days",
    },
}

def generate_proposal(contact: dict, package_key: str = "dfy_essential") -> str:
    """Generate a full HTML proposal personalized to the contact."""
    package = PACKAGES.get(package_key, PACKAGES["dfy_essential"])
    contact_name  = contact.get("name","")
    company       = contact.get("company","")
    industry      = contact.get("industry","your industry")
    title         = contact.get("title","")
    first_name    = contact_name.split()[0] if contact_name else "there"

    # AI-generate the personalized executive summary
    exec_summary = claude(
        "You are a senior sales consultant. Write a 2-paragraph personalized executive summary for a sales proposal.",
        f"""Contact: {contact_name} | {title} at {company} | Industry: {industry}
Package: {package["name"]} — {package["headline"]}
Pain points this solves: manual processes, slow content production, scaling challenges.
Write 2 paragraphs: (1) Acknowledge their specific situation/challenge. (2) How our solution solves it specifically for them.
Be specific to their company/industry. Sound like you've done research.""",
        max_tokens=300
    ) or f"Based on your work at {company}, we understand the challenges of scaling {industry} operations efficiently. The demands on your team continue to grow while the pressure to deliver results remains constant.

Our {package['headline']} is designed specifically for businesses like {company} — giving you enterprise-grade AI automation without the enterprise price tag or the technical overhead."

    # ROI calculation
    employees = contact.get("employees") or 5
    if isinstance(employees, str):
        try: employees = int(employees.replace(",","").split("-")[0])
        except: employees = 5
    hours_saved_per_month = employees * 4
    hourly_rate           = 50
    monthly_value_created = hours_saved_per_month * hourly_rate
    roi_multiple          = round(monthly_value_created / max(package["price"], 1), 1)

    valid_until = (datetime.utcnow() + timedelta(days=7)).strftime("%B %d, %Y")
    features_html = "".join([f'<li>{f}</li>' for f in package["features"]])
    stripe_url    = STRIPE_LINKS.get(package_key, "https://nyspotlightreport.com/pricing/")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Proposal for {company} — NYSR</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#F8F9FB;color:#1A1E2E;line-height:1.6;}}
.doc{{max-width:800px;margin:0 auto;background:#fff;box-shadow:0 4px 40px rgba(0,0,0,.08);}}
.hero{{background:linear-gradient(135deg,#060910,#0A1428);color:#fff;padding:60px 60px 40px;position:relative;overflow:hidden;}}
.hero::before{{content:"";position:absolute;top:-50%;right:-20%;width:600px;height:600px;border-radius:50%;background:rgba(201,168,76,.05);}}
.hero-tag{{font-size:11px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#C9A84C;margin-bottom:16px;font-family:monospace;}}
.hero h1{{font-size:36px;font-weight:800;line-height:1.2;margin-bottom:12px;}}
.hero-sub{{font-size:16px;color:rgba(255,255,255,.65);margin-bottom:30px;}}
.hero-meta{{display:flex;gap:24px;font-size:13px;color:rgba(255,255,255,.5);padding-top:20px;border-top:1px solid rgba(255,255,255,.1);}}
.section{{padding:40px 60px;border-bottom:1px solid #F0F2F5;}}
.section-tag{{font-size:10px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#C9A84C;margin-bottom:12px;font-family:monospace;}}
h2{{font-size:24px;font-weight:700;color:#060910;margin-bottom:16px;}}
h3{{font-size:16px;font-weight:700;color:#060910;margin-bottom:8px;}}
p{{margin-bottom:16px;font-size:15px;line-height:1.7;color:#3D4557;}}
.feature-list{{list-style:none;}}
.feature-list li{{padding:10px 0;border-bottom:1px solid #F5F6FA;font-size:15px;display:flex;align-items:center;gap:10px;}}
.feature-list li::before{{content:"✓";color:#C9A84C;font-weight:700;font-size:14px;}}
.roi-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:24px 0;}}
.roi-card{{background:#F8F9FB;border-radius:12px;padding:20px;text-align:center;}}
.roi-num{{font-size:28px;font-weight:800;color:#060910;}}
.roi-lbl{{font-size:12px;color:#6B7280;margin-top:4px;}}
.price-box{{background:linear-gradient(135deg,#060910,#0A1428);color:#fff;border-radius:16px;padding:32px;text-align:center;margin:24px 0;}}
.price-amount{{font-size:48px;font-weight:900;color:#C9A84C;}}
.price-period{{font-size:16px;color:rgba(255,255,255,.5);}}
.cta-btn{{display:block;background:linear-gradient(90deg,#C9A84C,#D4A64E);color:#060910;text-align:center;padding:18px 32px;border-radius:12px;font-size:16px;font-weight:800;text-decoration:none;margin:24px 0;letter-spacing:.03em;}}
.guarantee{{background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;padding:16px 20px;font-size:14px;color:#166534;display:flex;align-items:center;gap:10px;}}
.timeline{{display:flex;gap:0;margin:20px 0;}}
.timeline-step{{flex:1;text-align:center;position:relative;}}
.timeline-step::after{{content:"";position:absolute;top:20px;left:50%;width:100%;height:2px;background:#E5E7EB;z-index:0;}}
.timeline-step:last-child::after{{display:none;}}
.step-dot{{width:40px;height:40px;border-radius:50%;background:#060910;color:#C9A84C;font-weight:800;display:flex;align-items:center;justify-content:center;margin:0 auto 8px;position:relative;z-index:1;font-size:14px;}}
.step-label{{font-size:12px;font-weight:600;}}
.step-sub{{font-size:11px;color:#6B7280;}}
.footer{{background:#060910;color:rgba(255,255,255,.5);padding:30px 60px;font-size:13px;text-align:center;}}
.footer a{{color:#C9A84C;text-decoration:none;}}
@media print{{body{{background:#fff;}}.doc{{box-shadow:none;}}}}
</style>
</head>
<body>
<div class="doc">

<div class="hero">
  <div class="hero-tag">Confidential Proposal</div>
  <h1>AI Automation Proposal<br>for {company}</h1>
  <div class="hero-sub">Prepared for {contact_name} | {title}</div>
  <div class="hero-meta">
    <span>📅 Prepared: {datetime.utcnow().strftime("%B %d, %Y")}</span>
    <span>⏰ Valid until: {valid_until}</span>
    <span>🏢 NY Spotlight Report</span>
  </div>
</div>

<div class="section">
  <div class="section-tag">Executive Summary</div>
  <h2>Why This Is Built for {company}</h2>
  <p>{exec_summary.replace(chr(10), "</p><p>")}</p>
</div>

<div class="section">
  <div class="section-tag">The Solution</div>
  <h2>{package["headline"]}</h2>
  <h3>{package["name"]}</h3>
  <ul class="feature-list">
    {features_html}
  </ul>
  <p style="margin-top:20px"><strong>Setup timeline:</strong> {package["setup_time"]} from contract signing to full deployment.</p>
</div>

<div class="section">
  <div class="section-tag">ROI Analysis</div>
  <h2>Your Investment Return</h2>
  <p>Based on a team of {employees} people at {company}:</p>
  <div class="roi-grid">
    <div class="roi-card"><div class="roi-num">{hours_saved_per_month}h</div><div class="roi-lbl">Hours saved monthly</div></div>
    <div class="roi-card"><div class="roi-num">${monthly_value_created:,}</div><div class="roi-lbl">Monthly value created</div></div>
    <div class="roi-card"><div class="roi-num">{roi_multiple}×</div><div class="roi-lbl">ROI multiple</div></div>
  </div>
  <p>At <strong>${package["price"]:,}/{package["billing"]}</strong>, you get {roi_multiple}× return on your investment every single month.</p>
</div>

<div class="section">
  <div class="section-tag">Investment</div>
  <h2>Simple, Transparent Pricing</h2>
  <div class="price-box">
    <div class="price-amount">${package["price"]:,}</div>
    <div class="price-period">/{package["billing"]}</div>
    <p style="color:rgba(255,255,255,.6);font-size:14px;margin-top:8px;margin-bottom:0">
      {package["guarantee"]} · No hidden fees · Cancel anytime
    </p>
  </div>
  <div class="guarantee">
    <span>🛡️</span>
    <span><strong>{package["guarantee"]}.</strong> If you're not 100% satisfied with the results in the first {30 if "monthly" in package["billing"] else 14} days, we'll refund every dollar. No questions asked.</span>
  </div>
</div>

<div class="section">
  <div class="section-tag">Timeline</div>
  <h2>How We Get You Live Fast</h2>
  <div class="timeline">
    <div class="timeline-step"><div class="step-dot">1</div><div class="step-label">Day 1</div><div class="step-sub">Strategy call</div></div>
    <div class="timeline-step"><div class="step-dot">2</div><div class="step-label">Day 2-3</div><div class="step-sub">Build & configure</div></div>
    <div class="timeline-step"><div class="step-dot">3</div><div class="step-label">Day 4-5</div><div class="step-sub">Testing & QA</div></div>
    <div class="timeline-step"><div class="step-dot">4</div><div class="step-label">Day {package["setup_time"].split("-")[0].replace(" business days","").replace(" hours","")}</div><div class="step-sub">Full launch</div></div>
  </div>
</div>

<div class="section">
  <div class="section-tag">Next Steps</div>
  <h2>Ready to Move Forward?</h2>
  <p>This proposal is valid until <strong>{valid_until}</strong>. To secure your spot and lock in this pricing:</p>
  <a href="{stripe_url}" class="cta-btn">Accept Proposal & Get Started →</a>
  <p style="text-align:center;font-size:13px;color:#6B7280">Or reply to schedule a 15-minute walkthrough call</p>
</div>

<div class="footer">
  <p>NY Spotlight Report — AI Automation Agency · <a href="https://nyspotlightreport.com">nyspotlightreport.com</a></p>
  <p style="margin-top:8px">Prepared by Sean Thomas, Founder · seanb041992@gmail.com</p>
</div>

</div>
</body>
</html>"""
    return html

def save_proposal(contact_id: str, package_key: str, html: str) -> str:
    """Save proposal to Supabase and return proposal ID."""
    result = supabase_request("POST", "proposals", {
        "contact_id":    contact_id,
        "package":       package_key,
        "html_content":  html[:50000],  # truncate for storage
        "status":        "sent",
        "created_at":    datetime.utcnow().isoformat(),
        "expires_at":    (datetime.utcnow() + timedelta(days=7)).isoformat(),
    })
    return result[0]["id"] if result and isinstance(result, list) and result[0].get("id") else ""

def run():
    """Generate proposals for all QUALIFIED leads."""
    log.info("Proposal Agent: generating proposals for qualified leads...")

    contacts = supabase_request("GET", "contacts",
        query="?stage=in.(QUALIFIED,PROPOSAL)&order=score.desc&limit=20"
    ) or []

    generated = 0
    for contact in contacts:
        icp = contact.get("icp","dfy_agency")
        pkg = "proflow_starter" if icp == "proflow_ai" else "dfy_agency" if contact.get("score",0)>=75 else "dfy_essential"
        html = generate_proposal(contact, pkg)
        if contact.get("id"):
            save_proposal(contact["id"], pkg, html)
        generated += 1
        log.info(f"  Proposal: {contact.get('name','')} @ {contact.get('company','')} — {pkg}")

    log.info(f"Generated {generated} proposals")
    return {"proposals_generated": generated}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Proposal] %(message)s")
    run()

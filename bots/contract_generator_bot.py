#!/usr/bin/env python3
"""
Contract Generator Bot — Auto-generates service contracts for NYSR packages.
Creates legally sound, NY-jurisdiction contracts with:
  - Clear scope of work
  - Payment terms (Net 15)
  - IP/ownership clauses
  - Termination provisions
  - Dispute resolution (NY courts)
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude
    from agents.crm_core_agent import supabase_request
except:
    def claude(s,u,**k): return ""
    def supabase_request(m,t,**k): return None

log = logging.getLogger(__name__)

CONTRACT_TEMPLATES = {
    "monthly_saas": {
        "name": "SaaS Subscription Agreement",
        "payment_terms": "billed monthly, auto-renews",
        "notice_period": "30 days written notice to cancel",
        "ip_ownership": "Client owns all content generated. NYSR retains system IP.",
    },
    "one_time_dfy": {
        "name": "Done-For-You Services Agreement",
        "payment_terms": "50% upfront, 50% on delivery",
        "notice_period": "Non-refundable after work begins",
        "ip_ownership": "Client owns all deliverables upon full payment.",
    },
}

def generate_contract(client_name: str, client_company: str, client_email: str,
                      package_name: str, package_price: float, billing: str,
                      scope_items: list = None) -> str:
    """Generate a full service contract as HTML."""
    today = datetime.utcnow().strftime("%B %d, %Y")
    template_key = "monthly_saas" if billing == "monthly" else "one_time_dfy"
    template = CONTRACT_TEMPLATES[template_key]

    scope_list = scope_items or [
        "AI automation system setup and configuration",
        "Bot deployment and integration",
        "Training and documentation",
        "30-day post-launch support",
    ]
    scope_html = "".join([f"<li>{item}</li>" for item in scope_list])

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Service Agreement — {client_company} × NYSR</title>
<style>
body{{font-family:Georgia,serif;max-width:750px;margin:40px auto;color:#1a1a1a;line-height:1.7;padding:40px;}}
h1{{font-size:24px;text-align:center;border-bottom:2px solid #000;padding-bottom:16px;margin-bottom:24px;}}
h2{{font-size:16px;font-weight:700;margin:24px 0 8px;text-transform:uppercase;letter-spacing:.08em;}}
p{{margin:0 0 12px;font-size:14px;}}
.parties{{background:#f9f9f9;border:1px solid #ddd;padding:20px;border-radius:4px;margin:20px 0;}}
.sig-block{{display:grid;grid-template-columns:1fr 1fr;gap:40px;margin-top:60px;}}
.sig-line{{border-top:1px solid #000;padding-top:8px;font-size:13px;}}
ul{{font-size:14px;line-height:2;}}
.amount{{font-size:18px;font-weight:700;}}
</style>
</head>
<body>
<h1>SERVICE AGREEMENT</h1>

<div class="parties">
<p><strong>Agreement Date:</strong> {today}</p>
<p><strong>Service Provider:</strong> NY Spotlight Report (Sean Thomas), Coram, NY 11727 | seanb041992@gmail.com</p>
<p><strong>Client:</strong> {client_name}, {client_company} | {client_email}</p>
</div>

<h2>1. Services</h2>
<p>Service Provider agrees to deliver the following under the <strong>{package_name}</strong> package:</p>
<ul>{scope_html}</ul>

<h2>2. Compensation</h2>
<p>Client agrees to pay: <span class="amount">${package_price:,.2f}</span> ({billing}).</p>
<p>Payment terms: {template["payment_terms"]}. Late payments incur 1.5% monthly interest after Net 15.</p>
<p>Payment processed via Stripe. Client authorizes recurring charges if applicable.</p>

<h2>3. Term & Termination</h2>
<p>This Agreement begins on the date signed and continues until terminated. {template["notice_period"]}.</p>
<p>Either party may terminate for material breach with 14 days written notice and opportunity to cure.</p>

<h2>4. Intellectual Property</h2>
<p>{template["ip_ownership"]} Client grants NYSR a limited license to use client materials solely for service delivery.</p>

<h2>5. Confidentiality</h2>
<p>Both parties agree to keep confidential all non-public information disclosed during this engagement for 3 years post-termination.</p>

<h2>6. Limitation of Liability</h2>
<p>NYSR's total liability is limited to fees paid in the prior 30 days. Neither party liable for indirect, incidental, or consequential damages.</p>

<h2>7. Warranties & Disclaimers</h2>
<p>NYSR warrants services will be performed professionally. NO WARRANTY of specific revenue results. AI-generated content requires client review before publishing.</p>

<h2>8. Governing Law</h2>
<p>This Agreement is governed by the laws of the State of New York. Disputes resolved in Suffolk County, NY courts.</p>

<h2>9. Entire Agreement</h2>
<p>This constitutes the entire agreement between the parties and supersedes all prior discussions.</p>

<div class="sig-block">
  <div>
    <div class="sig-line">Signature: _______________________</div>
    <p>Sean Thomas<br>NY Spotlight Report<br>Date: _______________</p>
  </div>
  <div>
    <div class="sig-line">Signature: _______________________</div>
    <p>{client_name}<br>{client_company}<br>Date: _______________</p>
  </div>
</div>

</body></html>"""

def run():
    log.info("Contract Generator Bot — test run")
    contract = generate_contract(
        "John Smith", "TestCo Inc.", "john@testco.com",
        "DFY Bot Setup", 1497, "one-time",
        ["Custom AI system build", "5 automation bots", "30-day support"]
    )
    log.info(f"Contract generated: {len(contract)} chars")
    return {"status": "ready", "contract_length": len(contract)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [Contract] %(message)s")
    run()

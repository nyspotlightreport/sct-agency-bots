#!/usr/bin/env python3
"""
Contract Generator Agent — Auto-generates sales agreements, SOWs, and NDAs
Production-ready legal templates for every deal type.
"""
import os, sys, json, logging
from datetime import datetime, timedelta
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except:
    def claude(s,u,**k): return ""

log = logging.getLogger(__name__)

def generate_saas_agreement(contact: Dict, product: str, price: float, billing: str = "monthly") -> str:
    today      = datetime.utcnow().strftime("%B %d, %Y")
    start_date = (datetime.utcnow() + timedelta(days=3)).strftime("%B %d, %Y")
    return f"""SUBSCRIPTION SERVICES AGREEMENT

Effective Date: {today}
Start Date: {start_date}

PARTIES
Provider: NY Spotlight Report ("NYSR"), Coram, NY 11727
Client: {contact.get("company","Client Company")} ("{contact.get("company","Client").split()[0]}")

1. SERVICES
NYSR will provide access to {product} software-as-a-service platform as described 
at nyspotlightreport.com/proflow/. Service includes all features listed in the 
selected plan tier as of the Effective Date.

2. PAYMENT TERMS
Subscription Fee: ${price:,.2f} per {"month" if billing=="monthly" else "year"}
Billing: Automatic charge to payment method on file
Due: {"1st of each month" if billing=="monthly" else "Annual, on anniversary date"}
Late Payment: 1.5% monthly interest on overdue amounts

3. TERM & TERMINATION
Initial Term: 30 days from Start Date
Renewal: Automatically renews monthly/annually unless cancelled
Cancellation: 30 days written notice via email to nyspotlightreport@gmail.com
No refunds for partial periods.

4. INTELLECTUAL PROPERTY
Client retains ownership of all content produced using the Service.
NYSR retains all rights to the platform, algorithms, and underlying technology.
Client grants NYSR right to use company name in anonymized case studies.

5. CONFIDENTIALITY
Both parties agree to keep proprietary information confidential for 2 years post-termination.

6. WARRANTIES & LIABILITY
NYSR warrants 99.5% uptime (excluding scheduled maintenance).
TOTAL LIABILITY CAPPED AT 1 MONTH'S SUBSCRIPTION FEE.
NO LIABILITY FOR INDIRECT, CONSEQUENTIAL, OR PUNITIVE DAMAGES.

7. GOVERNING LAW
This Agreement is governed by the laws of New York State.
Disputes resolved by binding arbitration in Suffolk County, NY.

SIGNATURES

NYSR: _________________________ Date: {today}
S.C. Thomas, Chairman

Client: _________________________ Date: _______________
{contact.get("name","Authorized Signatory")}, {contact.get("title","")}
{contact.get("company","")}

"""

def generate_dfy_sow(contact: Dict, scope: List[str], price: float, timeline_weeks: int = 4) -> str:
    today     = datetime.utcnow().strftime("%B %d, %Y")
    end_date  = (datetime.utcnow() + timedelta(weeks=timeline_weeks)).strftime("%B %d, %Y")
    scope_str = "
".join([f"  {i+1}. {item}" for i,item in enumerate(scope)])
    return f"""STATEMENT OF WORK (SOW)

Date: {today}
Project: AI Automation System Build — Done-For-You

PARTIES
Provider: NY Spotlight Report (NYSR)
Client: {contact.get("company","Client")} ({contact.get("name","")}, {contact.get("title","")})

1. PROJECT SCOPE
NYSR will design, build, and deploy the following:
{scope_str}

2. DELIVERABLES
All components deployed to Client's GitHub repository and Netlify hosting.
Complete documentation and video walkthrough provided.
Source code: Client's property upon final payment.

3. TIMELINE
Project Start: Upon receipt of 50% deposit
Estimated Completion: {end_date} ({timeline_weeks} weeks)
Final Delivery: Within 48 hours of final payment

4. INVESTMENT
Total Project Fee: ${price:,.2f}
Payment Schedule:
  - 50% deposit (${price/2:,.2f}) due before work begins
  - 50% balance (${price/2:,.2f}) due upon delivery

5. REVISIONS
Includes 2 rounds of revisions within 30 days of delivery.
Additional revisions billed at $150/hour.

6. SUPPORT
30-day post-delivery support included (bugs and setup issues only).
Ongoing support available via NYSR monthly retainer.

7. CHANGE ORDERS
Any scope changes require written approval and may affect timeline/price.

8. CONFIDENTIALITY
NYSR will not share Client's systems, data, or business logic with third parties.

CLIENT APPROVAL:
Signature: ___________________ Date: _______________
{contact.get("name","Authorized Signatory")}
{contact.get("company","")}

NYSR APPROVAL:
Signature: ___________________ Date: {today}
S.C. Thomas, Chairman, NY Spotlight Report
"""

def generate_nda(contact: Dict) -> str:
    today = datetime.utcnow().strftime("%B %d, %Y")
    return f"""MUTUAL NON-DISCLOSURE AGREEMENT

Date: {today}
Between: NY Spotlight Report ("NYSR") and {contact.get("company","Recipient")}

1. CONFIDENTIAL INFORMATION includes any non-public business, technical, 
   financial, or strategic information shared between parties.

2. OBLIGATIONS: Each party will (a) hold confidential information in strict 
   confidence; (b) not disclose to third parties without prior written consent; 
   (c) use only for evaluating a potential business relationship.

3. TERM: 2 years from the date of this Agreement.

4. EXCLUSIONS: Information that is publicly known, already known to recipient, 
   independently developed, or required to be disclosed by law.

5. GOVERNING LAW: New York State

NYSR: S.C. Thomas, Chairman         Date: {today}
{contact.get("company","")}: {contact.get("name","")}    Date: _______________
"""

def run(contact: Dict = None, contract_type: str = "saas"):
    if not contact:
        contact = {"name":"John Smith","company":"Acme Corp","title":"CEO"}
    if contract_type == "saas":
        return generate_saas_agreement(contact, "ProFlow Growth", 297)
    elif contract_type == "dfy":
        return generate_dfy_sow(contact, ["Custom bot system","CRM integration","10 workflows"], 4997, 4)
    return generate_nda(contact)

if __name__ == "__main__":
    import sys
    contact = {"name":"Jane Doe","company":"StartupCo","title":"Founder"}
    print(run(contact, sys.argv[1] if len(sys.argv)>1 else "saas"))

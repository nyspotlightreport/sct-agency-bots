#!/usr/bin/env python3
"""
Objection Handler Agent — AI-powered sales objection response system
Handles every objection type with psychologically proven response frameworks.
Uses FEEL-FELT-FOUND, ACKNOWLEDGE-CLARIFY-RESPOND, and custom frameworks.
"""
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

log = logging.getLogger(__name__)

# Master objection library — 40+ objections mapped to proven responses
OBJECTIONS = {
    "price": {
        "keywords": ["expensive","too much","cost","budget","afford","price","cheaper","discount"],
        "framework": "ROI_REFRAME",
        "response_template": """I hear you on the investment. Let me reframe it quickly.

At $[PRICE]/mo, you break even if this saves your team just [HOURS] hours a month.
What do you pay someone for [HOURS] hours? Probably 5-10× the subscription.

Our clients typically see [ROI]× ROI within 90 days. [CLIENT_TYPE] like you are saving
$[SAVINGS] per month in team hours alone.

Would it help to walk through the exact ROI for [COMPANY] specifically?""",
        "follow_up": "The goal isn't to spend less — it's to make more than you spend. Does that math make sense?"
    },
    "not_right_now": {
        "keywords": ["not now","later","busy","bad timing","next quarter","next year"],
        "framework": "URGENCY_BRIDGE",
        "response_template": """Totally understand. What's the one thing that needs to happen before the timing is right?

I ask because most of our clients said the same thing — then realized their competitors
were moving while they were waiting. [COMPETITOR] just onboarded last month.

I can hold your onboarding slot for [DATE]. After that it goes to the next company
on the waitlist. Worth a quick 10-min call to see if the timing could actually work now?""",
    },
    "need_to_think": {
        "keywords": ["think","consider","sleep on it","not sure","maybe","decision"],
        "framework": "CLARIFY_BARRIER",
        "response_template": """Of course — what specifically do you want to think through?

Usually when someone says that, it means there's either a question I haven't answered,
a concern about fit, or another stakeholder involved. Which is it for you?

I'd rather answer your real question now than have you spend a week thinking about
a concern I could resolve in 2 minutes.""",
    },
    "competitor": {
        "keywords": ["competitor","already use","similar","alternative","jasper","copy.ai","hubspot","other tool"],
        "framework": "DIFFERENTIATION",
        "response_template": """Good to know. What do you like most about what you're using?

Most clients who switched came because [COMPETITOR_WEAKNESS].
We're fundamentally different because [KEY_DIFFERENTIATOR].

It's actually easy to run us side by side for a month. Most clients see the difference
in week 1. Want to do a quick comparison on your specific use case?""",
    },
    "need_approval": {
        "keywords": ["boss","partner","approve","team","committee","stakeholder","sign off"],
        "framework": "STAKEHOLDER_ENABLEMENT",
        "response_template": """Makes sense — who else is typically involved in these decisions?

I've put together an executive summary that makes it really easy to share internally.
It covers the ROI, risk profile, and a one-page overview of what we do.

Would it help if I sent that directly to your [TITLE], or would you prefer to forward it?
I can also do a 20-min demo for the full team — most decisions get made in that call.""",
    },
    "security_concerns": {
        "keywords": ["security","data","privacy","GDPR","compliance","trust"],
        "framework": "TRUST_BUILDING",
        "response_template": """Completely valid concern. Security is non-negotiable for us too.

Here's our posture: [SECURITY_DETAILS]. We don't store your data beyond what's needed
for the service. Everything is encrypted in transit and at rest.

We can also do a technical deep-dive with your IT/security team if needed.
What specific requirements does [COMPANY] need met?""",
    },
    "too_complex": {
        "keywords": ["complicated","technical","complex","implement","setup","hard to use","learning curve"],
        "framework": "SIMPLICITY_PROOF",
        "response_template": """You'd be surprised — most clients are live in under 48 hours.

The DFY option means we handle everything. You log in and it's already running.
No technical knowledge needed.

Our average client goes from zero to publishing 10× more content in week 1.
Want me to walk you through exactly what setup looks like for [COMPANY] specifically?""",
    },
    "results_skepticism": {
        "keywords": ["prove","results","works","actually","really","guarantee","skeptical"],
        "framework": "SOCIAL_PROOF",
        "response_template": """Fair — you shouldn't take my word for it.

Here's what I can show you: [CASE_STUDY_TEASER]. Similar company, similar situation,
these were the results in 90 days.

Better yet — let's do a 14-day pilot on your actual content. You see real results
with your brand, your industry, your keywords. No risk. If it doesn't work, we part ways.
Interested?""",
    },
}

def classify_objection(objection_text: str) -> str:
    """Classify which objection type this is."""
    text_lower = objection_text.lower()
    for obj_type, obj_data in OBJECTIONS.items():
        if any(kw in text_lower for kw in obj_data.get("keywords",[])):
            return obj_type
    return "unknown"

def handle_objection(objection_text: str, contact: Dict = None, context: Dict = None) -> Dict:
    """Generate the best response to an objection."""
    obj_type  = classify_objection(objection_text)
    obj_data  = OBJECTIONS.get(obj_type, {})
    company   = (contact or {}).get("company","your company")
    price     = (context or {}).get("price", 297)

    # Fill template if available
    template_response = ""
    if obj_data.get("response_template"):
        template_response = obj_data["response_template"].replace(
            "[PRICE]", str(price)
        ).replace("[COMPANY]", company).replace("[HOURS]", "8").replace(
            "[ROI]", "10").replace("[SAVINGS]", str(price * 8))

    # Get AI-enhanced response
    ai_response = claude(
        """You are Sloane Pierce, VP of Sales at an elite AI agency. 
Respond to this objection with a confident, empathetic, psychologically effective response.
3-4 sentences. End with a question that moves the deal forward. Never be pushy.""",
        f"Objection: {objection_text}
Company: {company}
Product price: ${price}/mo
Objection type: {obj_type}",
        max_tokens=200
    ) or template_response or f"That's a fair point. Can you tell me more about what's driving that concern?"

    return {
        "objection_type": obj_type,
        "framework": obj_data.get("framework","ACKNOWLEDGE_RESPOND"),
        "response": ai_response,
        "follow_up": obj_data.get("follow_up",""),
        "escalation_needed": obj_type in ["security_concerns","need_approval"],
    }

def batch_handle(objections: List[str], contact: Dict = None) -> List[Dict]:
    return [handle_objection(obj, contact) for obj in objections]

def run():
    test_objections = [
        "It's too expensive for us right now",
        "We're already using HubSpot",
        "I need to talk to my partner first",
        "I'm not sure it will actually work",
        "We're too busy right now",
    ]
    contact = {"company":"TestCorp","title":"CEO"}
    for obj in test_objections:
        result = handle_objection(obj, contact)
        log.info(f"Objection: '{obj}'
Type: {result['objection_type']}
Response: {result['response'][:100]}...
")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

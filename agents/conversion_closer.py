# AG ENFORCEMENT GMAIL_ZERO 2026-03-28 Chairman auth granted
#!/usr/bin/env python3
"""
Conversion Closer — NYSR
The zero-friction path from interest to payment.

When triggered:
  • Lead opens email 3+ times → auto-send "saw you were looking" message
  • Lead clicks pricing page → trigger urgency sequence
  • Lead visits /proflow/ → start 48-hour close window
  • Lead replies to any email → instantly classify + respond
  • Lead books call → send prep doc + case studies + buy link
  • After call → same-day follow-up with custom proposal

The principle: no lead should ever have to wait more than 15 minutes
for a next step from us. Most businesses lose deals in the silence.
"""
import os,sys,json,logging,requests,base64,smtplib
from datetime import datetime,date,timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sys.path.insert(0,".")
try:
    from agents.claude_core import claude,claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

logging.basicConfig(level=logging.INFO,format="%(asctime)s [Closer] %(message)s")
log=logging.getLogger()
ANTHROPIC=os.environ.get("ANTHROPIC_API_KEY","")
# AG-HARD-DISABLED-GMAIL-ZERO: GMAIL_USER=os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")
# AG-HARD-DISABLED-GMAIL-ZERO: GMAIL_PASS=os.environ.get("GMAIL_APP_PASS","")
STRIPE=os.environ.get("STRIPE_SECRET_KEY","")
GH_TOKEN=os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
GH_H={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github+json"}
REPO="nyspotlightreport/sct-agency-bots"

CLOSER_SYSTEM="""You are Sloane Pierce, elite closer. You close deals. That's it.
You never over-explain. You never over-pitch.
You create momentum. You remove friction. You make yes easier than no.
Every message moves the deal forward or closes it.
Write like a human, not a sales bot."""

# PAYMENT LINKS — ready to drop into any message
PAYMENT_LINKS={
    "proflow_starter":  "https://buy.stripe.com/fZu3cv3Ra2vV0Ej8eX24005",
    "proflow_growth":   "https://buy.stripe.com/9B600j87q9Yn5YDeDl24006",
    "proflow_agency":   "https://buy.stripe.com/4gMdR987qeeD9aPgLt24007",
    "dfy_essential":    "https://buy.stripe.com/4gMdR9evO1rRev97aT24008",
    "dfy_growth":       "https://buy.stripe.com/dRmdR987q1rR0Ej66P24009",
    "lead_gen_starter": "https://buy.stripe.com/14AbJ11J2fiHev9dzh2400a",
    "lead_gen_growth":  "https://buy.stripe.com/28EfZh87q4E3gDhan52400b",
}

OBJECTION_LIBRARY={
    "too_expensive":[
        "What's your current content cost per month? I ask because most people I talk to realize $97 is cheaper than what they're already paying.",
        "Completely get it. Want me to show you the ROI math for your specific situation? Takes 2 minutes.",
        "Fair. What would it need to cost to be a no-brainer? I want to understand your budget range."
    ],
    "not_sure_it_works":[
        "That's the right concern. Want to see 3 months of our own data? Open to sharing everything.",
        "I can send you a sample — actual output from the system. Judge the quality yourself.",
        "What would you need to see to believe it? Tell me and I'll either show it or tell you honestly if I can't."
    ],
    "need_to_think":[
        "Of course. What's the main thing you're weighing? I can probably help you think through it faster.",
        "Totally. What's the one thing that would make this a yes vs a maybe?",
        "Makes sense. I'll follow up Friday. If it's not right for you, just say so — no hard feelings at all."
    ],
    "already_have_tools":[
        "What are you using? I ask because we often work alongside existing tools — might not be either/or.",
        "Good. What's the one thing your current setup can't do that you wish it could?",
        "Makes sense to stick with what's working. What would make you consider switching?"
    ],
    "bad_timing":[
        "Understood. When would be better — after Q1, after your launch, or when you're next evaluating tools?",
        "I'll reach back out then. Quick question before I go: what triggered you to open this email today?",
        "No problem at all. I'll put you on the list for our Q2 cohort — limited spots, I'll make sure you get first look."
    ],
    "send_me_info":[
        "Sending now. What's the one thing you'd most want to see?",
        "On it. And when you look it over — what would make you want to jump on a call vs pass?",
        "Will do. What's a better time to follow up — Thursday or Monday?"
    ]
}

def classify_reply(reply_text:str)->dict:
    """Classify an inbound reply and determine the best response strategy."""
    if not ANTHROPIC:
        return {"intent":"interested","objection":None,"urgency":"medium","recommended_action":"follow_up"}
    return claude_json(CLOSER_SYSTEM,
        f"""Classify this sales reply: "{reply_text[:300]}"
Return JSON: {{
  "intent": "interested|objecting|buying_signal|not_interested|referral|question",
  "objection": "too_expensive|not_sure_it_works|need_to_think|already_have_tools|bad_timing|send_me_info|none",
  "urgency": "hot|warm|cold",
  "emotional_state": "excited|skeptical|neutral|annoyed|curious",
  "recommended_action": "send_payment_link|book_call|send_case_study|handle_objection|follow_up|close_out",
  "confidence": 0-100
}}""",max_tokens=150) or {}

def generate_close_response(prospect:dict, reply_text:str, classification:dict)->str:
    """Generate the perfect response to close or advance the deal."""
    intent=classification.get("intent","interested")
    objection=classification.get("objection","none")
    action=classification.get("recommended_action","follow_up")
    
    name=prospect.get("first_name","")
    
    # Handle objections from library first (faster, proven)
    if objection and objection in OBJECTION_LIBRARY and objection!="none":
        import random
        return OBJECTION_LIBRARY[objection][0]
    
    # For buying signals — go straight to payment
    if intent=="buying_signal" or action=="send_payment_link":
        product=prospect.get("recommended_product","proflow_starter")
        link=PAYMENT_LINKS.get(product,PAYMENT_LINKS["proflow_starter"])
        if ANTHROPIC:
            return claude(CLOSER_SYSTEM,
                f"""Prospect {name} is ready to buy. Their message: "{reply_text[:200]}"
Write a 3-sentence response that confirms they're getting the right product,
includes the payment link: {link}
and makes it dead simple to proceed. No fluff.""",max_tokens=100) or f"Great, {name}! Here's your link: {link}"
        return f"Perfect timing, {name}. Here's your direct link: {link} — takes 2 minutes to get started."
    
    # For book_call
    if action=="book_call":
        return f"Let's do it, {name}. Book directly here: https://calendly.com/nyspotlightreport — 15 minutes, I'll show you the system live."
    
    # AI-generated response for complex situations
    if ANTHROPIC:
        return claude(CLOSER_SYSTEM,
            f"""Prospect: {name}
Their reply: "{reply_text[:300]}"
Intent: {intent} | Action needed: {action}
Write a tight, human response (under 80 words) that advances the deal.
Don't pitch. Move forward.""",max_tokens=120) or ""
    return ""

def send_response(to_email:str, subject:str, body:str)->bool:
# AG-HARD-DISABLED-GMAIL-ZERO:     if not GMAIL_PASS: return False
    try:
        msg=MIMEMultipart("alternative")
# AG-HARD-DISABLED-GMAIL-ZERO:         msg["From"]=f"S.C. Thomas <{GMAIL_USER}>"
        msg["To"]=to_email
        msg["Subject"]=subject
        msg.attach(MIMEText(body,"plain"))
# AG-GMAIL-ZERO-20260328: # AG-GMAIL-ZERO-ENFORCED-20260328: with smtplib.SMTP_SSL("[GMAIL-SMTP-REDACTED]",465) as s:
# AG-NUCLEAR-GMAIL-ZERO-20260328:             s.login(GMAIL_USER,GMAIL_PASS)
# AG-HARD-DISABLED-GMAIL-ZERO:             s.send_message(msg)
        return True
    except Exception as e:
        log.warning(f"Email send failed: {e}")
        return False

def check_inbox_for_replies()->list:
    """Check Gmail for replies to our outreach sequences."""
# AG-HARD-DISABLED-GMAIL-ZERO:     if not GMAIL_PASS: return []
    import imaplib,email as email_lib
    replies=[]
    try:
        mail=imaplib.IMAP4_SSL("imap.gmail.com")
# AG-NUCLEAR-GMAIL-ZERO-20260328:         mail.login(GMAIL_USER,GMAIL_PASS)
        mail.select("inbox")
        _,msgs=mail.search(None,"UNSEEN")
        for mid in msgs[0].split()[-10:]:
            _,data=mail.fetch(mid,"(RFC822)")
            msg=email_lib.message_from_bytes(data[0][1])
            subject=msg.get("Subject","")
            sender=msg.get("From","")
            body=""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type()=="text/plain":
                        body=part.get_payload(decode=True).decode("utf-8","ignore")[:400]
                        break
            else:
                body=msg.get_payload(decode=True).decode("utf-8","ignore")[:400]
            # Only process replies to our outreach (Re: or contains our keywords)
            if "Re:" in subject or any(k in body.lower() for k in ["proflow","dfy","content bot","automation","nysr"]):
                replies.append({"sender":sender,"subject":subject,"body":body,"msg_id":mid.decode()})
        mail.logout()
    except Exception as e:
        log.warning(f"Inbox check failed: {e}")
    return replies

def process_reply(reply:dict)->dict:
    """Classify a reply and generate + send the response."""
    classification=classify_reply(reply["body"])
    prospect={"first_name":reply["sender"].split()[0].replace('"',''),
              "recommended_product":"proflow_starter"}
    
    response=generate_close_response(prospect,reply["body"],classification)
    if response:
        subject=reply["subject"] if reply["subject"].startswith("Re:") else f"Re: {reply['subject']}"
        # Extract email from sender
        sender_email=reply["sender"]
        if "<" in sender_email:
            sender_email=sender_email.split("<")[1].rstrip(">")
        sent=send_response(sender_email,subject,response)
        log.info(f"  Reply processed: {classification.get('intent','?')} | Sent: {sent}")
        return {"processed":True,"intent":classification.get("intent"),"sent":sent,"response_preview":response[:80]}
    return {"processed":False}

def run():
    log.info("Conversion Closer starting...")
    replies=check_inbox_for_replies()
    log.info(f"  Replies found: {len(replies)}")
    results=[]
    for reply in replies:
        result=process_reply(reply)
        results.append(result)
        if result.get("sent"): time.sleep(2)  # Rate limit
    # Save results
    path="data/sales/closer_log.json"
    r=requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}",headers=GH_H)
    existing=[]
    if r.status_code==200:
        try: existing=json.loads(base64.b64decode(r.json()["content"]).decode())
        except Exception:  # noqa: bare-except

            pass
    existing.insert(0,{"date":str(date.today()),"replies_processed":len(results),"results":results[:10]})
    existing=existing[:30]
    enc=base64.b64encode(json.dumps(existing,indent=2).encode()).decode()
    body={"message":f"closer: {len(results)} replies processed","content":enc}
    if r.status_code==200: body["sha"]=r.json()["sha"]
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}",json=body,headers=GH_H)
    log.info(f"✅ Closer: {len([r for r in results if r.get('sent')])} responses sent")

import time
if __name__=="__main__": run()

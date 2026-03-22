"""
email_sequence_bot.py — Automated Outbound Email Sequence Engine
Runs timed nurture sequences for:
  - Media contacts (sponsorship outreach)
  - Newsletter subscribers (onboarding)
  - Lead prospects (HubSpot pipeline)
Runs: Daily 8am ET
Revenue: Newsletter sponsorships $500-5k/email | Consulting leads $1k-10k
"""
import os, json, urllib.request, datetime, time, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailSequenceBot:
    def __init__(self):
        self.gmail_user    = os.environ.get("GMAIL_USER","")
        self.gmail_pass    = os.environ.get("GMAIL_APP_PASS","")
        self.hubspot_key   = os.environ.get("HUBSPOT_API_KEY","")
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY","")

        # Email sequences definition
        self.sequences = {
            "sponsor_outreach": {
                "name": "Media Sponsor Outreach",
                "from_name": "Sean Thomas, NY Spotlight Report",
                "delays_days": [0, 3, 7, 14],
                "subjects": [
                    "Partnership opportunity — NY Spotlight Report (15k+ monthly readers)",
                    "Following up: NY Spotlight Report advertising",
                    "Last touch: media sponsorship opportunity",
                    "Quick question about {company}"
                ]
            },
            "newsletter_welcome": {
                "name": "New Subscriber Welcome",
                "from_name": "Sean Thomas, NY Spotlight Report",
                "delays_days": [0, 1, 3],
                "subjects": [
                    "Welcome to NY Spotlight Report 🎭",
                    "Your exclusive NYC entertainment guide",
                    "Behind the scenes of NY Spotlight Report"
                ]
            },
            "consulting_lead": {
                "name": "Media Consulting Lead Nurture",
                "from_name": "Sean Thomas",
                "delays_days": [0, 5, 10, 21],
                "subjects": [
                    "Quick thought about {company}'s media strategy",
                    "Case study: how we helped similar media brands",
                    "Free 15-min strategy call for {company}",
                    "Final thought on your media strategy"
                ]
            }
        }

    def get_hubspot_contacts_for_sequence(self, sequence_name, limit=10):
        """Pull contacts from HubSpot that need next sequence email"""
        if not self.hubspot_key:
            return []
        try:
            req = urllib.request.Request(
                "https://api.hubapi.com/crm/v3/objects/contacts?limit=50&properties=email,firstname,lastname,company,hs_lead_status,lifecyclestage",
                headers={"Authorization":f"Bearer {self.hubspot_key}"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            contacts = data.get("results",[])
            # Filter: only NEW contacts in prospecting
            eligible = [c for c in contacts if c.get("properties",{}).get("hs_lead_status") == "NEW"]
            return eligible[:limit]
        except Exception as e:
            print(f"HubSpot error: {e}")
            return []

    def generate_email_body(self, sequence_name, step, contact_data):
        """Generate personalized email for each sequence step"""
        first_name = contact_data.get("firstname","there")
        company    = contact_data.get("company","your company")
        seq        = self.sequences.get(sequence_name,{})

        if not self.anthropic_key:
            return self._fallback_email(sequence_name, step, first_name, company)

        prompts = {
            "sponsor_outreach_0": f"Write a cold outreach email to {first_name} at {company} about advertising/sponsoring NY Spotlight Report newsletter (15k+ readers, NYC entertainment). Be brief (3 paragraphs), value-first, no hype. From: Sean Thomas",
            "sponsor_outreach_1": f"Write a 2-paragraph follow-up email to {first_name} at {company} about NY Spotlight Report sponsorship. Reference previous email wasn't answered. Keep very short.",
            "newsletter_welcome_0": f"Write a warm welcome email to {first_name} who just subscribed to NY Spotlight Report. 3 short paragraphs. Mention what they'll get (daily NYC entertainment news), personal tone from Sean.",
            "consulting_lead_0": f"Write a brief, value-first cold email to {first_name} at {company} about media consulting for entertainment brands. From Sean Thomas. 3 paragraphs max. No fluff.",
        }

        key = f"{sequence_name}_{step}"
        prompt = prompts.get(key, f"Write a {sequence_name} step {step} email to {first_name} at {company} from Sean Thomas, NY Spotlight Report. Professional, brief, 3 paragraphs.")

        try:
            req_data = json.dumps({
                "model":"claude-haiku-4-5-20251001","max_tokens":400,
                "messages":[{"role":"user","content":prompt}]
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=req_data,
                headers={"x-api-key":self.anthropic_key,"anthropic-version":"2023-06-01","Content-Type":"application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                resp = json.loads(r.read())
                return resp.get("content",[{}])[0].get("text","")
        except Exception as e:
            print(f"Claude error: {e}")
            return self._fallback_email(sequence_name, step, first_name, company)

    def _fallback_email(self, sequence_name, step, first_name, company):
        templates = {
            "sponsor_outreach": f"""Hi {first_name},

I run NY Spotlight Report — New York's entertainment authority covering Broadway, film premieres, fashion, and celebrity news for 15,000+ monthly readers.

I wanted to reach out about potential advertising or sponsorship opportunities. Our audience is exactly who {company} wants to reach: entertainment professionals, media buyers, and affluent NYC culture enthusiasts.

Would you have 15 minutes to explore how we might work together?

Best,
Sean Thomas
Editor in Chief, NY Spotlight Report
nyspotlightreport.com""",
            "newsletter_welcome": f"""Welcome to NY Spotlight Report, {first_name}!

You're now part of an exclusive community of entertainment insiders and culture enthusiasts who rely on us for New York's best coverage.

Every morning, you'll get the stories that matter — Broadway openings, film premieres, fashion week coverage, and the celebrity news that actually matters.

This is New York. Let's make it count.

— Sean Thomas, Editor in Chief"""
        }
        return templates.get(sequence_name, f"Hi {first_name}, following up from NY Spotlight Report. — Sean Thomas")

    def send_email(self, to_email, subject, body, from_name="Sean Thomas, NY Spotlight Report"):
        """Send via Gmail"""
        if not self.gmail_user or not self.gmail_pass:
            print(f"⚠️ No Gmail creds — would send to {to_email}: {subject[:40]}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg['Subject'] = subject
            msg['From']    = f"{from_name} <{self.gmail_user}>"
            msg['To']      = to_email

            html_body = f"<html><body style='font-family:Georgia,serif;max-width:600px;'>{body.replace(chr(10),'<br>')}</body></html>"
            msg.attach(MIMEText(body,'plain'))
            msg.attach(MIMEText(html_body,'html'))

            with smtplib.SMTP_SSL('smtp.gmail.com',465) as server:
                server.login(self.gmail_user, self.gmail_pass)
                server.send_message(msg)
            print(f"✅ Sent to {to_email}: {subject[:40]}")
            return True
        except Exception as e:
            print(f"Email send error to {to_email}: {e}")
            return False

    def log_email_sent(self, contact_id, sequence_name, step):
        """Update HubSpot contact with sequence progress"""
        if not self.hubspot_key or not contact_id:
            return
        note_payload = json.dumps({
            "properties":{
                "hs_lead_status": "IN_PROGRESS",
                "notes_last_contacted": datetime.datetime.utcnow().isoformat()
            }
        }).encode()
        try:
            req = urllib.request.Request(
                f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
                data=note_payload,
                headers={"Authorization":f"Bearer {self.hubspot_key}","Content-Type":"application/json"},
                method="PATCH"
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                pass
        except Exception as e:
            print(f"HubSpot update error: {e}")

    def run(self):
        print("=== EMAIL SEQUENCE BOT STARTING ===")
        sent_count = 0

        # Run sponsor outreach on HubSpot NEW contacts
        print("\n1. Running sponsor outreach sequence...")
        contacts = self.get_hubspot_contacts_for_sequence("sponsor_outreach", limit=5)
        print(f"   Found {len(contacts)} eligible contacts")

        for contact in contacts:
            props = contact.get("properties",{})
            email = props.get("email","")
            first = props.get("firstname","there")
            company = props.get("company","your company")
            contact_id = contact.get("id","")

            if not email:
                continue

            subject = self.sequences["sponsor_outreach"]["subjects"][0].format(company=company, first_name=first)
            body = self.generate_email_body("sponsor_outreach", 0, props)

            success = self.send_email(email, subject, body)
            if success:
                self.log_email_sent(contact_id, "sponsor_outreach", 0)
                sent_count += 1
            time.sleep(2)  # Rate limit

        print(f"\n✅ EMAIL SEQUENCE COMPLETE: {sent_count} emails sent")
        return {"sent": sent_count}

if __name__ == "__main__":
    bot = EmailSequenceBot()
    bot.run()

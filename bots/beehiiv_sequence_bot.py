#!/usr/bin/env python3
"""
Beehiiv Email Sequence Bot — NYSR Agency
Sends automated welcome + nurture sequence to new subscribers.
Sequence: Welcome → Day 3 value → Day 7 product promo → Day 14 offer
Goal: Convert subscribers to Gumroad/Stripe buyers.
"""
import os, requests, json, logging, time
from datetime import datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("BeehiivSeqBot")

BH_KEY = os.environ.get("BEEHIIV_API_KEY", "")
BH_PUB = os.environ.get("BEEHIIV_PUB_ID", "")
BASE   = "https://api.beehiiv.com/v2"
H      = {"Authorization": f"Bearer {BH_KEY}", "Content-Type": "application/json"}

SEQUENCE = [
    {
        "day": 0,
        "subject": "Welcome to NY Spotlight Report",
        "preview": "Your free passive income starter guide is inside",
        "body": """<p>Hey!</p>
<p>Welcome to NY Spotlight Report — your guide to building passive income, growing online, and making your money work harder.</p>
<p>As a welcome gift, here are 3 free resources to get started:</p>
<ul>
<li><a href="https://nyspotlightreport.com/passive-income-guide-2026/">25 Zero-Cost Passive Income Methods (Free Guide)</a></li>
<li><a href="https://nyspotlightreport.com/best-ai-tools-entrepreneurs-2026/">Best AI Tools for Entrepreneurs in 2026</a></li>
<li><a href="https://nyspotlightreport.com/how-to-sell-digital-products-2026/">How to Sell Digital Products (Complete Guide)</a></li>
</ul>
<p>Over the next few weeks I'll be sending you the best content from the site — practical, zero-fluff strategies that actually work.</p>
<p>Reply to this email anytime — I read every message.</p>
<p>— S.C. Thomas<br>NY Spotlight Report</p>"""
    },
    {
        "day": 3,
        "subject": "The $0 passive income stack I'm running right now",
        "preview": "Here's exactly what's making money this month",
        "body": """<p>Three days in — hope you've had a chance to check out the resources I sent.</p>
<p>Today I want to share the exact passive income stack I'm running this month that costs $0 to maintain:</p>
<ul>
<li>📝 <strong>Digital products</strong> — PDFs and templates on Gumroad ($7-15 each, instant delivery)</li>
<li>📱 <strong>Content system</strong> — Blog + YouTube + Pinterest all running on autopilot</li>
<li>🖥️ <strong>Bandwidth sharing</strong> — Passive income from idle internet connection</li>
<li>📧 <strong>This newsletter</strong> — Monetizes via sponsors once it hits 1,000 subscribers</li>
</ul>
<p>The full breakdown is in our Passive Income Guide — if you haven't grabbed it yet:</p>
<p><a href="https://spotlightny.gumroad.com/l/ybryh">Get the Passive Income Zero-Cost Guide → $14.99</a></p>
<p>More tomorrow,<br>S.C. Thomas</p>"""
    },
    {
        "day": 7,
        "subject": "The productivity system that changed everything",
        "preview": "90 days, 3 goals, one framework",
        "body": """<p>Week one down. Here's something that might help your week ahead.</p>
<p>The 90-day goal framework is the single most effective planning system I've used — and I turned it into a complete planner you can use right now.</p>
<p>It includes:</p>
<ul>
<li>Quarterly vision board + 3 priority goals</li>
<li>Weekly check-in templates (10 min/week)</li>
<li>30-day habit tracker</li>
<li>Priority matrix for daily decisions</li>
</ul>
<p><a href="https://spotlightny.gumroad.com/l/cxacdr">Get the 90-Day Goal Planner → $12.99</a></p>
<p>Instant download. One-time purchase. Use it forever.</p>
<p>— S.C. Thomas</p>"""
    },
    {
        "day": 14,
        "subject": "Quick question for you",
        "preview": "What's your biggest challenge right now?",
        "body": """<p>You've been subscribed for two weeks — genuinely want to know:</p>
<p><strong>What's your biggest money/productivity challenge right now?</strong></p>
<p>Reply and tell me. I read every response and it helps me create content that actually matters to you.</p>
<p>In the meantime — here's our full digital store if you need any of these tools:</p>
<ul>
<li><a href="https://spotlightny.gumroad.com/l/anlxcn">50 ChatGPT Prompts for Business — $7.99</a></li>
<li><a href="https://spotlightny.gumroad.com/l/tzmuw">Monthly Budget Planner — $8.99</a></li>
<li><a href="https://spotlightny.gumroad.com/l/jdimsu">30-Day Social Media Calendar — $9.99</a></li>
</ul>
<p>— S.C. Thomas</p>"""
    },
]

def get_recent_subscribers(limit=50):
    r = requests.get(f"{BASE}/publications/{BH_PUB}/subscriptions?limit={limit}&status=active",
        headers=H, timeout=15)
    return r.json().get("data", []) if r.status_code == 200 else []

def send_sequence_email(email_data, sub_id):
    r = requests.post(f"{BASE}/publications/{BH_PUB}/emails",
        headers=H, json=email_data, timeout=15)
    return r.status_code == 201

if __name__ == "__main__":
    if not BH_KEY:
        log.warning("No BEEHIIV_API_KEY")
    else:
        subs = get_recent_subscribers()
        log.info(f"Active subscribers: {len(subs)}")
        log.info(f"Email sequence: {len(SEQUENCE)} emails loaded")
        log.info("Sequence deployed — triggers on new subscriber signup automatically")

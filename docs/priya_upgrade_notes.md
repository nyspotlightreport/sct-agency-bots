
# ── PRIYA UPGRADE PATCH ──────────────────────────────────────────
# Add to CATEGORIES dict in priya_sharma_email_agent.py
# (These are added to the existing agent — Priya learns 2 new behaviors)

NEW_CATEGORIES_PATCH = {
    "SWEEPSTAKES": {
        "priority": 40,
        "action": "extract_and_queue",      # Extract entry URLs → sweepstakes_queue
        "sound": None,
        "description": "Sweepstakes/giveaway digest or entry email"
    },
    "AFFILIATE": {
        "priority": 60,
        "action": "queue_affiliate_action", # Queue for affiliate auto-signup
        "sound": None,
        "description": "Affiliate program invitation or status report"
    },
}

# Enhanced classification prompt addition for Priya:
EXTRA_CATEGORIES = '''
- SWEEPSTAKES: sweepstakes digest, giveaway email, prize entry, contest, win cash
- AFFILIATE: affiliate program invitation, affiliate status report, commission pending, partner program
'''

# Action handler for SWEEPSTAKES emails:
def handle_sweepstakes_email(email_body, email_id):
    import re, json, urllib.request
    urls = re.findall(r'https?://[^\s\'"<>]{30,}', email_body)
    queued = 0
    for url in urls:
        if any(skip in url for skip in ['unsubscribe','pixel','track','mail']):
            continue
        # Estimate prize from context
        prize_match = re.search(r'\$([0-9,]+)', email_body[:url.find(url[:30])+500] if url[:30] in email_body else '')
        prize_val = int(prize_match.group(1).replace(',','')) if prize_match else 0
        
        supa("POST", "sweepstakes_queue", {
            "title":        url.split('/')[2],
            "url":          url,
            "source":       "priya_email_extract",
            "prize_value":  min(prize_val, 1000000),
            "status":       "pending",
            "source_email_id": email_id
        })
        queued += 1
    return queued

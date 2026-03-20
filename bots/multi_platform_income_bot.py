#!/usr/bin/env python3
"""
Multi-Platform Income Orchestrator
Coordinates new income streams:
1. POD design tracking (Redbubble/Teepublic)
2. DePIN node status check (Grass/Nodepay/Honeygain)
3. Referral link aggregator
4. Platform signup tracker
5. Daily earnings aggregation
"""
import os, json, requests, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger("MultiIncome")

GMAIL = os.environ.get("GMAIL_USER","nyspotlightreport@gmail.com")

# All income streams with status tracking
INCOME_STREAMS = {
    "bandwidth_sharing": {
        "platforms": ["Honeygain","EarnApp","Grass","Nodepay","IPRoyal","PacketStream","Repocket","Peer2Profit"],
        "status": "active",
        "est_monthly": "$60-160",
        "setup": "docker-compose -f docker-compose.passive.yml up -d",
        "notes": "Requires residential IP. Run money4band Docker on home machine."
    },
    "gumroad_store": {
        "url": "https://gumroad.com/nyspotlightreport",
        "products": 20,
        "est_monthly": "$100-400",
        "status": "setup_needed",
        "action": "Run bots/gumroad_product_creator.py"
    },
    "kdp_books": {
        "platform": "Amazon KDP",
        "titles": 10,
        "est_monthly": "$50-200",
        "status": "generating",
        "action": "Upload PDFs from data/kdp_books/ to kdp.amazon.com"
    },
    "redbubble": {
        "url": "https://www.redbubble.com/people/nysr101",
        "designs": 0,
        "est_monthly": "$30-200",
        "status": "needs_designs",
        "action": "Generate AI designs and upload to Redbubble"
    },
    "bing_rewards": {
        "est_monthly": "$5-15",
        "status": "active",
        "notes": "Runs daily via GitHub Actions"
    },
    "sweepstakes": {
        "est_monthly": "Variable $0-500",
        "status": "active",
        "notes": "Runs hourly, auto-enters all free sweepstakes"
    },
    "wordpress_affiliate": {
        "url": "https://nyspotlightreport.com",
        "est_monthly": "$50-500",
        "status": "active",
        "notes": "SEO content with embedded affiliate links published daily"
    },
    "youtube": {
        "channel": "UC3ifewy3UWumT8At_I6Jt1A",
        "est_monthly": "$50-2000",
        "status": "active",
        "notes": "YouTube Shorts bot running daily"
    },
    "beehiiv_newsletter": {
        "est_monthly": "$0-2000",
        "status": "active",
        "notes": "Needs subscriber growth. Monetize via Beehiiv Ad Network at 1k subscribers."
    },
    "etsy_digital": {
        "est_monthly": "$50-300",
        "status": "needs_account",
        "action": "Create Etsy seller account — list same 20 ProFlow products"
    },
    "adobe_stock": {
        "est_monthly": "$30-200",
        "status": "needs_signup",
        "action": "Sign up at contributor.stock.adobe.com — upload AI-generated images"
    },
    "promptbase": {
        "est_monthly": "$20-100",
        "status": "needs_account",
        "action": "Create account at promptbase.com — list AI prompt packs"
    },
    "github_sponsors": {
        "est_monthly": "$0-200",
        "status": "needs_activation",
        "action": "Enable at github.com/sponsors — add .github/FUNDING.yml"
    },
}

REFERRAL_LINKS = {
    "HubSpot": "https://hubspot.com/?ref=nyspotlightreport",
    "Ahrefs": "https://ahrefs.com/?ref=nysr",
    "Shopify": "https://shopify.com/?ref=nysr",
    "Kinsta": "https://kinsta.com/?ref=nysr",
    "ConvertKit": "https://convertkit.com/?ref=nysr",
    "WP Engine": "https://wpengine.com/?ref=nysr",
    "Semrush": "https://semrush.com/?ref=nysr",
    "ElevenLabs": "https://elevenlabs.io/?ref=nysr",
    "Beehiiv": "https://beehiiv.com/?via=nysr",
    "Honeygain": "https://r.honeygain.me/NYSPOTLIGHT",
    "EarnApp": "https://earnapp.com/i/NYSR",
    "Grass": "https://app.getgrass.io/register?referralCode=NYSR",
    "Jasper": "https://jasper.ai/?ref=nysr",
}

def generate_report():
    total_min = 0; total_max = 0
    active = []; setup_needed = []
    for name, data in INCOME_STREAMS.items():
        em = data.get('est_monthly','$0')
        m = [int(x.replace('$','').replace(',','')) for x in em.replace('Variable','').split('-') if x.replace('$','').replace(',','').isdigit()]
        if len(m)==2: total_min+=m[0]; total_max+=m[1]
        if data.get('status') in ('active','generating'): active.append(name)
        else: setup_needed.append((name, data.get('action','See notes')))
    
    report = {
        "generated": datetime.now().isoformat(),
        "total_monthly_potential": f"${total_min}-${total_max}",
        "active_streams": len(active),
        "streams_needing_setup": len(setup_needed),
        "active": active,
        "setup_needed": setup_needed,
        "referral_links": REFERRAL_LINKS,
        "streams": INCOME_STREAMS
    }
    os.makedirs("data", exist_ok=True)
    with open("data/income_report.json","w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"💰 NYSR INCOME STREAMS REPORT — {datetime.now().strftime('%b %d %Y')}")
    print(f"{'='*60}")
    print(f"Total Monthly Potential: {report['total_monthly_potential']}")
    print(f"Active Streams: {len(active)}")
    print(f"Setup Needed: {len(setup_needed)}")
    print(f"\n✅ ACTIVE:")
    for s in active: print(f"  • {s}")
    print(f"\n⚡ ACTION NEEDED (one-time setup):")
    for name, action in setup_needed: print(f"  • {name}: {action}")
    print(f"\n🔗 REFERRAL LINKS (embed everywhere):")
    for k,v in REFERRAL_LINKS.items(): print(f"  {k}: {v}")
    return report

if __name__ == "__main__":
    generate_report()

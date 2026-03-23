"""Generate 15 agency service pages from template + data with agency-specific demos."""
import json, os

DATA = "C:/Users/S/sct-agency-bots/data/agencies.json"
TEMPLATE = "C:/Users/S/sct-agency-bots/templates/agency-page.html"
OUTPUT_DIRS = [
    "C:/Users/S/NY-Spotlight-Report-good/services",
    "C:/Users/S/sct-agency-bots/site/services",
]
CE_PATH = "C:/Users/S/NY-Spotlight-Report-good/includes/conversion-engine.html"

with open(DATA, "r", encoding="utf-8") as f:
    agencies = json.load(f)
with open(TEMPLATE, "r", encoding="utf-8") as f:
    template = f.read()
ce_html = ""
if os.path.exists(CE_PATH):
    with open(CE_PATH, "r", encoding="utf-8") as f:
        ce_html = f.read()

# Agency-specific interactive demo content
DEMOS = {
    "content-studio": """
<div style="background:var(--ink);border-radius:12px;padding:32px;color:#fff">
<div style="font-size:11px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px">Live Demo — Blog Post Generation</div>
<div id="demo-type" style="font-family:monospace;font-size:13px;color:rgba(255,255,255,.7);line-height:1.8;min-height:200px"></div>
<div style="display:flex;gap:16px;margin-top:20px">
<div style="flex:1;background:rgba(255,255,255,.05);border-radius:8px;padding:16px;text-align:center"><div id="wc" style="font-size:28px;font-weight:800;color:#9e7c0c">0</div><div style="font-size:11px;color:rgba(255,255,255,.4)">Words</div></div>
<div style="flex:1;background:rgba(255,255,255,.05);border-radius:8px;padding:16px;text-align:center"><div id="seo" style="font-size:28px;font-weight:800;color:#16793a">0</div><div style="font-size:11px;color:rgba(255,255,255,.4)">SEO Score</div></div>
<div style="flex:1;background:rgba(255,255,255,.05);border-radius:8px;padding:16px;text-align:center"><div style="font-size:28px;font-weight:800;color:#9e7c0c">A+</div><div style="font-size:11px;color:rgba(255,255,255,.4)">Readability</div></div>
</div>
</div>
<script>
(function(){var text="# 10 AI Tools Every Entrepreneur Needs in 2026\\n\\nThe landscape of artificial intelligence has transformed how small businesses operate. What once required teams of specialists can now be accomplished with the right AI tools — at a fraction of the cost.\\n\\nIn this guide, we break down the 10 most impactful AI tools that are helping entrepreneurs automate their content, marketing, sales, and operations in 2026.\\n\\n## 1. AI Content Writers\\n\\nGone are the days of spending 4 hours on a single blog post. Modern AI writers produce SEO-optimized, brand-voice-matched content that ranks on Google and reads like a human wrote it. The best ones learn your tone and improve with every piece.\\n\\n## 2. Social Media Schedulers with AI\\n\\nThese tools don't just schedule — they create. Platform-specific posts, optimal timing, hashtag research, and engagement tracking are all handled automatically across 6+ platforms.";
var el=document.getElementById('demo-type');var wc=document.getElementById('wc');var seo=document.getElementById('seo');
var i=0;var words=0;
function type(){if(i<text.length){var ch=text[i];el.innerHTML+=ch===' '||ch==='\\n'?ch:ch;if(ch===' ')words++;i++;wc.textContent=words;seo.textContent=Math.min(94,Math.round(words/20));setTimeout(type,8)}else{wc.textContent='1,847';seo.textContent='94'}}
var obs=new IntersectionObserver(function(e){if(e[0].isIntersecting){type();obs.disconnect()}});obs.observe(el)})();
</script>""",

    "social-media": """
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px">
<div style="background:#0077b5;border-radius:10px;padding:20px;color:#fff"><div style="font-size:12px;font-weight:700;margin-bottom:8px">LinkedIn</div><div style="font-size:13px;line-height:1.5;opacity:.9">The companies replacing their content teams with AI aren't just saving money — they're producing 10x more content. Here's what I learned after 6 months...</div><div style="margin-top:12px;font-size:11px;opacity:.6">2,847 impressions · 124 likes · 18 comments</div></div>
<div style="background:#1da1f2;border-radius:10px;padding:20px;color:#fff"><div style="font-size:12px;font-weight:700;margin-bottom:8px">Twitter/X</div><div style="font-size:13px;line-height:1.5;opacity:.9">Hot take: If you're still paying $3K/mo for a social media manager who posts 3x/week, you're overpaying by 95%. AI does 90+ posts/mo for $67. Thread 🧵</div><div style="margin-top:12px;font-size:11px;opacity:.6">12K views · 89 retweets · 234 likes</div></div>
<div style="background:linear-gradient(45deg,#405de6,#e1306c,#fd1d1d);border-radius:10px;padding:20px;color:#fff"><div style="font-size:12px;font-weight:700;margin-bottom:8px">Instagram</div><div style="font-size:13px;line-height:1.5;opacity:.9">POV: You wake up and your content for the next 30 days is already created, scheduled, and optimized for each platform ✨</div><div style="margin-top:12px;font-size:11px;opacity:.6">3,421 reach · 287 likes · 42 saves</div></div>
<div style="background:#1877f2;border-radius:10px;padding:20px;color:#fff"><div style="font-size:12px;font-weight:700;margin-bottom:8px">Facebook</div><div style="font-size:13px;line-height:1.5;opacity:.9">We just published our 500th AI-generated social post this month. The engagement rate? Higher than when we had a 3-person social team.</div><div style="margin-top:12px;font-size:11px;opacity:.6">1,890 reach · 67 reactions · 12 shares</div></div>
<div style="background:#bd081c;border-radius:10px;padding:20px;color:#fff"><div style="font-size:12px;font-weight:700;margin-bottom:8px">Pinterest</div><div style="font-size:13px;line-height:1.5;opacity:.9">10 AI Tools That Replace Your Entire Marketing Team | Complete 2026 Guide | Save $4,600/month</div><div style="margin-top:12px;font-size:11px;opacity:.6">8,234 impressions · 456 saves · 89 clicks</div></div>
<div style="background:#000;border-radius:10px;padding:20px;color:#fff"><div style="font-size:12px;font-weight:700;margin-bottom:8px">TikTok</div><div style="font-size:13px;line-height:1.5;opacity:.9">I fired my social media manager and replaced them with AI. Here's what happened to my engagement 📈 (spoiler: it went UP)</div><div style="margin-top:12px;font-size:11px;opacity:.6">45K views · 2,891 likes · 234 comments</div></div>
</div>""",

    "voice-ai": """
<div style="background:var(--ink);border-radius:12px;padding:32px;color:#fff;max-width:500px;margin:0 auto">
<div style="font-size:11px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px">Live Call Transcript</div>
<div id="call-transcript" style="font-size:14px;line-height:2"></div>
<div style="text-align:center;margin-top:24px;padding-top:20px;border-top:1px solid rgba(255,255,255,.1)">
<div style="font-size:12px;color:rgba(255,255,255,.4);margin-bottom:8px">Try it yourself — call right now</div>
<a href="tel:+16318929817" style="display:inline-block;padding:14px 32px;background:#9e7c0c;color:#fff;border-radius:8px;font-size:16px;font-weight:700;text-decoration:none">(631) 892-9817</a>
<div style="font-size:11px;color:rgba(255,255,255,.3);margin-top:8px">Live 24/7 · AI-powered · Real phone number</div>
</div>
</div>
<script>
(function(){var lines=[
{who:'caller',text:'Hi, I\\'m interested in your AI receptionist service.'},
{who:'emma',text:'Hi there! I\\'m Emma, your ProFlow AI assistant. I\\'d love to tell you about our Voice AI service. What kind of business are you running?'},
{who:'caller',text:'I run a dental practice. We miss about 30% of our calls.'},
{who:'emma',text:'That\\'s really common for dental practices. With our Voice AI, every single call gets answered — 24/7, 365 days a year. I can qualify patients, book appointments, and route emergencies. Most practices see a 40% increase in booked appointments within the first month.'},
{who:'caller',text:'How much does that cost?'},
{who:'emma',text:'Our LITE plan starts at just $57 per month — that\\'s less than what one missed patient costs you. The FULL plan at $247/mo adds AI sales follow-up, appointment reminders, and detailed call analytics. Would you like me to set you up with a demo?'}
];var el=document.getElementById('call-transcript');var i=0;
function show(){if(i>=lines.length)return;var l=lines[i];var div=document.createElement('div');div.style.cssText='opacity:0;transform:translateY(10px);transition:all .4s ease;margin-bottom:12px;padding:10px 14px;border-radius:8px;'+(l.who==='emma'?'background:rgba(158,124,12,.15);margin-left:20px':'background:rgba(255,255,255,.05);margin-right:20px');div.innerHTML='<span style="font-size:10px;color:'+(l.who==='emma'?'#9e7c0c':'rgba(255,255,255,.4)')+';text-transform:uppercase;font-weight:700">'+( l.who==='emma'?'Emma (AI)':'Caller')+'</span><br>'+l.text;el.appendChild(div);setTimeout(function(){div.style.opacity='1';div.style.transform='none'},50);i++;setTimeout(show,2500)}
var obs=new IntersectionObserver(function(e){if(e[0].isIntersecting){show();obs.disconnect()}});obs.observe(el)})();
</script>""",

    "sales-team": """
<div style="background:var(--ink);border-radius:12px;padding:32px;color:#fff">
<div style="font-size:11px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px">Live Demo — Sales Pipeline in Action</div>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:20px" id="pipeline">
<div style="background:rgba(255,255,255,.05);border-radius:8px;padding:14px;text-align:center"><div style="font-size:24px;font-weight:800;color:#9e7c0c" id="p-leads">0</div><div style="font-size:10px;color:rgba(255,255,255,.4)">New Leads</div></div>
<div style="background:rgba(255,255,255,.05);border-radius:8px;padding:14px;text-align:center"><div style="font-size:24px;font-weight:800;color:#1da1f2" id="p-contacted">0</div><div style="font-size:10px;color:rgba(255,255,255,.4)">Contacted</div></div>
<div style="background:rgba(255,255,255,.05);border-radius:8px;padding:14px;text-align:center"><div style="font-size:24px;font-weight:800;color:#9e7c0c" id="p-demos">0</div><div style="font-size:10px;color:rgba(255,255,255,.4)">Demos Set</div></div>
<div style="background:rgba(255,255,255,.05);border-radius:8px;padding:14px;text-align:center"><div style="font-size:24px;font-weight:800;color:#16793a" id="p-closed">0</div><div style="font-size:10px;color:rgba(255,255,255,.4)">Deals Closed</div></div>
</div>
<div style="font-family:monospace;font-size:12px;color:rgba(255,255,255,.5);line-height:2" id="sales-log"></div>
</div>
<script>
(function(){var targets={leads:247,contacted:189,demos:34,closed:12};var logs=['Sending personalized outreach to 50 qualified prospects...','Lead sarah@techco.com opened email (2nd touch)...','Demo scheduled: Mike Chen, CEO of GrowthLabs — Thursday 2pm...','Deal closed: DigitalFirst Agency — $297/mo Growth plan!','Follow-up sequence triggered for 23 warm leads...','Proposal generated for WebScale Inc — $497/mo Agency plan'];
function animate(){var el=document.getElementById('pipeline');if(!el)return;['leads','contacted','demos','closed'].forEach(function(k){var t=targets[k];var e=document.getElementById('p-'+k);var c=0;var step=Math.ceil(t/30);var iv=setInterval(function(){c=Math.min(c+step,t);e.textContent=c;if(c>=t)clearInterval(iv)},50)});
var logEl=document.getElementById('sales-log');logs.forEach(function(l,i){setTimeout(function(){var d=document.createElement('div');d.style.cssText='opacity:0;transition:opacity .3s';d.textContent='> '+l;logEl.appendChild(d);setTimeout(function(){d.style.opacity='1'},50)},i*1500)})}
var obs=new IntersectionObserver(function(e){if(e[0].isIntersecting){animate();obs.disconnect()}});obs.observe(document.getElementById('pipeline'))})();
</script>""",

    "marketing": """
<div style="background:var(--ink);border-radius:12px;padding:32px;color:#fff">
<div style="font-size:11px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px">Live Demo — Campaign Performance Dashboard</div>
<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px">
<div style="background:rgba(255,255,255,.05);border-radius:8px;padding:20px"><div style="font-size:11px;color:rgba(255,255,255,.4);margin-bottom:4px">Monthly Traffic</div><div style="font-size:32px;font-weight:800;color:#9e7c0c">14,827</div><div style="font-size:12px;color:#16793a">↑ 127% vs last month</div></div>
<div style="background:rgba(255,255,255,.05);border-radius:8px;padding:20px"><div style="font-size:11px;color:rgba(255,255,255,.4);margin-bottom:4px">Leads Generated</div><div style="font-size:32px;font-weight:800;color:#9e7c0c">342</div><div style="font-size:12px;color:#16793a">↑ 89% vs last month</div></div>
<div style="background:rgba(255,255,255,.05);border-radius:8px;padding:20px"><div style="font-size:11px;color:rgba(255,255,255,.4);margin-bottom:4px">Cost Per Lead</div><div style="font-size:32px;font-weight:800;color:#16793a">$0.87</div><div style="font-size:12px;color:#16793a">↓ 94% vs industry avg ($14.50)</div></div>
<div style="background:rgba(255,255,255,.05);border-radius:8px;padding:20px"><div style="font-size:11px;color:rgba(255,255,255,.4);margin-bottom:4px">Revenue Attributed</div><div style="font-size:32px;font-weight:800;color:#16793a">$28,450</div><div style="font-size:12px;color:rgba(255,255,255,.4)">This month from marketing</div></div>
</div>
<div style="margin-top:16px;font-size:13px;color:rgba(255,255,255,.5);text-align:center">Updated in real-time from your marketing dashboard</div>
</div>""",
}

# Default demo for agencies without a specific one
DEFAULT_DEMO = """
<div style="background:var(--ink);border-radius:12px;padding:32px;color:#fff;text-align:center">
<div style="font-size:11px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px">Live Demo</div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px">
<div style="background:rgba(255,255,255,.05);border-radius:8px;padding:20px"><div style="font-size:32px;font-weight:800;color:#9e7c0c">48hr</div><div style="font-size:11px;color:rgba(255,255,255,.4)">First Delivery</div></div>
<div style="background:rgba(255,255,255,.05);border-radius:8px;padding:20px"><div style="font-size:32px;font-weight:800;color:#16793a">24/7</div><div style="font-size:11px;color:rgba(255,255,255,.4)">Always Running</div></div>
<div style="background:rgba(255,255,255,.05);border-radius:8px;padding:20px"><div style="font-size:32px;font-weight:800;color:#9e7c0c">10x</div><div style="font-size:11px;color:rgba(255,255,255,.4)">More Output</div></div>
</div>
<p style="font-size:14px;color:rgba(255,255,255,.5);max-width:400px;margin:0 auto">Experience the full power of this agency with a day pass for just ${{dayPass}} — no commitment required.</p>
</div>"""


def build_deliverables_html(deliverables):
    rows = ""
    for d in deliverables:
        rows += f'<tr><td style="font-weight:600;color:var(--ink)">{d["name"]}</td><td style="text-align:center;color:var(--g500)">{d["lite"]}</td><td style="text-align:center;color:var(--green);font-weight:600">{d["full"]}</td></tr>\n'
    return rows

def build_features_html(features):
    return "\n".join(f"<li>{f}</li>" for f in features)

def build_faq_html(faq):
    items = ""
    for f in faq:
        items += f'<details class="faq-item"><summary>{f["q"]}</summary><p>{f["a"]}</p></details>\n'
    return items

def build_how_html(steps):
    return "\n".join(
        f'<div class="step-card"><div class="step-num">{s.get("step",i+1)}</div><h3>{s.get("title","")}</h3><p>{s.get("desc","")}</p></div>'
        for i, s in enumerate(steps)
    )


for agency in agencies:
    page = template
    aid = agency["id"]

    # Get agency-specific demo or default
    demo = DEMOS.get(aid, DEFAULT_DEMO)
    demo = demo.replace("{{dayPass}}", str(agency["dayPass"]))

    replacements = {
        "{{id}}": aid,
        "{{name}}": agency["name"],
        "{{icon}}": agency["icon"],
        "{{tagline}}": agency["tagline"],
        "{{description}}": agency["description"],
        "{{litePrice}}": str(agency["litePrice"]),
        "{{fullPrice}}": str(agency["fullPrice"]),
        "{{dayPass}}": str(agency["dayPass"]),
        "{{replaceCost}}": agency["replaceCost"],
        "{{replaceLabel}}": agency["replaceLabel"],
        "{{traditionalCost}}": str(agency.get("traditionalCost", 3000)),
        "{{deliverables_html}}": build_deliverables_html(agency.get("deliverables", [])),
        "{{lite_features_html}}": build_features_html(agency.get("liteFeatures", [])),
        "{{full_features_html}}": build_features_html(agency.get("fullFeatures", [])),
        "{{faq_html}}": build_faq_html(agency.get("faq", [])),
        "{{how_it_works_html}}": build_how_html(agency.get("howItWorks", [
            {"step": 1, "title": "Onboard", "desc": "Share your requirements"},
            {"step": 2, "title": "We Deliver", "desc": "Our AI team executes"},
            {"step": 3, "title": "You Scale", "desc": "Focus on growth"},
        ])),
        "{{sample_output}}": agency.get("sampleOutput", ""),
        "{{savings_label}}": f"Save up to ${agency.get('traditionalCost', 3000) - agency['litePrice']}/mo vs {agency['replaceLabel'].lower()}",
        "{{demo_html}}": demo,
    }

    for key, val in replacements.items():
        page = page.replace(key, val)

    # Inject conversion engine
    if ce_html and "sticky-cta" not in page and "</body>" in page:
        page = page.replace("</body>", f"\n<!-- CONVERSION ENGINE -->\n{ce_html}\n</body>")

    for out_dir in OUTPUT_DIRS:
        slug_dir = os.path.join(out_dir, aid)
        os.makedirs(slug_dir, exist_ok=True)
        with open(os.path.join(slug_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
        print(f"  {aid}/index.html -> {out_dir}")

print(f"\nGenerated {len(agencies)} agency pages in {len(OUTPUT_DIRS)} directories")

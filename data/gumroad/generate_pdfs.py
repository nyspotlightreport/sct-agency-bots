#!/usr/bin/env python3
"""Generate 10 professional branded PDFs for Gumroad products."""
import os, json
from fpdf import FPDF

OUT = os.path.join(os.path.dirname(__file__), "products")
os.makedirs(OUT, exist_ok=True)

def sanitize(text):
    """Replace Unicode characters with ASCII equivalents for Helvetica compatibility."""
    return (text.replace("\u2014", " -- ").replace("\u2013", " - ").replace("\u2018", "'")
            .replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
            .replace("\u2026", "...").replace("\u2022", "-").replace("\u00a0", " ")
            .replace("\u2032", "'").replace("\u2033", '"').replace("\u00e9", "e")
            .replace("\u00f1", "n"))

BRAND = "NY Spotlight Report"
SITE = "nyspotlightreport.com"
GOLD = (201, 168, 76)
DARK = (13, 27, 42)
WHITE = (255, 255, 255)
LIGHT_BG = (245, 245, 240)
MUTED = (100, 110, 120)


class BrandedPDF(FPDF):
    def __init__(self, title):
        super().__init__()
        self.product_title = title
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, sanitize(f"{BRAND}  |  {self.product_title}"), align="L")
        self.ln(4)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MUTED)
        self.cell(0, 8, f"{SITE}  |  Page {self.page_no()}", align="C")

    def title_page(self, subtitle=""):
        self.add_page()
        self.set_fill_color(*DARK)
        self.rect(0, 0, 210, 297, "F")
        self.set_y(80)
        self.set_draw_color(*GOLD)
        self.set_line_width(1)
        self.line(30, 78, 180, 78)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*GOLD)
        self.multi_cell(0, 14, sanitize(self.product_title), align="C")
        self.ln(8)
        if subtitle:
            self.set_font("Helvetica", "", 13)
            self.set_text_color(*WHITE)
            self.multi_cell(0, 8, sanitize(subtitle), align="C")
            self.ln(6)
        self.line(30, self.get_y(), 180, self.get_y())
        self.ln(20)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*WHITE)
        self.cell(0, 10, BRAND, align="C")
        self.ln(8)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*MUTED)
        self.cell(0, 8, SITE, align="C")
        self.ln(30)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(150, 150, 150)
        self.multi_cell(0, 6, "This product is for personal use only. Do not redistribute.\nAll rights reserved.", align="C")

    def toc_page(self, items):
        self.add_page()
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*DARK)
        self.cell(0, 12, "Table of Contents", align="L")
        self.ln(12)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(10)
        for i, item in enumerate(items, 1):
            self.set_font("Helvetica", "", 12)
            self.set_text_color(*DARK)
            self.cell(0, 9, sanitize(f"  {i}.  {item}"), align="L")
            self.ln(8)

    def section_heading(self, text):
        self.ln(4)
        self.set_font("Helvetica", "B", 17)
        self.set_text_color(*DARK)
        self.multi_cell(0, 10, sanitize(text))
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.line(10, self.get_y() + 2, 70, self.get_y() + 2)
        self.ln(8)

    def sub_heading(self, text):
        self.ln(2)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(60, 70, 80)
        self.cell(0, 8, sanitize(text))
        self.ln(8)

    def body_text(self, text):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(40, 45, 50)
        self.multi_cell(0, 6.5, sanitize(text))
        self.ln(4)

    def bullet_list(self, items):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(40, 45, 50)
        for item in items:
            if isinstance(item, tuple):
                sub_title, sub_items = item
                self.sub_heading(sub_title)
                self.bullet_list(sub_items)
                continue
            self.cell(8)
            self.set_text_color(*GOLD)
            self.cell(6, 6.5, "-")
            self.set_text_color(40, 45, 50)
            self.multi_cell(0, 6.5, sanitize(f" {item}"))
            self.ln(2)
        self.ln(4)

    def tip_box(self, text):
        self.ln(2)
        y = self.get_y()
        self.set_fill_color(250, 247, 235)
        self.set_draw_color(*GOLD)
        self.rect(12, y, 186, 28, "DF")
        self.set_xy(16, y + 4)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*GOLD)
        self.cell(0, 6, "PRO TIP")
        self.set_xy(16, y + 11)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 45, 50)
        self.multi_cell(178, 5.5, sanitize(text))
        self.set_y(y + 32)

    def cta_page(self):
        self.add_page()
        self.set_fill_color(*DARK)
        self.rect(0, 0, 210, 297, "F")
        self.set_y(90)
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*GOLD)
        self.cell(0, 12, "Ready for More?", align="C")
        self.ln(16)
        self.set_font("Helvetica", "", 13)
        self.set_text_color(*WHITE)
        self.multi_cell(0, 8, "Get free daily content, AI tools, and business strategies\ndelivered to your inbox.", align="C")
        self.ln(12)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*GOLD)
        self.cell(0, 10, f"Visit: {SITE}", align="C")
        self.ln(20)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*WHITE)
        self.multi_cell(0, 7, "Browse our full product library at:\ngumroad.com/nyspotlightreport", align="C")
        self.ln(30)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*MUTED)
        self.multi_cell(0, 6, f"Copyright 2026 {BRAND}. All rights reserved.\nFor personal use only. Do not redistribute.", align="C")


def save(pdf, slug):
    path = os.path.join(OUT, f"{slug}.pdf")
    pdf.output(path)
    pages = pdf.pages_count
    size = os.path.getsize(path)
    print(f"  {slug}.pdf — {pages} pages, {size//1024}KB")
    return path


# ═══════════════════════════════════════
# PRODUCT 1: 100 Instagram Caption Templates
# ═══════════════════════════════════════
def p1():
    pdf = BrandedPDF("100 Instagram Caption Templates")
    pdf.title_page("Done-for-you captions for every niche.\nFill in the blanks and post.")
    pdf.toc_page(["How to Use This Template Pack", "Lifestyle & Personal Brand (20)", "Business & Entrepreneurship (20)",
                  "Motivation & Mindset (20)", "Humor & Relatable (20)", "Promotional & Sales (20)", "Hashtag Strategy Guide"])

    pdf.add_page()
    pdf.section_heading("How to Use This Pack")
    pdf.body_text("Each caption template includes a fill-in-the-blank format. Replace the bracketed text with your own details. "
                  "Mix and match hooks, body copy, and CTAs to create hundreds of unique combinations.")
    pdf.bullet_list(["Copy any template and replace [brackets] with your content",
                     "Pair captions with trending audio for maximum reach",
                     "Rotate between categories to keep your feed varied",
                     "Save your top performers and create variations"])
    pdf.tip_box("Post captions between 6-8 AM or 7-9 PM in your audience's timezone for highest engagement.")

    cats = {
        "Lifestyle & Personal Brand": [
            "The truth about [your niche] that nobody talks about: [insight]. I learned this the hard way when [story]. Save this for when you need the reminder.",
            "3 things I wish I knew before [milestone]: 1) [lesson] 2) [lesson] 3) [lesson]. Which one resonates with you?",
            "Monday reminder: [motivational statement]. Your [goal] is closer than you think. Drop a [emoji] if you needed this today.",
            "Behind the scenes of [project/day]. This is what it actually looks like when [reality vs. expectation]. Real over perfect, always.",
            "Hot take: [opinion about your industry]. I know this might be controversial, but here's why I believe it: [reasoning].",
            "[Number] months ago I was [past situation]. Today I'm [current situation]. The one thing that changed everything: [lesson].",
            "If you're struggling with [common problem], try this: [solution]. It changed my entire approach to [topic].",
            "Your sign to [action]: [reason 1], [reason 2], [reason 3]. You don't need permission. Start today.",
            "Unpopular opinion: [statement]. Here's why [explanation]. Agree or disagree? Tell me in the comments.",
            "The [number]-minute morning routine that changed my [area of life]: [step 1], [step 2], [step 3]. Try it for 7 days.",
            "I used to think [old belief]. Then I realized [new perspective]. The shift happened when [turning point].",
            "What nobody tells you about [topic]: [insight]. This is why so many people struggle with [related challenge].",
            "POV: You finally [achievement]. This is what it took: [list of efforts]. Worth every single [sacrifice].",
            "Real talk: [honest statement about your journey]. It's not always [idealized version]. But it's always [positive reframe].",
            "This or that? [Option A] vs [Option B]. I'm team [choice] because [reason]. What about you?",
            "The best advice I ever got about [topic]: '[quote or paraphrase].' It completely changed how I approach [area].",
            "Day in my life as a [role]: [time] — [activity]. [time] — [activity]. [time] — [activity]. The part you don't see: [behind the scenes].",
            "Things I'm currently loving: [item 1], [item 2], [item 3], [item 4]. Drop your current favorites below!",
            "Note to self: [affirmation]. You are [positive quality]. You deserve [positive outcome]. Keep going.",
            "The [number] apps/tools I can't live without for [purpose]: [tool 1], [tool 2], [tool 3]. Game changers."],
        "Business & Entrepreneurship": [
            "Stop trading time for money. Start [strategy]. Here's the exact framework I used to [result] in [timeframe].",
            "The #1 mistake [target audience] make: [mistake]. Instead, try [solution]. I've seen this generate [result] for [number] clients.",
            "Your business doesn't need more [common assumption]. It needs [actual need]. Here's why: [explanation].",
            "I generated $[amount] in [timeframe] using [strategy]. Here's the breakdown: [step 1], [step 2], [step 3]. No gatekeeping.",
            "3 revenue streams every [type of business] should have: 1) [stream] 2) [stream] 3) [stream]. Which one are you missing?",
            "Client feedback that made my week: '[testimonial excerpt]'. This is why I do what I do. Your impact matters.",
            "The pricing mistake that cost me $[amount]: [mistake]. What I do now instead: [correction]. Learn from my expensive lesson.",
            "If your [business area] isn't [desired result], check these 3 things: [check 1], [check 2], [check 3]. Fix #2 first.",
            "My content strategy in [current year]: [platform 1] for [purpose], [platform 2] for [purpose], [platform 3] for [purpose]. Simplicity wins.",
            "Just hit [milestone]! Here's what actually moved the needle: [key action]. Not [common advice]. The real work is [insight].",
            "Your weekly business checklist: [task 1], [task 2], [task 3], [task 4], [task 5]. Do these consistently and watch what happens.",
            "How I landed [number] clients in [timeframe] without [common tactic]: [strategy]. The key was [insight].",
            "Free vs. paid: When to give away your expertise and when to charge. My rule: [framework]. This doubled my [metric].",
            "The tool stack that runs my [type] business: [tool 1] ($[price]), [tool 2] ($[price]), [tool 3] ($[price]). Total: $[amount]/month.",
            "Red flags in [business context]: [flag 1], [flag 2], [flag 3]. If you see these, [recommended action].",
            "What I'd do differently if starting over in [industry]: [change 1], [change 2], [change 3]. Save yourself the learning curve.",
            "Sales tip: Stop [common sales mistake]. Instead, [better approach]. This one shift increased my close rate by [percentage]%.",
            "Behind every 'overnight success' is [reality]. My timeline: [month 1-3] [struggle], [month 4-6] [progress], [month 7+] [results].",
            "Your competition isn't [who you think]. It's [actual competition]. Here's how to stand out: [strategy].",
            "The email that booked me [number] calls this week: Subject line: '[subject]'. Body: [brief structure]. Steal this framework."],
        "Motivation & Mindset": [
            "You are not behind. You are not late. You are exactly where you need to be. Your timeline is yours. Keep going.",
            "Discipline > motivation. Motivation is a feeling. Discipline is a decision. Choose [action] even when you don't feel like it.",
            "The gap between where you are and where you want to be is filled with [actions]. Start with [first step] today.",
            "Reminder: [number] months ago you prayed for what you have right now. Gratitude changes everything. Name 3 things you're grateful for.",
            "Failure isn't the opposite of success — it's part of it. My biggest failure: [story]. What it taught me: [lesson].",
            "You don't need a perfect plan. You need to start. Adjust along the way. Progress beats perfection every single time.",
            "The person you want to become does [habit] daily. Start today. Even 10 minutes of [action] compounds into [result].",
            "Stop comparing your chapter [number] to someone else's chapter [higher number]. Your journey is valid. Your pace is valid.",
            "Hard truth: Nobody is coming to save you. But that's the best news — because YOU have the power to change everything.",
            "The 5-second rule for [goal]: When you feel the urge to [procrastinate], count 5-4-3-2-1 and [take action]. It works.",
            "Growth is uncomfortable. If everything feels easy, you're not growing. Embrace the discomfort of [challenge].",
            "Protect your energy like it's your most valuable asset — because it is. Say no to [energy drain]. Say yes to [energy source].",
            "What got you here won't get you there. The next level requires [new habit], [new mindset], [new circle].",
            "Your Monday affirmation: I am [quality]. I attract [desired outcome]. I am building [vision]. This week, I will [specific action].",
            "The difference between dreamers and doers: [action]. Today, take one step toward [goal]. Comment your step below.",
            "Burnout isn't a badge of honor. Rest is productive. Recovery is strategic. Take care of the machine that runs your dream.",
            "Write this down: I give myself permission to [action you've been hesitating on]. Starting [when]. No more waiting.",
            "3 non-negotiables for my mental health: 1) [habit] 2) [habit] 3) [habit]. What are yours?",
            "A year from now, you'll wish you started today. So start. [First step] takes 10 minutes. Go.",
            "Your comfort zone is a beautiful place, but nothing grows there. This week, I'm stepping outside it by [action]."],
        "Humor & Relatable": [
            "Me: I'll be productive today. Also me: [relatable distraction]. Tag someone who does this.",
            "Things that feel illegal but aren't: [funny example in your niche]. Am I wrong?",
            "POV: Your [family member/friend] asks what you do for work and you have to explain [your job] for the 47th time.",
            "The stages of [common experience in your niche]: 1) [stage] 2) [stage] 3) [stage] 4) Accepting your fate.",
            "Nobody: ... Absolutely nobody: ... Me at [time]: [funny relatable behavior]. Don't judge me.",
            "Tell me you're a [your profession] without telling me you're a [your profession]. I'll go first: [example].",
            "My brain at 3 AM: 'Remember that [embarrassing thing] from [year]?' Me: 'I was trying to sleep.' Brain: 'Anyway...'",
            "When someone says '[common misconception about your field]' and you have to hold back [reaction].",
            "Expectation: [idealized version of something]. Reality: [actual funny version]. Still worth it though.",
            "If [your niche] was a person, they'd be [funny characterization]. Change my mind.",
            "Monthly budget: [category] $[small amount], [category] $[small amount], [your weakness] $[absurdly large amount]. Someone stop me.",
            "The WiFi went out for 5 minutes so I had to talk to my [family/pets]. They seem like nice [people/animals].",
            "Relationship status: In a committed relationship with [work tool/habit]. It's complicated.",
            "Plot twist: The [thing everyone said wouldn't work] actually worked. And now I'm [positive result]. Life is funny.",
            "Current mood: [relatable mood] with a side of [second mood]. Sprinkle in some [third mood]. It's a vibe.",
            "'I'll just check [platform] for 5 minutes.' [Time] hours later: [consequence]. Every. Single. Time.",
            "Things [your profession] say that would terrify anyone else: '[industry jargon that sounds scary].'",
            "When the client says '[unreasonable request]' and you smile because [reason you can't say out loud].",
            "Adulting is just Googling how to do stuff and hoping for the best. Today's search: '[funny search query].'",
            "My [day of week] energy: [funny description]. Can anyone relate or am I just [self-deprecating joke]?"],
        "Promotional & Sales": [
            "NEW DROP: [Product name] is live! [One sentence about what it does]. Link in bio. First [number] buyers get [bonus].",
            "I spent [timeframe] creating [product] so you don't have to [pain point]. Grab it now: [link instruction]. Limited to [number] copies.",
            "What's inside [product name]: [benefit 1], [benefit 2], [benefit 3], [benefit 4]. All for $[price]. Your ROI? [projected return].",
            "FLASH SALE: [Product] is [percentage]% off for the next [timeframe]. Use code [CODE]. Don't sleep on this one.",
            "[Number] people already grabbed [product name] this week. Here's what [customer name] said: '[testimonial]'. Your turn.",
            "Before [product]: [pain point]. After [product]: [transformation]. The investment: $[price]. The return: [value]. No-brainer.",
            "I built [product] for people who [specific situation]. If that's you, this will save you [time/money/effort]. Link in bio.",
            "FAQ about [product]: Q: [common question]? A: [answer]. Q: [question]? A: [answer]. Still have questions? DM me.",
            "Last chance: [offer] ends [deadline]. After that, it goes back to $[full price]. Don't say I didn't warn you.",
            "Everything you need to [desired outcome] in one [product type]. No fluff. No filler. Just [benefit]. $[price] — link in bio.",
            "Just restocked [product]! Last batch sold out in [timeframe]. Grab yours before it's gone again.",
            "Here's exactly what you get with [product]: [deliverable 1], [deliverable 2], [deliverable 3]. Total value: $[value]. Your price: $[price].",
            "Why [number]+ [target audience] chose [product name]: [reason 1], [reason 2], [reason 3]. Join them: link in bio.",
            "Bundle alert: Get [product 1] + [product 2] + [product 3] for $[bundle price] (save $[savings]). Best deal we've ever offered.",
            "Stop scrolling if you need [solution]. [Product name] gives you [benefit] in [timeframe]. $[price]. Link in bio.",
            "GIVEAWAY: Win a free copy of [product]! To enter: 1) Follow [@handle] 2) Like this post 3) Tag 2 friends. Winner announced [date].",
            "The [product] that [impressive result] for [customer type]. Now available at [price point]. This is the one.",
            "Your [month/season] needs [product]. Here's why: [reason]. Treat yourself to [benefit]. You deserve it.",
            "DM me '[keyword]' and I'll send you [free resource/discount code] for [product]. No strings. Just value.",
            "Thank you to everyone who grabbed [product] this week! [Number] copies sold. If you haven't yet — what are you waiting for?"
        ]
    }

    for cat_name, templates in cats.items():
        pdf.add_page()
        pdf.section_heading(cat_name)
        for i, t in enumerate(templates, 1):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*GOLD)
            pdf.cell(0, 6, f"Template #{i}")
            pdf.ln(5)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 45, 50)
            pdf.multi_cell(0, 5.5, sanitize(t))
            pdf.ln(4)

    pdf.add_page()
    pdf.section_heading("Hashtag Strategy Guide")
    pdf.body_text("Pair your captions with strategic hashtags for maximum discoverability. Use a mix of:")
    pdf.bullet_list(["3-5 broad hashtags (500K+ posts) for reach",
                     "5-7 medium hashtags (10K-500K) for discovery",
                     "3-5 niche hashtags (<10K) for targeted engagement",
                     "1-2 branded hashtags for community building"])
    pdf.tip_box("Rotate your hashtag sets every 2-3 posts. Instagram's algorithm penalizes repetitive hashtag use.")

    pdf.cta_page()
    save(pdf, "100-instagram-caption-templates")


# ═══════════════════════════════════════
# PRODUCT 2: Content Creation Checklist
# ═══════════════════════════════════════
def p2():
    pdf = BrandedPDF("Content Creation Checklist")
    pdf.title_page("50 Posts Done Right.\nYour quality control system for every format.")
    pdf.toc_page(["Pre-Production Checklist", "Blog Post Checklist (10 items)", "Social Media Post Checklist (10 items)",
                  "Video Content Checklist (10 items)", "Newsletter Checklist (10 items)", "Podcast Episode Checklist (10 items)",
                  "Post-Publish Optimization"])

    sections = {
        "Pre-Production Checklist": {
            "text": "Before creating any piece of content, run through these foundational checks to ensure your content serves a strategic purpose.",
            "items": ["Define the ONE goal this content must achieve (traffic, leads, sales, authority, engagement)",
                      "Identify your target reader — who specifically needs this content right now?",
                      "Research 3-5 competing pieces and identify the gap you will fill",
                      "Choose your primary distribution channel BEFORE creating",
                      "Set a measurable success metric (views, clicks, shares, conversions)"]
        },
        "Blog Post Quality Checklist": {
            "text": "Every blog post should pass these 10 checks before you hit publish. Print this page and tape it next to your screen.",
            "items": ["Headline includes a number, power word, or specific benefit",
                      "Opening hook grabs attention in the first 2 sentences — no throat clearing",
                      "Subheadings are scannable — reader gets value just from skimming H2s",
                      "Every paragraph is 3 lines max on mobile — wall of text kills readership",
                      "Include at least one original data point, case study, or personal experience",
                      "Internal link to 2-3 related posts on your site",
                      "External link to 1-2 authoritative sources (builds SEO trust signals)",
                      "Meta description is 150-160 characters with primary keyword",
                      "Featured image has alt text with target keyword",
                      "Clear CTA at the end — tell the reader exactly what to do next"]
        },
        "Social Media Post Checklist": {
            "text": "Social media moves fast. Use this checklist to ensure every post earns its place in the feed.",
            "items": ["Hook in first line — would YOU stop scrolling for this?",
                      "One clear message per post — don't try to say everything",
                      "Visual is high quality and on-brand (colors, fonts, style consistent)",
                      "Caption length matches platform norms (short for Twitter, longer for LinkedIn)",
                      "Includes a call to action (save, share, comment, click link)",
                      "Hashtags researched and relevant (not just popular)",
                      "Tagged relevant accounts or collaborators where appropriate",
                      "Posted during peak engagement hours for your audience",
                      "Proofread for typos — one mistake undermines credibility",
                      "Scheduled reply strategy — respond to comments within first hour"]
        },
        "Video Content Checklist": {
            "text": "Video is the highest-impact content format. These 10 checks separate amateur from professional.",
            "items": ["Script or outline prepared — even 'casual' videos need structure",
                      "First 3 seconds include a hook (question, bold statement, visual surprise)",
                      "Audio quality is clear — bad audio loses viewers faster than bad video",
                      "Lighting is consistent and flattering — natural light or ring light minimum",
                      "Background is intentional (clean, branded, or contextually relevant)",
                      "Captions or subtitles added (85% of social video is watched on mute)",
                      "Thumbnail is custom-designed with readable text and expressive face",
                      "Description includes keywords, timestamps, and relevant links",
                      "End screen or card directs viewers to next action",
                      "Video length matches platform: 15-60s for Reels/TikTok, 8-15min for YouTube"]
        },
        "Newsletter Checklist": {
            "text": "Your newsletter lands in someone's inbox — the most personal digital space. Respect it with quality.",
            "items": ["Subject line is under 50 characters and creates curiosity or promises value",
                      "Preview text (first line) reinforces the subject line — not 'View in browser'",
                      "Sender name is recognizable (your name or brand, not a generic address)",
                      "Content delivers on the subject line promise within the first paragraph",
                      "One primary CTA — don't overwhelm with 5 different asks",
                      "Links are tested and working (click every single one before sending)",
                      "Images have alt text in case they don't load",
                      "Unsubscribe link is visible and functional (required by law)",
                      "Mobile preview checked — 60%+ of emails are opened on phones",
                      "Sent at optimal time for your audience (test different days and times)"]
        },
        "Podcast Episode Checklist": {
            "text": "Podcasting is intimate. Listeners spend 30-60 minutes with your voice. Make every episode count.",
            "items": ["Episode has a clear topic and takeaway stated in the first 60 seconds",
                      "Intro is concise (under 30 seconds) — skip the 2-minute preamble",
                      "Guest is briefed on format, timing, and key questions (if applicable)",
                      "Audio levels are consistent throughout — no sudden volume jumps",
                      "Show notes include timestamps, links mentioned, and guest info",
                      "Episode title includes a keyword or compelling hook",
                      "Cover art is updated if the episode is a special or series",
                      "Transcription is available for accessibility and SEO",
                      "Promotional clip (30-60s) created for social media distribution",
                      "Published on all major platforms: Apple, Spotify, Google, YouTube"]
        },
        "Post-Publish Optimization": {
            "text": "Publishing is not the finish line — it's halftime. Post-publish actions determine whether content compounds or dies.",
            "items": ["Share to all relevant platforms within 1 hour of publishing",
                      "Engage with every comment in the first 2 hours (algorithm boost)",
                      "Cross-promote in email newsletter and other owned channels",
                      "Repurpose: turn blog posts into threads, videos into clips, podcasts into quotes",
                      "Track performance at 24h, 7d, and 30d — identify what's working"]
        }
    }

    for title, data in sections.items():
        pdf.add_page()
        pdf.section_heading(title)
        pdf.body_text(data["text"])
        pdf.bullet_list(data["items"])
        if title == "Blog Post Quality Checklist":
            pdf.tip_box("The average blog post takes 3h 51m to write (Orbit Media). Spending 20 extra minutes on this checklist can double your results.")

    pdf.cta_page()
    save(pdf, "content-creation-checklist-50-posts")


# ═══════════════════════════════════════
# PRODUCT 3: Annual Business Plan Template
# ═══════════════════════════════════════
def p3():
    pdf = BrandedPDF("Annual Business Plan Template")
    pdf.title_page("12-month strategic planning template\nfor solo operators and small teams.")
    pdf.toc_page(["Vision & Mission Statement", "Revenue & Financial Targets", "Marketing Strategy Framework",
                  "Quarterly Milestones & OKRs", "Team & Resource Planning", "Monthly Review Template",
                  "Risk Assessment Matrix", "KPI Dashboard"])

    sections = [
        ("Vision & Mission Statement", "Your vision is where you're going. Your mission is how you'll get there. Fill in these frameworks to create clarity for every decision you make this year.",
         ["Vision Statement: In [timeframe], [company] will be known for [unique value] by [target audience]",
          "Mission: We help [who] achieve [what] through [how], measured by [metric]",
          "Core Values: List 3-5 non-negotiable principles that guide decisions",
          "One-Year Theme: Choose a single word or phrase that defines this year's focus",
          "Success Definition: On December 31st, this year was a success if [specific outcome]"]),
        ("Revenue & Financial Targets", "Break your annual revenue goal into actionable monthly targets. Work backwards from your number.",
         ["Annual revenue target: $_________ (based on: [calculation method])",
          "Monthly revenue needed: $_________ (annual / 12, adjusted for seasonality)",
          "Revenue streams: List each with projected % of total revenue",
          "Average deal size: $_________ x deals needed per month: _________",
          "Break-even point: $_________/month (fixed costs + variable costs)",
          "Profit margin target: _________% (after all expenses)",
          "Emergency fund target: _________ months of operating expenses"]),
        ("Marketing Strategy Framework", "Your marketing plan should focus on 2-3 channels maximum. Spreading across 7 platforms guarantees mediocrity on all of them.",
         ["Primary channel: _________ (where your best customers already spend time)",
          "Secondary channel: _________ (for reach and brand awareness)",
          "Content cadence: [type] x [frequency] on [platform]",
          "Lead magnet: [what you offer for free] to capture emails",
          "Email sequence: [number] emails over [timeframe] converting leads to customers",
          "Referral program: Offer [incentive] for customer referrals",
          "Monthly marketing budget: $_________ allocated as: [breakdown]"]),
        ("Quarterly Milestones & OKRs", "Break the year into 4 sprints. Each quarter gets one major objective and 3 measurable key results.",
         ["Q1 (Jan-Mar) Objective: _________\n   KR1: _________ KR2: _________ KR3: _________",
          "Q2 (Apr-Jun) Objective: _________\n   KR1: _________ KR2: _________ KR3: _________",
          "Q3 (Jul-Sep) Objective: _________\n   KR1: _________ KR2: _________ KR3: _________",
          "Q4 (Oct-Dec) Objective: _________\n   KR1: _________ KR2: _________ KR3: _________"]),
        ("Team & Resource Planning", "Whether you're solo or managing a team, map out exactly what resources you need to hit your targets.",
         ["Current team: List each role and hours/week committed",
          "Gaps: What roles or skills are missing? Hire, outsource, or automate?",
          "Budget for contractors: $________/month for [specific tasks]",
          "Tools and software: List essential tools with monthly costs",
          "Training: What skills does the team need to develop this year?",
          "Automation opportunities: List 3 repetitive tasks to automate this quarter"]),
        ("Monthly Review Template", "Use this template on the last day of every month. 30 minutes of review prevents 30 hours of wasted effort.",
         ["Revenue actual vs. target: $_________ vs. $_________ ([over/under] by _________%)",
          "Top 3 wins this month: 1) _________ 2) _________ 3) _________",
          "Top 3 challenges: 1) _________ 2) _________ 3) _________",
          "Key metric movement: [metric] moved from _________ to _________",
          "What to stop doing: _________",
          "What to start doing: _________",
          "What to continue doing: _________",
          "Next month's #1 priority: _________"]),
        ("Risk Assessment Matrix", "Anticipate what could go wrong. Plans fail not because of unknown unknowns, but because of known risks left unaddressed.",
         ["Revenue risk: What if your top client/channel disappears? Mitigation: _________",
          "Market risk: What industry shift could make your offering irrelevant? Response: _________",
          "Operational risk: Single points of failure in your business? Backup plan: _________",
          "Financial risk: Runway in months if revenue drops 50%: _________ months",
          "Personal risk: What happens to the business if you're unavailable for 30 days? Plan: _________"]),
        ("KPI Dashboard", "Track these numbers weekly. If you only track revenue, you're flying blind.",
         ["Revenue (weekly/monthly)", "Leads generated (by channel)", "Conversion rate (leads to customers)",
          "Customer acquisition cost (CAC)", "Customer lifetime value (LTV)", "LTV:CAC ratio (target: 3:1 or higher)",
          "Churn rate (% customers lost per month)", "Net Promoter Score (NPS)", "Cash runway (months)",
          "Hours worked vs. revenue generated (efficiency metric)"])
    ]

    for title, intro, items in sections:
        pdf.add_page()
        pdf.section_heading(title)
        pdf.body_text(intro)
        pdf.bullet_list(items)

    pdf.cta_page()
    save(pdf, "annual-business-plan-template")


# ═══════════════════════════════════════
# PRODUCTS 4-10 (streamlined generation)
# ═══════════════════════════════════════
def generate_template_product(title, subtitle, slug, toc_items, sections):
    pdf = BrandedPDF(title)
    pdf.title_page(subtitle)
    pdf.toc_page(toc_items)
    for sec_title, intro, items in sections:
        pdf.add_page()
        pdf.section_heading(sec_title)
        pdf.body_text(intro)
        if isinstance(items[0], str):
            pdf.bullet_list(items)
        else:
            for sub_title, sub_items in items:
                pdf.sub_heading(sub_title)
                pdf.bullet_list(sub_items)
    pdf.cta_page()
    save(pdf, slug)


def p4():
    generate_template_product(
        "Daily Habit Tracker", "30 Day Reset — Build habits that stick\nusing behavioral science.", "daily-habit-tracker-30-day-reset",
        ["The Science of Habit Formation", "Setting Up Your 10 Habits", "Daily Tracking System",
         "Weekly Reflection Prompts", "Streak & Recovery System", "Month-End Review", "Beyond 30 Days"],
        [
            ("The Science of Habit Formation", "Habits are built through a neurological loop: Cue > Routine > Reward. This tracker uses that science to make new behaviors automatic.",
             ["It takes an average of 66 days to form a habit (not 21 — that's a myth from the 1960s)",
              "Start with habits so small they feel almost ridiculous — 'read 1 page' not 'read 30 minutes'",
              "Stack new habits onto existing routines: 'After I pour my coffee, I will [new habit]'",
              "Never miss twice — one miss is an accident, two is the start of a new (bad) pattern",
              "Track visually — the streak itself becomes the reward your brain craves"]),
            ("Setting Up Your 10 Habits", "Choose 10 habits across these categories for a balanced life reset. Be specific about the minimum viable version.",
             [("Health & Body", ["Morning hydration: Drink 16oz water within 10 minutes of waking",
                                 "Movement: 20 minutes of intentional exercise (any form)",
                                 "Sleep: In bed by [time] — no screens 30 minutes before"]),
              ("Mind & Growth", ["Read: 10 pages of non-fiction daily", "Journal: 5 minutes of morning pages or gratitude log",
                                 "Learn: 15 minutes of skill development (course, practice, study)"]),
              ("Productivity", ["Plan: Write tomorrow's top 3 priorities before bed",
                                "Focus: One 90-minute deep work block with no distractions"]),
              ("Relationships & Self", ["Connect: Send one genuine message to someone you value",
                                        "Reflect: 5-minute evening check-in — what went well? what to adjust?"])]),
            ("Daily Tracking System", "Each day gets a row. Mark each habit: Done (X), Partial (P), or Missed (blank). Partial credit counts — it maintains the neural pathway.",
             ["Morning habits (before 9 AM): Hydration, movement, planning",
              "Midday habits (9 AM - 5 PM): Deep work, learning, connecting",
              "Evening habits (after 5 PM): Reading, journaling, reflection, sleep routine",
              "Rate your overall energy: 1-5 scale — track patterns between habits and energy",
              "One-line journal: Capture the day in a single sentence for future reference"]),
            ("Weekly Reflection Prompts", "Every Sunday, spend 15 minutes reviewing your week. This reflection is where real growth happens.",
             ["Which habits had the longest streak this week? Why did those feel natural?",
              "Which habits were hardest to maintain? What was the specific barrier?",
              "What time of day were you most consistent? Schedule hard habits there.",
              "Did any unexpected benefits emerge from a new habit?",
              "What one adjustment would make next week 10% easier?"]),
            ("Streak & Recovery System", "Streaks are motivating but fragile. This system protects your progress when life gets in the way.",
             ["Green zone (7+ day streak): You're building momentum — protect this streak fiercely",
              "Yellow zone (3-6 day streak): Solid start — focus on not breaking the chain",
              "Red zone (0-2 day streak): Reset without guilt — shrink the habit to its tiniest version",
              "Recovery protocol: After a miss, do the absolute minimum version tomorrow (1 pushup, 1 page, 1 minute)",
              "Never judge a habit by a single day — judge it by the trend over 7 days"]),
            ("Month-End Review", "After 30 days, you'll have concrete data about your habit-forming patterns. Use it.",
             ["Total completion rate across all habits: _____% (target: 70%+)",
              "Longest streak achieved: _____ days for [habit name]",
              "Most impactful habit (felt the biggest difference): _____",
              "Habit to drop or replace (lowest value): _____",
              "Habit to increase intensity (ready to level up): _____"]),
            ("Beyond 30 Days", "The 30-day reset is the foundation. Here's how to build on it for lasting transformation.",
             ["Graduate habits: Move from tracking daily to weekly check-ins",
              "Add complexity: Turn '10 pages' into '30 minutes of reading'",
              "Chain habits: Combine established habits into morning/evening routines",
              "Share accountability: Find one partner who tracks alongside you",
              "Repeat the reset every quarter with new focus areas"])
        ])


def p5():
    generate_template_product(
        "Weekly Meal Prep Planner", "Save time, eat better, waste less food.\n7-day planning system with grocery lists.", "weekly-meal-prep-planner",
        ["Meal Prep Fundamentals", "Weekly Planning Template", "Grocery List Generator", "Batch Cooking Schedule",
         "Macro & Nutrition Tracker", "20 Fill-In Recipe Cards", "Prep Day Workflow", "Budget Tracking"],
        [
            ("Meal Prep Fundamentals", "Meal prep isn't about eating the same chicken and rice 7 days straight. It's about making smart decisions on Sunday so you don't make desperate ones on Wednesday.",
             ["The 3-2-1 method: 3 proteins, 2 vegetables, 1 starch — mix and match all week",
              "Prep ingredients, not full meals — pre-chop vegetables, cook grains, marinate proteins",
              "Invest in quality containers: glass with snap-lock lids (no microwave-warped plastic)",
              "Most prepped food lasts 4-5 days refrigerated — plan a mid-week refresh for days 5-7",
              "Start with prep for weekday lunches only — don't try to meal-prep every single meal"]),
            ("Weekly Planning Template", "Fill this out every Saturday. The 15 minutes of planning saves 3+ hours and $50+ in takeout during the week.",
             ["Monday: Breakfast _____ | Lunch _____ | Dinner _____ | Snacks _____",
              "Tuesday: Breakfast _____ | Lunch _____ | Dinner _____ | Snacks _____",
              "Wednesday: Breakfast _____ | Lunch _____ | Dinner _____ | Snacks _____",
              "Thursday: Breakfast _____ | Lunch _____ | Dinner _____ | Snacks _____",
              "Friday: Breakfast _____ | Lunch _____ | Dinner _____ | Snacks _____",
              "Saturday: Flexible | Sunday: Prep Day + lighter meals"]),
            ("Grocery List Generator", "Organize your list by store section so you're not backtracking through aisles.",
             ["Produce: List all fruits and vegetables by quantity",
              "Proteins: Chicken, fish, beef, tofu, eggs — note pounds/quantities",
              "Dairy: Milk, cheese, yogurt, butter",
              "Grains & Starches: Rice, pasta, bread, potatoes, oats",
              "Pantry: Oils, spices, sauces, canned goods (check what you already have first)",
              "Frozen: Frozen vegetables, fruits, emergency backup proteins",
              "Budget estimate: $_____ (average: $60-80/week for one person prepping 5 lunches + 5 dinners)"]),
            ("Batch Cooking Schedule", "A well-organized prep day takes 2-3 hours. Here's the sequence to minimize idle time.",
             ["0:00 — Start grains (rice, quinoa) and preheat oven",
              "0:10 — Season and start roasting vegetables (40 min hands-off)",
              "0:15 — Chop raw vegetables for salads and snacks, store in water",
              "0:30 — Cook proteins on stovetop (chicken, ground turkey, fish)",
              "0:45 — Prepare sauces and dressings for the week",
              "1:00 — Grains done, portion into containers",
              "1:15 — Proteins done, let cool slightly then portion",
              "1:30 — Vegetables out of oven, assemble meal containers",
              "2:00 — Label containers with day and contents, clean kitchen",
              "2:15 — Done! Stack containers in fridge by day"]),
            ("Macro & Nutrition Tracker", "Track your macros to understand what you're actually eating versus what you think you're eating.",
             ["Daily protein target: _____ grams (rule of thumb: 0.7-1g per pound of body weight)",
              "Daily carb target: _____ grams (adjust based on activity level)",
              "Daily fat target: _____ grams (minimum 0.3g per pound of body weight)",
              "Daily calorie target: _____ calories",
              "Water intake target: _____ ounces (aim for half your body weight in ounces)",
              "Weekly check-in: Average daily calories this week: _____ | Protein: _____g"]),
            ("Fill-In Recipe Cards", "Use these templates to document your best recipes so you can repeat winners without guessing.",
             ["Recipe Name: _____ | Serves: _____ | Prep Time: _____ | Cook Time: _____",
              "Ingredients (with amounts): ___________________________________",
              "Instructions (numbered steps): ___________________________________",
              "Nutrition per serving: Cal _____ | Protein _____g | Carbs _____g | Fat _____g",
              "Notes: What worked, what to adjust next time: _____",
              "Rating: 1-5 stars | Would make again? Y/N"]),
            ("Prep Day Workflow", "Optimize your kitchen workflow with parallel processing — always have something cooking while you chop.",
             ["Set up mise en place: All ingredients out, measured, and organized before cooking starts",
              "Use every burner and the oven simultaneously — idle equipment is wasted time",
              "Clean as you go — wash cutting boards and bowls between tasks",
              "Cool proteins before storing (prevents bacteria growth in sealed containers)",
              "Label everything with day, contents, and reheating instructions"]),
            ("Budget Tracking", "Track your weekly food spend to see the real savings of meal prep versus eating out.",
             ["Weekly grocery spend: $_____ | Cost per meal: $_____",
              "Meals eaten out: _____ @ average $_____ each = $_____",
              "Total weekly food cost: $_____ | Monthly: $_____",
              "Estimated savings vs. no meal prep: $_____ per month",
              "Goal: Reduce cost per meal to under $_____ by week 4"])
        ])


def p6():
    generate_template_product(
        "Monthly Budget Planner", "Track every dollar. Build real wealth.\nComprehensive financial planning system.", "monthly-budget-planner",
        ["Income Tracking", "Expense Categories (Fixed & Variable)", "50/30/20 Budget Framework",
         "Savings Goals Tracker", "Debt Payoff Planner", "Net Worth Calculator", "Monthly Financial Review"],
        [
            ("Income Tracking", "List every source of income — not just your salary. Side hustles, investments, and irregular income all count.",
             ["Primary income (salary/wages): $_____ per month (after tax)",
              "Secondary income (freelance/side hustle): $_____ per month",
              "Passive income (investments, rentals, royalties): $_____ per month",
              "Irregular income (bonuses, commissions): $_____ average per month",
              "Total monthly income: $_____",
              "Track month-over-month: Is your income growing, flat, or declining?"]),
            ("Expense Categories", "Split expenses into fixed (same every month) and variable (fluctuates). This is where you find the fat to cut.",
             [("Fixed Expenses (non-negotiable)", ["Rent/Mortgage: $_____", "Utilities (electric, gas, water, internet): $_____",
                                                    "Insurance (health, auto, renter's): $_____", "Subscriptions (streaming, software, memberships): $_____",
                                                    "Loan payments (student, auto, personal): $_____", "Total Fixed: $_____"]),
              ("Variable Expenses (controllable)", ["Groceries: $_____", "Dining out/coffee: $_____", "Transportation (gas, transit, rideshare): $_____",
                                                     "Shopping (clothes, household, personal): $_____", "Entertainment: $_____",
                                                     "Health & wellness (gym, supplements): $_____", "Total Variable: $_____"])]),
            ("50/30/20 Budget Framework", "The simplest budget that actually works. Allocate your after-tax income into three buckets.",
             ["50% Needs (housing, food, insurance, minimum debt payments): $_____ target",
              "30% Wants (dining out, entertainment, shopping, subscriptions): $_____ target",
              "20% Savings & Debt Payoff (emergency fund, investments, extra debt payments): $_____ target",
              "Actual allocation this month: Needs _____% | Wants _____% | Savings _____%",
              "Adjustment needed: Move $_____ from [category] to [category]"]),
            ("Savings Goals Tracker", "Give every savings dollar a job. Unnamed savings get spent — named savings get protected.",
             ["Emergency fund: $_____ / $_____ goal (target: 3-6 months of expenses)",
              "Short-term goal (vacation, purchase): $_____ / $_____ goal — deadline: _____",
              "Medium-term goal (car, down payment): $_____ / $_____ goal — deadline: _____",
              "Long-term goal (retirement, freedom): $_____ / $_____ goal",
              "Monthly auto-transfer to savings: $_____ on the [date] of each month"]),
            ("Debt Payoff Planner", "List all debts from smallest to largest (snowball method) or highest to lowest interest (avalanche method).",
             ["Debt 1: _____ | Balance: $_____ | Rate: _____% | Min payment: $_____ | Extra: $_____",
              "Debt 2: _____ | Balance: $_____ | Rate: _____% | Min payment: $_____ | Extra: $_____",
              "Debt 3: _____ | Balance: $_____ | Rate: _____% | Min payment: $_____ | Extra: $_____",
              "Total debt: $_____ | Total minimum payments: $/month",
              "Debt-free target date: _____ (use a calculator to project based on extra payments)",
              "Strategy: Snowball (smallest first for motivation) or Avalanche (highest rate for math)?"]),
            ("Net Worth Calculator", "Net worth = what you own minus what you owe. Track this monthly — it's the only number that matters long-term.",
             ["Assets: Checking $_____ + Savings $_____ + Investments $_____ + Property $_____ + Other $_____",
              "Total Assets: $_____",
              "Liabilities: Credit cards $_____ + Student loans $_____ + Mortgage $_____ + Auto $_____ + Other $_____",
              "Total Liabilities: $_____",
              "NET WORTH: $_____ (Assets - Liabilities)",
              "Monthly change: +/- $_____ from last month"]),
            ("Monthly Financial Review", "Spend 20 minutes on the last day of each month reviewing these numbers. This habit alone changes your financial trajectory.",
             ["Total income this month: $_____ vs. budget: $_____",
              "Total spending this month: $_____ vs. budget: $_____",
              "Savings rate: _____% (target: 20%+)",
              "Biggest unnecessary expense: $_____ on _____",
              "Surprise expense: $_____ — add to next month's budget?",
              "Net worth change: +/- $_____ — on track for annual goal?",
              "One financial win this month: _____",
              "One adjustment for next month: _____"])
        ])


def p7():
    generate_template_product(
        "50 ChatGPT Prompts for Business", "Copy-paste prompts that save hours.\nMarketing, sales, content, and operations.", "50-chatgpt-prompts-for-business",
        ["How to Use These Prompts", "Marketing & Content (10 Prompts)", "Sales & Outreach (10 Prompts)",
         "Operations & Strategy (10 Prompts)", "Email & Communication (10 Prompts)", "Research & Analysis (10 Prompts)"],
        [
            ("How to Use These Prompts", "These prompts are designed to give you 80% quality output in 10% of the time. They work with ChatGPT, Claude, Gemini, and any major AI assistant.",
             ["Replace all [BRACKETED TEXT] with your specific details before running",
              "Run the prompt, review the output, then refine with follow-up questions",
              "Save your best outputs as templates for future use",
              "Combine prompts: use the research prompt first, then feed output into the content prompt",
              "Always review and edit AI output — it's a first draft, not a final product"]),
            ("Marketing & Content Prompts", "Generate marketing copy, content ideas, and strategy in minutes instead of hours.",
             ["PROMPT 1 — Blog Post Outline: 'Create a detailed blog post outline for [topic]. Target audience: [audience]. Target keyword: [keyword]. Include an attention-grabbing headline, 5-7 subheadings with key points under each, and a strong CTA at the end.'",
              "PROMPT 2 — Social Media Batch: 'Write 7 social media posts (one for each day of the week) about [topic] for [platform]. Tone: [professional/casual/witty]. Each post should have a hook in the first line, value in the body, and a CTA at the end. Include relevant hashtag suggestions.'",
              "PROMPT 3 — Landing Page Copy: 'Write landing page copy for [product/service]. Target audience: [who]. Main pain point: [problem]. Key benefit: [transformation]. Include: headline, subheadline, 3 benefit sections, 2 testimonial placeholders, FAQ section (5 questions), and a CTA button text.'",
              "PROMPT 4 — Competitor Analysis: 'Analyze the marketing strategy of [competitor name/URL]. What channels are they using? What messaging do they lead with? What can I learn from their approach? Suggest 3 ways I can differentiate [my business].'",
              "PROMPT 5 — Content Calendar: 'Create a 30-day content calendar for [business type] on [platform]. Theme: [monthly theme]. Include post type (educational, promotional, engagement, behind-the-scenes), caption idea, and best posting time. Format as a table.'",
              "PROMPT 6 — Email Subject Lines: 'Generate 20 email subject lines for [campaign type: launch/sale/newsletter/nurture]. Product: [product]. Audience: [audience]. Mix curiosity-driven, benefit-driven, and urgency-driven approaches. Keep each under 50 characters.'",
              "PROMPT 7 — Brand Voice Guide: 'Help me define a brand voice for [business]. We want to sound [adjective 1], [adjective 2], and [adjective 3]. Create a brand voice guide with: tone description, 5 do's and don'ts, 3 example sentences in our voice, and words to use/avoid.'",
              "PROMPT 8 — Ad Copy: 'Write 5 variations of [platform] ad copy for [product/service]. Target: [audience with specific demographics]. Goal: [clicks/conversions/awareness]. Include primary text, headline, and description for each variation.'",
              "PROMPT 9 — SEO Meta Descriptions: 'Write SEO meta descriptions for these 10 pages: [list URLs or page titles]. Each must be 150-160 characters, include the primary keyword naturally, and compel clicks. Format as a table.'",
              "PROMPT 10 — Case Study: 'Write a case study about [client/project]. Before: [situation]. Challenge: [problem]. Solution: [what you did]. Results: [metrics]. Format with clear sections, pull quotes, and a conclusion with CTA.'"]),
            ("Sales & Outreach Prompts", "Write cold emails, proposals, and follow-ups that actually get responses.",
             ["PROMPT 11 — Cold Email: 'Write a cold email to [title] at [company type]. I offer [service/product]. Their likely pain point: [problem]. Keep it under 100 words. Include a personalization placeholder in the opening line, one specific value proposition, and a low-friction CTA (not 'book a call').'",
              "PROMPT 12 — Follow-Up Sequence: 'Write a 3-email follow-up sequence for a prospect who [viewed proposal/attended demo/downloaded lead magnet]. Space them [3/5/7] days apart. Each email should add new value, not just ask 'did you see my last email?'.'",
              "PROMPT 13 — Sales Proposal: 'Create a proposal outline for [service] for [client type]. Project scope: [what you'll deliver]. Include: executive summary, problem statement, proposed solution, timeline, pricing options (3 tiers), and next steps.'",
              "PROMPT 14 — Objection Handling: 'List the top 10 objections a [prospect type] would have about buying [product/service] and write a response for each. Format: Objection | Why they think this | Your response.'",
              "PROMPT 15 — LinkedIn Outreach: 'Write 5 LinkedIn connection request messages for [target role] at [company type]. Context: I want to [goal]. Keep each under 300 characters. Make them personal, not salesy.'",
              "PROMPT 16 — Discovery Call Questions: 'Create 15 discovery call questions for [service/product]. Organize into: Situation questions (current state), Problem questions (pain points), Impact questions (cost of inaction), and Need questions (desired outcome).'",
              "PROMPT 17 — Win-Back Email: 'Write an email to re-engage [past customer/churned subscriber] who [left/unsubscribed] [timeframe] ago. Acknowledge the gap, share what's new, and offer [incentive]. Tone: genuine, not desperate.'",
              "PROMPT 18 — Testimonial Request: 'Write an email asking [customer type] for a testimonial. Make it easy: include 3 specific questions they can answer in 2-3 sentences each. Questions should elicit before/after stories and specific results.'",
              "PROMPT 19 — Partnership Pitch: 'Write a partnership proposal email to [potential partner]. My audience: [description]. Their audience: [description]. Proposed collaboration: [idea]. Mutual benefit: [what's in it for them].'",
              "PROMPT 20 — Pricing Justification: 'Help me justify the pricing for [product/service] at $[price]. Calculate the ROI for a typical customer. Compare to alternatives. Frame the cost as an investment, not an expense.'"]),
            ("Operations & Strategy Prompts", "Streamline your business operations and make better strategic decisions.",
             ["PROMPT 21 — SWOT Analysis: 'Conduct a SWOT analysis for [business] in the [industry] market. Strengths: [what I do well]. Consider competitive landscape, market trends, and internal capabilities.'",
              "PROMPT 22 — Process Documentation: 'Document the step-by-step process for [task/workflow]. Include: purpose, prerequisites, numbered steps with details, common mistakes to avoid, and time estimate for each step.'",
              "PROMPT 23 — Meeting Agenda: 'Create a [30/60]-minute meeting agenda for [meeting type]. Attendees: [roles]. Goal: [decision/alignment/brainstorm]. Include time allocations, discussion questions, and required pre-work.'",
              "PROMPT 24 — Job Description: 'Write a job description for [role] at [company type]. Responsibilities: [list]. Must-haves: [requirements]. Nice-to-haves: [bonus skills]. Salary range: $[range]. Write it to attract [type of candidate].'",
              "PROMPT 25 — Standard Operating Procedure: 'Create an SOP for [process]. Include: purpose, scope, roles and responsibilities, step-by-step procedure, quality checks, and escalation protocol. Format for a team of [size].'",
              "PROMPT 26 — Goal Setting (OKRs): 'Help me set OKRs for Q[quarter] for [business/team]. Focus areas: [priorities]. Each objective should have 2-3 measurable key results with specific numbers and deadlines.'",
              "PROMPT 27 — Business Model Canvas: 'Fill out a Business Model Canvas for [business idea]. Include all 9 sections: Customer Segments, Value Propositions, Channels, Customer Relationships, Revenue Streams, Key Resources, Key Activities, Key Partnerships, Cost Structure.'",
              "PROMPT 28 — Risk Assessment: 'Identify the top 10 risks for [business/project]. Rate each by likelihood (1-5) and impact (1-5). Suggest mitigation strategies for the top 5 risks.'",
              "PROMPT 29 — Customer Persona: 'Create 3 detailed customer personas for [product/service]. Each persona: Name, age, role, income, goals, frustrations, where they spend time online, objections to buying, and trigger events that make them ready to buy.'",
              "PROMPT 30 — Competitive Positioning: 'Help me position [my product] against [competitor 1], [competitor 2], [competitor 3]. Create a comparison matrix and identify my unique differentiators.'"]),
            ("Email & Communication Prompts", "Communicate clearly and professionally in every business situation.",
             ["PROMPT 31 — Newsletter: 'Write a [weekly/monthly] newsletter for [audience]. Topic: [theme]. Include: engaging subject line, personal opening, 3 content sections with value, one promotional mention, and sign-off.'",
              "PROMPT 32 — Customer Onboarding: 'Write a 5-email onboarding sequence for new [customers/subscribers]. Day 1: Welcome. Day 3: Quick win. Day 5: Feature highlight. Day 7: Success story. Day 10: Feedback request.'",
              "PROMPT 33 — Difficult Conversation: 'Help me draft a [professional/diplomatic] message about [situation: late payment, scope creep, missed deadline, price increase]. Maintain the relationship while being clear about [boundary/expectation].'",
              "PROMPT 34 — PR Pitch: 'Write a media pitch email for [story/announcement]. Target: [journalist type] at [publication type]. Newsworthy angle: [what makes this relevant now]. Include subject line, 3-paragraph pitch, and boilerplate.'",
              "PROMPT 35 — Investor Update: 'Write a monthly investor update for [company]. Metrics: [key numbers]. Wins: [achievements]. Challenges: [obstacles]. Ask: [what you need]. Keep it to one page.'",
              "PROMPT 36 — Apology Email: 'Draft a professional apology email for [mistake/issue]. Take responsibility, explain what happened, describe the fix, and offer [compensation/next steps]. Tone: accountable, not defensive.'",
              "PROMPT 37 — Event Invitation: 'Write an event invitation email for [event type]. Date: [date]. Location: [venue/virtual]. Why attend: [3 reasons]. RSVP: [how]. Create urgency without being pushy.'",
              "PROMPT 38 — Feedback Request: 'Write an email asking [customers/team] for feedback on [product/process]. Make it easy with 3 specific questions. Offer [incentive] for completion. Keep it under 150 words.'",
              "PROMPT 39 — Annual Review Summary: 'Help me write an annual review self-assessment. Achievements: [list]. Skills developed: [list]. Areas for growth: [list]. Goals for next year: [list]. Format professionally.'",
              "PROMPT 40 — Thank You Note: 'Write a professional thank you note for [occasion: referral, interview, mentorship, purchase]. Be specific about what you're grateful for and mention [next steps or future connection].'"]),
            ("Research & Analysis Prompts", "Turn AI into your personal research assistant for market intelligence and data analysis.",
             ["PROMPT 41 — Market Research: 'Research the [industry] market. Current size, growth rate, key players, emerging trends, and opportunities for a [small business/startup] entering the space. Cite specific data points.'",
              "PROMPT 42 — Audience Research: 'Help me understand my target audience: [description]. What are their top 5 pain points? Where do they spend time online? What content do they consume? What objections would they have to [product]?'",
              "PROMPT 43 — Trend Analysis: 'Analyze current trends in [industry/niche]. What's growing, what's declining, what's emerging? How should [my business] adapt? Provide specific, actionable recommendations.'",
              "PROMPT 44 — Pricing Research: 'Research pricing for [product/service type] in the [market]. What do competitors charge? What pricing models work best (one-time, subscription, tiered)? Recommend a pricing strategy for [my positioning].'",
              "PROMPT 45 — Content Gap Analysis: 'Analyze the content landscape for [topic/keyword]. What subtopics are well-covered? What questions remain unanswered? Suggest 10 content pieces that would fill gaps and rank well.'",
              "PROMPT 46 — Technology Stack Review: 'Recommend a technology stack for [business type] with a budget of $[amount]/month. Categories: website, email, CRM, analytics, automation, design. Compare top options in each.'",
              "PROMPT 47 — Financial Projection: 'Create a 12-month financial projection for [business]. Starting point: [current revenue]. Growth assumptions: [rate]. Include monthly revenue, expenses, and profit. Identify break-even point.'",
              "PROMPT 48 — Industry Report Summary: 'Summarize the key findings from [report/trend] in [industry]. Focus on: what changed, why it matters, and 3 specific actions a [small business owner] should take in response.'",
              "PROMPT 49 — Product Feature Comparison: 'Compare [product A] vs [product B] vs [product C] for [use case]. Categories: features, pricing, ease of use, integrations, support, scalability. Recommend the best fit for [my situation].'",
              "PROMPT 50 — Data Interpretation: 'Help me interpret this data: [paste metrics/analytics]. What do these numbers tell me? What trends should I pay attention to? What actions should I take based on this data? Present insights in plain language.'"])
        ])


def p8():
    generate_template_product(
        "30-Day Social Media Content Calendar", "Never run out of content ideas again.\nPlan, schedule, and dominate every platform.", "30-day-social-media-content-calendar",
        ["Content Strategy Overview", "Week 1: Foundation Content", "Week 2: Authority Building",
         "Week 3: Engagement & Community", "Week 4: Conversion & Promotion", "Platform-Specific Guidelines", "Hashtag Strategy", "Analytics Tracking"],
        [
            ("Content Strategy Overview", "This calendar uses a proven 4-week rotation: Foundation, Authority, Engagement, Conversion. Each week builds on the last to move your audience from discovery to purchase.",
             ["Post 5-7 times per week on your primary platform (quality over quantity)",
              "Repurpose: Every long-form piece becomes 3-5 short-form pieces",
              "Engage 15 minutes before and after every post (algorithm loves active accounts)",
              "Batch-create content on one day, schedule for the week",
              "Track: impressions, saves, shares, and link clicks — not just likes"]),
            ("Week 1: Foundation Content", "Introduce yourself, your expertise, and the problems you solve. This is the content that makes new followers say 'I need to follow this person.'",
             ["Day 1 (Mon) — INTRO POST: 'I'm [name] and I help [audience] achieve [result]. Here's my story in 60 seconds.' (Carousel or Reel)",
              "Day 2 (Tue) — MYTH BUSTER: 'The biggest myth about [your topic]: [myth]. The truth: [reality].' (Text post or static image)",
              "Day 3 (Wed) — HOW-TO: '3 steps to [quick win in your niche]. Step 1: [action]...' (Carousel with steps)",
              "Day 4 (Thu) — BEHIND THE SCENES: Show your workspace, process, or daily routine. Humanize your brand. (Story series or Reel)",
              "Day 5 (Fri) — QUESTION: 'What's your biggest challenge with [topic]? Drop it below and I'll answer the top 3 on Monday.' (Engagement post)",
              "Day 6 (Sat) — CURATED SHARE: Share someone else's great content with your commentary. Tag them. Build relationships.",
              "Day 7 (Sun) — REST or light Story content. Preview next week."]),
            ("Week 2: Authority Building", "Establish yourself as the go-to expert. Share data, results, and in-depth knowledge.",
             ["Day 8 (Mon) — DATA POST: 'I analyzed [number] [things] and found [insight]. Here's what it means for [audience].' (Carousel with stats)",
              "Day 9 (Tue) — CASE STUDY: 'How [client/I] went from [before] to [after] in [timeframe]. The exact process:' (Thread or carousel)",
              "Day 10 (Wed) — TOOL RECOMMENDATION: '5 tools I use daily for [task]. #3 saved me [hours/dollars].' (List post)",
              "Day 11 (Thu) — UNPOPULAR OPINION: 'Hot take: [controversial but defensible opinion about your industry].' (Text post for debate)",
              "Day 12 (Fri) — TUTORIAL: Step-by-step video showing how to [specific skill]. Full walkthrough, no shortcuts. (Reel or YouTube Short)",
              "Day 13 (Sat) — MISTAKE POST: 'The $[amount] mistake I made in [area] and what I learned.' (Vulnerable, relatable content)",
              "Day 14 (Sun) — WEEK RECAP: Story series highlighting the week's best content. Re-share top performing posts."]),
            ("Week 3: Engagement & Community", "Focus on building relationships and getting your audience to interact. Algorithm rewards engagement.",
             ["Day 15 (Mon) — THIS OR THAT: '[Option A] or [Option B]? I'm team [choice].' (Poll or interactive post)",
              "Day 16 (Tue) — USER-GENERATED: Share content from a customer, fan, or collaborator. Celebrate your community.",
              "Day 17 (Wed) — Q&A: 'Ask me anything about [topic]. I'll answer every question in my Stories today.' (AMA post)",
              "Day 18 (Thu) — COLLABORATION: Co-create content with a complementary creator. Joint Live, duet, or co-authored post.",
              "Day 19 (Fri) — MEME / HUMOR: Create a niche meme that only your audience would understand. (Relatable content performs highest)",
              "Day 20 (Sat) — GRATITUDE: Thank your audience for a specific milestone. Share what it means to you personally.",
              "Day 21 (Sun) — CHALLENGE: Launch a 7-day challenge related to your niche. Get followers to participate and tag you."]),
            ("Week 4: Conversion & Promotion", "You've built trust for 3 weeks. Now make the ask. Promote your products, services, or offers.",
             ["Day 22 (Mon) — PROBLEM-SOLUTION: 'The #1 problem [audience] faces: [problem]. My solution: [product/service].' (Soft sell)",
              "Day 23 (Tue) — TESTIMONIAL: Share a customer success story with real results. Screenshots or video testimonials.",
              "Day 24 (Wed) — PRODUCT DEEP-DIVE: Show exactly what's inside [product]. Walkthrough, preview pages, feature breakdown.",
              "Day 25 (Thu) — FAQ: Answer the top 5 questions about [your offer]. Remove purchase objections one by one.",
              "Day 26 (Fri) — URGENCY: 'Last chance to grab [offer] at [price]. Ends [deadline].' Direct, clear CTA.",
              "Day 27 (Sat) — VALUE STACK: 'Here's everything you get: [item 1 value], [item 2 value], [item 3 value]. Total value: $[high]. Your price: $[low].'",
              "Day 28-30 — RESULTS + RESET: Share results from the month, thank your audience, tease next month's content."]),
            ("Platform-Specific Guidelines", "Each platform rewards different content. Optimize your posts accordingly.",
             [("Instagram", ["Reels: 15-30 seconds, hook in first 2 seconds, text on screen, trending audio",
                             "Carousels: 7-10 slides, each slide = one point, last slide = CTA",
                             "Stories: 5-7 per day, mix polls/questions/behind-the-scenes"]),
              ("LinkedIn", ["Text posts: 1,200-1,500 characters, use line breaks every 1-2 sentences",
                           "Carousels (PDF): 8-12 slides, one insight per slide, branded design",
                           "Best times: Tuesday-Thursday, 8-10 AM or 12-1 PM"]),
              ("TikTok", ["Hook in first 1 second — or they swipe", "15-60 seconds for highest completion rate",
                         "Use trending sounds and hashtags — discoverability is everything"])]),
            ("Hashtag Strategy", "Use 20-30 hashtags on Instagram, 3-5 on LinkedIn, 3-4 on TikTok. Rotate sets to avoid shadow-banning.",
             ["Set A (reach): 5 hashtags with 500K-5M posts — for broad discovery",
              "Set B (niche): 10 hashtags with 10K-500K posts — for targeted audience",
              "Set C (micro): 5 hashtags with 1K-10K posts — for high engagement rate",
              "Branded hashtag: Create one unique to your brand for community tracking",
              "Rotate between 3 hashtag sets — never use the same set twice in a row"]),
            ("Analytics Tracking", "What gets measured gets improved. Track these metrics weekly.",
             ["Follower growth rate: _____% (week over week)",
              "Average engagement rate: _____% (engagements / reach x 100)",
              "Top performing post type: _____ (carousel, reel, text, image)",
              "Best posting time: _____ (based on your analytics, not generic advice)",
              "Profile visits to follower conversion: _____%",
              "Link clicks: _____ (only metric that indicates purchase intent)"])
        ])


def p9():
    generate_template_product(
        "90-Day Goal Planner", "Set, track, and achieve your biggest goals\nwith structured quarterly planning.", "90-day-goal-planner",
        ["Quarterly Vision Setting", "SMART Goal Framework", "Monthly Breakdown", "Weekly Sprint Planning",
         "Daily Priority System", "Progress Tracking Dashboard", "Obstacle & Pivot Log",
         "90-Day Review Template", "Accountability System"],
        [
            ("Quarterly Vision Setting", "Before setting goals, get clear on your vision for the next 90 days. What does success look like on Day 90?",
             ["My #1 priority this quarter: ______________________________________",
              "If I could only accomplish ONE thing in 90 days, it would be: _____",
              "This matters because: _____",
              "On Day 90, I will feel: _____",
              "The person I need to become to achieve this: _____",
              "What I'm willing to sacrifice: _____",
              "What I'm NOT willing to sacrifice: _____"]),
            ("SMART Goal Framework", "Set 3-5 goals using the SMART framework. Vague goals produce vague results.",
             ["Goal 1: _____ | Specific: [what exactly] | Measurable: [how you'll track] | Achievable: [why it's realistic] | Relevant: [why it matters now] | Time-bound: [deadline within 90 days]",
              "Goal 2: _____ | S: _____ | M: _____ | A: _____ | R: _____ | T: _____",
              "Goal 3: _____ | S: _____ | M: _____ | A: _____ | R: _____ | T: _____",
              "Lead indicators (actions you control): _____, _____, _____",
              "Lag indicators (results you measure): _____, _____, _____"]),
            ("Monthly Breakdown", "Divide each goal into 3 monthly milestones. Month 1 = foundation, Month 2 = momentum, Month 3 = completion.",
             ["Month 1 (Days 1-30) — FOUNDATION: Milestone: _____ | Key actions: 1) _____ 2) _____ 3) _____",
              "Month 2 (Days 31-60) — MOMENTUM: Milestone: _____ | Key actions: 1) _____ 2) _____ 3) _____",
              "Month 3 (Days 61-90) — COMPLETION: Milestone: _____ | Key actions: 1) _____ 2) _____ 3) _____",
              "Non-negotiable weekly actions: _____, _____, _____",
              "Resources needed: _____ | Budget: $_____ | Support from: _____"]),
            ("Weekly Sprint Planning", "Every Monday, plan your week in 15 minutes. Every Friday, review in 10 minutes.",
             ["This week's #1 outcome: _____",
              "3 tasks that move me toward my 90-day goal: 1) _____ 2) _____ 3) _____",
              "Scheduled time blocks for goal work: _____ (minimum 5 hours/week)",
              "Potential obstacles this week: _____ | Prevention plan: _____",
              "Accountability check-in: Share progress with _____ on _____",
              "Friday review: Did I hit my #1 outcome? Y/N — What caused the result?"]),
            ("Daily Priority System", "Use the 1-3-5 method: each day, commit to 1 big task, 3 medium tasks, and 5 small tasks.",
             ["THE ONE (must complete today): _____",
              "THREE medium priorities: 1) _____ 2) _____ 3) _____",
              "FIVE quick wins: 1) _____ 2) _____ 3) _____ 4) _____ 5) _____",
              "Time blocked for deep work: _____ AM/PM to _____ AM/PM",
              "End-of-day reflection: What moved the needle today? _____"]),
            ("Progress Tracking Dashboard", "Track your goals quantitatively. Feelings lie, numbers don't.",
             ["Goal 1 progress: _____% complete | On track? Y/N | Days remaining: _____",
              "Goal 2 progress: _____% complete | On track? Y/N | Days remaining: _____",
              "Goal 3 progress: _____% complete | On track? Y/N | Days remaining: _____",
              "Current pace: Ahead / On track / Behind — by how much?",
              "Weekly effort hours logged: _____ / _____ target",
              "Momentum score (1-10): _____ — What would make it a 10?"]),
            ("Obstacle & Pivot Log", "When obstacles appear, document them. Patterns in your obstacles reveal systemic issues to fix.",
             ["Date: _____ | Obstacle: _____ | Root cause: _____ | Solution: _____ | Result: _____",
              "Common obstacle categories: Time, Energy, Knowledge, Resources, External factors",
              "If an obstacle recurs 3+ times, it's not an obstacle — it's a system problem. Fix the system.",
              "Pivot decision: Is this goal still relevant? If not, what's the new target?",
              "Support needed: Who can help me overcome this? _____ | Asked? Y/N"]),
            ("90-Day Review Template", "On Day 90, spend 1 hour reviewing everything. This review informs your next 90-day sprint.",
             ["Goal 1: Achieved / Partially / Missed — Completion: _____%",
              "Goal 2: Achieved / Partially / Missed — Completion: _____%",
              "Goal 3: Achieved / Partially / Missed — Completion: _____%",
              "Biggest win: _____",
              "Biggest lesson: _____",
              "What I would do differently: _____",
              "What I will carry forward: _____",
              "Next 90-day #1 priority: _____"]),
            ("Accountability System", "Goals without accountability are just wishes. Set up your support structure before Day 1.",
             ["Accountability partner: _____ | Check-in schedule: _____ (weekly recommended)",
              "Public commitment: Share your goal with _____ by _____ (date)",
              "Reward for completion: _____ | Consequence for quitting: _____",
              "Progress sharing: Post updates on _____ every _____ (builds public accountability)",
              "Emergency contact: If I haven't worked on my goal in 3+ days, _____ will reach out to me"])
        ])


def p10():
    generate_template_product(
        "Passive Income Zero-Cost Guide", "25 Methods That Actually Work in 2026.\nNo investment required. Start today.", "passive-income-zero-cost-guide",
        ["What 'Zero Cost' Really Means", "Digital Products (Methods 1-5)", "Content Monetization (Methods 6-10)",
         "Service Arbitrage (Methods 11-15)", "Platform Leverage (Methods 16-20)", "Emerging Opportunities (Methods 21-25)",
         "Implementation Roadmap", "Revenue Tracking Template"],
        [
            ("What 'Zero Cost' Really Means", "Every method in this guide can be started with $0 in upfront investment. Your only investment is time and effort. No courses to buy, no tools to purchase, no inventory to stock.",
             ["Zero cost means zero financial risk — but NOT zero effort",
              "Most methods take 30-90 days to generate first income",
              "Start with ONE method, master it, then stack additional streams",
              "Realistic first-month income: $50-500 (not $10K — anyone promising that is lying)",
              "The compounding effect: 3 streams at $500/month = $1,500/month = $18,000/year"]),
            ("Digital Products (Methods 1-5)", "Create once, sell forever. Digital products have near-100% profit margins because there's no cost of goods.",
             ["METHOD 1 — Notion Templates: Build templates for workflows you already use. Sell on Gumroad ($9-49). Time to first sale: 2-4 weeks. Potential: $500-3,000/month.",
              "METHOD 2 — Canva Templates: Design social media templates, presentations, or planners. Sell on Etsy or Creative Market. No design degree needed — Canva is free. Potential: $300-2,000/month.",
              "METHOD 3 — Ebooks/Guides: Write a 20-40 page guide solving a specific problem. Sell for $9-27 on Gumroad. Use Google Docs (free) to write. Potential: $200-1,500/month.",
              "METHOD 4 — Prompt Packs: Curate 50-100 AI prompts for a specific profession. Package as PDF. Sell for $9-19. Growing market. Potential: $300-1,000/month.",
              "METHOD 5 — Printable Planners: Design printable planners, trackers, or journals using Canva. Sell on Etsy. Each takes 2-4 hours to create. Potential: $400-2,500/month."]),
            ("Content Monetization (Methods 6-10)", "Turn your knowledge into content, then monetize the audience.",
             ["METHOD 6 — YouTube (Ad Revenue): Create educational or entertainment videos. Monetize at 1,000 subscribers + 4,000 watch hours. Film with your phone. Edit with free tools (CapCut, DaVinci Resolve). Potential: $500-5,000/month.",
              "METHOD 7 — Newsletter Sponsorships: Start a niche newsletter using Beehiiv (free tier). Grow to 1,000+ subscribers. Sell sponsorships at $50-200 per issue. Potential: $200-2,000/month.",
              "METHOD 8 — Blog + Affiliate Links: Start a blog on WordPress.com (free) or Medium. Write SEO-optimized articles. Add affiliate links (Amazon Associates, software referrals). Potential: $100-3,000/month.",
              "METHOD 9 — Podcast Sponsorships: Start a niche podcast with your phone and Anchor (free hosting). 500+ downloads per episode attracts sponsors at $15-25 CPM. Potential: $200-1,500/month.",
              "METHOD 10 — Medium Partner Program: Write articles on Medium. Get paid based on member reading time. Best for long-form, well-researched content. Potential: $100-2,000/month."]),
            ("Service Arbitrage (Methods 11-15)", "Offer services where your time investment is minimal because you've systematized the delivery.",
             ["METHOD 11 — Social Media Management: Manage posting for 3-5 small businesses. Use free scheduling tools (Buffer free tier). Charge $300-500/month per client. Potential: $900-2,500/month.",
              "METHOD 12 — Virtual Bookkeeping: Learn basic bookkeeping (free courses on YouTube). Use Wave (free accounting software). Charge $200-500/month per client. Potential: $600-2,000/month.",
              "METHOD 13 — Email Management: Manage inboxes for busy entrepreneurs. 30 min/day per client. Charge $300-500/month. Find clients on LinkedIn. Potential: $600-1,500/month.",
              "METHOD 14 — Transcription: Transcribe audio/video using free tools (oTranscribe) with manual cleanup. Pay: $15-25/audio hour. Platforms: Rev, TranscribeMe. Potential: $300-1,200/month.",
              "METHOD 15 — Online Tutoring: Teach subjects you know on Wyzant, Preply, or Varsity Tutors. No certification required for most platforms. Rate: $20-60/hour. Potential: $400-2,000/month."]),
            ("Platform Leverage (Methods 16-20)", "Use existing platforms with built-in audiences to generate income without building your own.",
             ["METHOD 16 — Print on Demand: Design t-shirts, mugs, phone cases. Upload to Redbubble, TeePublic, or Merch by Amazon. No inventory, no shipping. Potential: $100-1,500/month.",
              "METHOD 17 — Stock Photography/Video: Take photos and videos with your smartphone. Upload to Shutterstock, Adobe Stock, Pond5. Earn royalties per download. Potential: $50-800/month.",
              "METHOD 18 — App/Play Store: Create simple utility apps using no-code tools (Thunkable, Adalo — free tiers). Monetize with ads. Potential: $100-1,000/month.",
              "METHOD 19 — Fiverr/Upwork Productized Services: Create fixed-scope service gigs (logo review, resume formatting, data entry). Price at $5-50 per gig. Scale with templates. Potential: $300-2,000/month.",
              "METHOD 20 — Amazon KDP: Write and publish ebooks or low-content books (journals, planners) on Amazon KDP. Free to publish. Amazon handles printing and shipping. Potential: $200-3,000/month."]),
            ("Emerging Opportunities (Methods 21-25)", "These methods are newer and less saturated. Early movers have an advantage.",
             ["METHOD 21 — AI Service Provider: Offer AI-powered services (content writing, image generation, data analysis) to businesses that haven't adopted AI yet. Your edge: you know how to use the tools, they don't. Potential: $500-3,000/month.",
              "METHOD 22 — UGC (User-Generated Content) Creator: Brands pay $50-300 per video for authentic product reviews. No follower count needed. Sign up on platforms like Billo, JoinBrands, or pitch directly. Potential: $500-3,000/month.",
              "METHOD 23 — Community Management: Run Discord servers or online communities for creators and brands. Charge $500-1,500/month per community. Potential: $500-3,000/month.",
              "METHOD 24 — Data Labeling/AI Training: Help train AI models by labeling data. Platforms: Scale AI, Appen, Toloka. Rates: $10-25/hour. Flexible schedule. Potential: $200-1,000/month.",
              "METHOD 25 — Micro-Consulting: Offer 30-minute expert calls on Clarity.fm, Intro.co, or your own Calendly. Charge $50-200 per call based on expertise. Potential: $300-2,000/month."]),
            ("Implementation Roadmap", "Don't start 5 methods at once. Follow this phased approach for maximum success.",
             ["Week 1: Choose your top 2 methods based on your skills, interests, and available time",
              "Week 2-3: Set up Method #1 completely. Create your first product or listing.",
              "Week 4-6: Promote Method #1. Get your first sale or client. Document what works.",
              "Week 7-8: Set up Method #2 while maintaining Method #1.",
              "Week 9-12: Optimize both methods. Double down on what's generating income.",
              "Month 4+: Add Method #3 only after Methods #1 and #2 are generating consistent income.",
              "Golden rule: Revenue from existing methods funds growth of new methods."]),
            ("Revenue Tracking Template", "Track every dollar earned from every method. Monthly review shows you where to focus.",
             ["Method: _____ | Month 1: $_____ | Month 2: $_____ | Month 3: $_____ | Trend: Up/Flat/Down",
              "Method: _____ | Month 1: $_____ | Month 2: $_____ | Month 3: $_____ | Trend: Up/Flat/Down",
              "Method: _____ | Month 1: $_____ | Month 2: $_____ | Month 3: $_____ | Trend: Up/Flat/Down",
              "Total passive income: $_____ /month | Hours invested: _____ /month",
              "Effective hourly rate: $_____ (total income / total hours)",
              "Target: $_____ /month by _____ (date) | On track? Y/N",
              "Next action: Scale _____ method because _____ (highest ROI on time invested)"])
        ])


if __name__ == "__main__":
    print("Generating 10 Gumroad product PDFs...")
    print("=" * 50)
    p1()
    p2()
    p3()
    p4()
    p5()
    p6()
    p7()
    p8()
    p9()
    p10()
    print("=" * 50)
    print("All 10 PDFs generated in data/gumroad/products/")

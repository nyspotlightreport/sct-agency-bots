import json

agencies = [
    {
        "id": "content-studio", "name": "Content Creation Studio", "icon": "\U0001f4dd",
        "tagline": "30 SEO blog posts, articles, and guides every month in your brand voice",
        "description": "Our AI content team produces research-backed, keyword-optimized blog posts, articles, and long-form guides that drive organic traffic and establish your authority.",
        "litePrice": 67, "fullPrice": 297, "dayPass": 29.97,
        "replaceCost": "$2,000-$4,000/mo", "replaceLabel": "Freelance content writers", "traditionalCost": 3000,
        "liteFeatures": ["8 blog posts/month", "Basic SEO optimization", "Standard templates", "Email support", "48-hour turnaround"],
        "fullFeatures": ["30 blog posts/month", "Advanced SEO + keyword research", "Custom brand voice profile", "Content calendar", "Unlimited revisions", "Priority publishing", "Long-form guides (2,000+ words)", "Internal linking strategy", "Dedicated strategist", "Weekly performance reports"],
        "deliverables": [
            {"name": "SEO Blog Posts", "lite": "8/month", "full": "30/month", "desc": "Keyword-optimized articles in your brand voice"},
            {"name": "SEO Optimization", "lite": "Basic meta tags", "full": "Full keyword strategy", "desc": "On-page SEO for every piece"},
            {"name": "Content Calendar", "lite": "Monthly outline", "full": "Detailed 30-day plan", "desc": "Planned topics with dates and keywords"},
            {"name": "Brand Voice", "lite": "Standard tone", "full": "Custom voice profile", "desc": "Consistent tone across all content"},
            {"name": "Revisions", "lite": "1 per post", "full": "Unlimited", "desc": "Refine until perfect"},
            {"name": "Long-Form Guides", "lite": "Not included", "full": "4/month", "desc": "2,000+ word comprehensive guides"},
            {"name": "Performance Reports", "lite": "Monthly", "full": "Weekly detailed", "desc": "Traffic, rankings, and engagement"}
        ],
        "faq": [
            {"q": "How quickly do I get my first content?", "a": "Within 48 hours of onboarding."},
            {"q": "Can I review before it publishes?", "a": "Yes. Approve each piece or enable auto-publish."},
            {"q": "What if it doesn't match my voice?", "a": "We refine your brand profile until every piece sounds like you. FULL includes unlimited revisions."},
            {"q": "Do you publish to WordPress?", "a": "Yes. Content is formatted and published directly to your CMS."},
            {"q": "What topics do you cover?", "a": "Any topic in your industry. We research keywords and create a strategy for your niche."}
        ],
        "sampleOutput": "10 AI Tools Every Entrepreneur Needs in 2026 - 1,847 words, SEO score 94/100, published to WordPress with meta tags."
    },
    {
        "id": "social-media", "name": "Social Media Management", "icon": "\U0001f4f1",
        "tagline": "Daily posts on 6 platforms with engagement tracking and hashtag strategy",
        "description": "Complete social media management across LinkedIn, Twitter/X, Instagram, Facebook, Pinterest, and TikTok with platform-specific content and analytics.",
        "litePrice": 67, "fullPrice": 297, "dayPass": 29.97,
        "replaceCost": "$1,500-$3,000/mo", "replaceLabel": "Social media agency", "traditionalCost": 2000,
        "liteFeatures": ["3 platforms", "15 posts/month", "Basic scheduling", "Monthly analytics", "Standard hashtags"],
        "fullFeatures": ["6 platforms", "90+ posts/month", "AI-optimized timing", "Weekly analytics", "Custom hashtag strategy", "Engagement tracking", "Carousels and Reels", "Social listening", "Competitor analysis", "Content repurposing"],
        "deliverables": [
            {"name": "Social Posts", "lite": "15/month", "full": "90+/month", "desc": "Platform-native posts for each channel"},
            {"name": "Platforms", "lite": "3 platforms", "full": "6 platforms", "desc": "Full presence across major channels"},
            {"name": "Scheduling", "lite": "Standard times", "full": "AI-optimized times", "desc": "Posts when your audience is active"},
            {"name": "Hashtags", "lite": "Basic tags", "full": "Researched strategy", "desc": "Maximize discoverability"},
            {"name": "Analytics", "lite": "Monthly", "full": "Weekly", "desc": "Engagement and growth metrics"},
            {"name": "Visual Content", "lite": "Text only", "full": "Carousels + Reels + Stories", "desc": "Rich media formats"}
        ],
        "faq": [
            {"q": "Which platforms?", "a": "LinkedIn, Twitter/X, Instagram, Facebook, Pinterest, TikTok."},
            {"q": "Do you create images?", "a": "FULL includes custom graphics and video content."},
            {"q": "Can I approve posts?", "a": "Yes, or enable auto-publish."},
            {"q": "Platform-specific content?", "a": "Each post is adapted for the platform style."},
            {"q": "Do you respond to comments?", "a": "FULL includes engagement monitoring."}
        ],
        "sampleOutput": "LinkedIn thought piece: 2,400 impressions, 89 likes, 12 comments in 48 hours."
    },
    {
        "id": "seo", "name": "SEO Agency", "icon": "\U0001f50d",
        "tagline": "Technical audits, keyword research, on-page optimization, and rank tracking",
        "description": "Comprehensive SEO that drives organic traffic. Technical audits, keyword strategy, on-page optimization, and rank tracking.",
        "litePrice": 57, "fullPrice": 247, "dayPass": 29.97,
        "replaceCost": "$500-$2,000/mo", "replaceLabel": "SEO consultant", "traditionalCost": 1500,
        "liteFeatures": ["Monthly audit", "5 keywords tracked", "Basic on-page", "Monthly report", "Meta optimization"],
        "fullFeatures": ["Weekly audits", "25+ keywords", "Full technical SEO", "Weekly tracking", "Backlink analysis", "Competitor gaps", "Schema markup", "Speed optimization", "Internal linking", "Search Console management"],
        "deliverables": [
            {"name": "Site Audits", "lite": "Monthly", "full": "Weekly", "desc": "Technical health checks"},
            {"name": "Keywords", "lite": "5 tracked", "full": "25+ tracked", "desc": "Monitor target search terms"},
            {"name": "On-Page SEO", "lite": "Meta tags", "full": "Full optimization", "desc": "Titles, descriptions, headers, schema"},
            {"name": "Backlinks", "lite": "Not included", "full": "Monthly report", "desc": "Link profile monitoring"},
            {"name": "Competitors", "lite": "Not included", "full": "Gap reports", "desc": "Find ranking opportunities"},
            {"name": "Reports", "lite": "Monthly PDF", "full": "Weekly dashboard", "desc": "Rankings and traffic impact"}
        ],
        "faq": [
            {"q": "How long for results?", "a": "Most see improvements within 60-90 days."},
            {"q": "Do you build backlinks?", "a": "We focus on on-page. Backlink analysis included in FULL."},
            {"q": "Which tools?", "a": "Ahrefs, Google Search Console, and proprietary AI tools."},
            {"q": "Local SEO?", "a": "Google Business Profile included in FULL."},
            {"q": "Technical issues?", "a": "Our audits identify problems with actionable fixes."}
        ],
        "sampleOutput": "Client moved from page 3 to position 4 for target keyword in 8 weeks. Organic traffic up 340%."
    }
]

# Template for remaining 12 agencies
remaining_data = [
    ("email-marketing", "Email & Newsletter Agency", "\u2709\ufe0f", "Weekly newsletters, drip campaigns, list management, and A/B testing",
     "End-to-end email marketing from newsletters to drip campaigns to list segmentation.",
     47, 197, 24.97, "$400-$1,500/mo", "Email marketing firm", 800,
     ["2 newsletters/month", "Basic templates", "List management", "Open rate tracking", "Standard sequences"],
     ["4+ newsletters/month", "Custom templates", "Advanced segmentation", "A/B testing", "Drip campaigns", "Behavioral triggers", "List growth strategy", "Detailed analytics", "Subscriber management", "Deliverability optimization"]),
    ("marketing", "Marketing Agency", "\U0001f4c8", "Full-funnel strategy, campaign management, and performance analytics",
     "A complete marketing department. Strategy, campaigns, content, ads, analytics managed by AI.",
     97, 397, 39.97, "$3,000-$8,000/mo", "Marketing agency", 5000,
     ["Basic marketing plan", "Monthly campaign", "Standard analytics", "Email support", "Quarterly review"],
     ["Comprehensive strategy", "Weekly campaigns", "Multi-channel execution", "Real-time analytics", "Ad creatives", "Landing pages", "CRO", "Competitor intel", "Monthly calls", "Custom KPI dashboard"]),
    ("sales-team", "Full Cycle Sales Team", "\U0001f4bc", "Lead gen, outreach, qualification, demos, proposals, and pipeline management",
     "Complete AI sales operation from cold outreach to closed deals.",
     97, 497, 49.97, "$5,000-$15,000/mo", "Sales team", 8000,
     ["100 outreach emails/month", "Basic lead list", "Standard sequences", "Pipeline tracking", "Monthly report"],
     ["500+ outreach emails/month", "AI-qualified leads", "Multi-touch sequences", "Auto demo scheduling", "Proposals", "CRM integration", "Pipeline management", "Win/loss analysis", "Weekly reviews", "Apollo + HubSpot"]),
    ("customer-service", "Customer Service Provider", "\U0001f3a7", "24/7 AI support agents, ticket management, and satisfaction tracking",
     "Always-on support that never sleeps. AI agents handle inquiries and resolve issues 24/7.",
     67, 297, 29.97, "$2,000-$5,000/mo", "Customer service department", 3000,
     ["Business hours", "Email only", "Basic tickets", "Monthly CSAT", "Standard responses"],
     ["24/7 coverage", "Email + chat + phone", "Advanced routing", "Real-time CSAT", "Custom responses", "Escalation management", "Knowledge base", "Multilingual", "SLA tracking", "Feedback loops"]),
    ("voice-ai", "Voice AI & Appointment Setting", "\U0001f4de", "AI receptionist, sales bots, appointment booking, and call analytics",
     "Never miss a call. AI receptionist answers 24/7, qualifies callers, books appointments.",
     57, 247, 29.97, "$1,500-$3,000/mo", "Receptionist service", 2000,
     ["Business hours", "Basic routing", "Voicemail transcription", "Monthly report", "Standard greeting"],
     ["24/7 receptionist", "AI sales bot", "AI support bot", "Appointment scheduling", "Call analytics", "Custom voice", "CRM logging", "Lead scoring", "SMS follow-ups", "Multi-department routing"]),
    ("pr", "PR Agency", "\U0001f4f0", "Press releases, media outreach, reputation monitoring, and crisis management",
     "Professional PR powered by AI. Press releases, media outreach, brand monitoring.",
     67, 297, 29.97, "$3,000-$10,000/mo", "PR firm", 5000,
     ["2 press releases/month", "Basic media list", "Monthly mentions", "Standard distribution", "Email support"],
     ["8+ press releases/month", "Targeted outreach", "Real-time monitoring", "Crisis response", "Journalist database", "Social listening", "Thought leadership", "Award submissions", "Media training", "Weekly reports"]),
    ("hr", "HR, Hiring & Compliance", "\U0001f465", "Job postings, candidate screening, onboarding, and compliance tracking",
     "Streamline HR. Job descriptions, candidate screening, onboarding docs, compliance.",
     57, 247, 29.97, "$1,000-$4,000/mo", "HR outsourcing", 2000,
     ["5 job postings/month", "Basic screening", "Standard letters", "Monthly compliance", "Templates"],
     ["Unlimited postings", "AI screening + ranking", "Custom onboarding", "Continuous compliance", "Handbook generation", "Policy docs", "Background checks", "Benefits admin", "Review templates", "HR analytics"]),
    ("executive-assistant", "Executive & Personal Assistant", "\U0001f5d3\ufe0f", "Calendar, email triage, research, travel planning, and briefings",
     "AI executive assistant handles email, calendar, meeting prep, research, and travel.",
     47, 197, 24.97, "$1,500-$3,500/mo", "Virtual assistant", 2500,
     ["Basic email sorting", "Calendar scheduling", "Weekly briefing", "Simple research", "Reminders"],
     ["Advanced email triage", "Smart calendar optimization", "Daily briefings", "Deep research", "Travel planning", "Meeting prep", "Doc summarization", "Priority inbox", "Expense reports", "Communication drafts"]),
    ("web-development", "Website Development Agency", "\U0001f310", "Full-stack builds, landing pages, e-commerce, hosting, and maintenance",
     "Complete website development and management. Landing pages to full e-commerce stores.",
     97, 497, 49.97, "$3,000-$10,000/mo", "Web development agency", 5000,
     ["1 landing page/month", "Basic maintenance", "Standard templates", "SSL + hosting", "Monthly backup"],
     ["Unlimited pages", "Custom design", "E-commerce", "Performance optimization", "A/B testing", "Analytics", "SEO-optimized", "Mobile-first", "API integrations", "24/7 uptime"]),
    ("app-development", "Mobile & Desktop App Agency", "\U0001f4f2", "Native and cross-platform app development, UI/UX design, and deployment",
     "Full-service app development for iOS, Android, and desktop with ongoing maintenance.",
     97, 497, 49.97, "$5,000-$25,000/mo", "App development firm", 10000,
     ["Basic prototype", "Standard UI", "Single platform", "Monthly updates", "Bug fixes"],
     ["Full development", "Custom UI/UX", "Cross-platform", "Backend APIs", "App Store submission", "Push notifications", "Analytics", "Continuous deployment", "Performance monitoring", "Feature roadmap"]),
    ("content-strategy", "Content Strategy & Posting", "\U0001f5fa\ufe0f", "Editorial calendars, content audits, competitive analysis, and publishing workflows",
     "Strategic content planning aligned with business goals. Audit, plan, schedule, optimize.",
     57, 247, 29.97, "$2,000-$5,000/mo", "Content strategist", 3000,
     ["Monthly audit", "Basic calendar", "3 themes", "Standard publishing", "Monthly review"],
     ["Weekly audits", "Detailed calendar", "Unlimited themes", "Multi-channel publishing", "Competitive analysis", "Content gaps", "Repurposing", "Performance optimization", "Trend monitoring", "Strategy sessions"]),
    ("creative-studio", "Image & Creative Studio", "\U0001f3a8", "HD images, social graphics, ad creatives, brand assets, and design systems",
     "Professional visual content on demand. HD images, graphics, creatives in your brand style.",
     47, 197, 24.97, "$1,500-$4,000/mo", "Design agency", 2500,
     ["10 HD images/month", "Basic graphics", "Standard sizes", "PNG/JPG", "Email support"],
     ["50+ HD images/month", "Custom graphics", "Ad creatives", "Brand asset library", "All formats", "Design system", "Video thumbnails", "Infographics", "Presentations", "Unlimited revisions"]),
]

for r in remaining_data:
    agencies.append({
        "id": r[0], "name": r[1], "icon": r[2], "tagline": r[3], "description": r[4],
        "litePrice": r[5], "fullPrice": r[6], "dayPass": r[7],
        "replaceCost": r[8], "replaceLabel": r[9], "traditionalCost": r[10],
        "liteFeatures": r[11], "fullFeatures": r[12],
        "deliverables": [{"name": f, "lite": "Limited", "full": "Full access", "desc": f} for f in r[12][:7]],
        "faq": [
            {"q": "How quickly can I start?", "a": "Most clients are running within 24-48 hours."},
            {"q": "Can I upgrade LITE to FULL?", "a": "Yes, upgrade instantly. Price difference is prorated."},
            {"q": "What about day passes?", "a": "Full access for 24 hours, no commitment needed."},
            {"q": "Any contracts?", "a": "No contracts. Cancel anytime with one click."},
            {"q": "Quality vs hiring a firm?", "a": "Enterprise-grade output at a fraction of the cost, with faster turnaround."}
        ],
        "sampleOutput": f"Enterprise-grade {r[1].lower()} deliverables within 48 hours of onboarding."
    })

with open("C:/Users/S/sct-agency-bots/data/agencies.json", "w", encoding="utf-8") as f:
    json.dump(agencies, f, indent=2, ensure_ascii=False)

print(f"Created agencies.json with {len(agencies)} agencies")
for a in agencies:
    print(f"  {a['id']}: LITE ${a['litePrice']}/mo, FULL ${a['fullPrice']}/mo, Day ${a['dayPass']}")

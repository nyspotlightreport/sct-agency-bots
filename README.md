# 🎭 SCT Agency Bot System — NY Spotlight Report

**The fully autonomous AI agency operating at nyspotlightreport.com**

---

## 🚀 LIVE SYSTEM STATUS

| Component | Status | Details |
|-----------|--------|---------|
| Website | ✅ LIVE | nyspotlightreport.com — auto-updating news |
| Active Workflows | ✅ 20 active | All running on schedule |
| Total Bots | ✅ 37 bots | 8 new income bots added |
| GitHub Secrets | ✅ 24 configured | + 13 new ones to configure |
| Stripe Products | ✅ 5 live | Payment links active |
| HubSpot CRM | ✅ Connected | 7 prospects loaded |

---

## 📊 INCOME STREAMS (Active + Pending)

### ✅ Currently Running
| Stream | Bot | Est. Monthly |
|--------|-----|-------------|
| Newsletter subscriptions | social_poster_bot + stripe | $9.99/mo per sub |
| Content packages | stripe_revenue_bot | $29.99/mo |
| Consulting sessions | stripe_revenue_bot | $150/session |
| Bot system licenses | stripe_revenue_bot | $49.99/mo |
| Press releases | stripe_revenue_bot | $299/release |

### 🆕 New Bots (Need API Keys)
| Stream | Bot | Est. Monthly | Keys Needed |
|--------|-----|-------------|-------------|
| Newsletter + sponsorships | beehiiv_newsletter_bot | $500-5k | BEEHIIV_API_KEY |
| Lead generation | google_maps_scraper_bot | $500-5k | GOOGLE_MAPS_API_KEY |
| YouTube AdSense | youtube_shorts_bot | $100-5k | (uses existing keys) |
| 10x social reach | multiplatform_poster_bot | brand deals | REDDIT_CLIENT_* |
| Passive bandwidth | bandwidth_income_bot | $20-100 | HONEYGAIN_EMAIL/PASS |
| Email outreach | email_sequence_bot | $500-20k | (uses Gmail) |
| Events content | events_scraper_bot | SEO traffic | TICKETMASTER_API_KEY |
| Book royalties | kdp_full_pipeline_bot | $500-10k | (uses Anthropic) |

---

## 🤖 COMPLETE BOT INVENTORY (37 bots)

### Infrastructure
- `agency_core.py` — Base framework, alerts, state management
- `agency_command_center.py` — Master orchestrator

### Operations
- `weekly_report_bot.py` / `v2` — Monday 8am KPI digest
- `inbox_triage_bot.py` — Daily Gmail triage
- `invoice_bot.py` — Payment reminders
- `meeting_notes_bot.py` — Notes → HubSpot

### Marketing & Content
- `social_poster_bot.py` — Publer social posting
- `youtube_shorts_bot.py` 🆕 — Daily Shorts scripts + Publer
- `multiplatform_poster_bot.py` 🆕 — LinkedIn/Twitter/Reddit simultaneous
- `campaign_orchestrator_bot.py` — Full campaign management
- `content_repurpose_bot.py` — 1 input → 5 platform variants
- `content_calendar_bot.py` — Monthly calendar builder
- `news_digest_bot.py` — Daily news content
- `beehiiv_newsletter_bot.py` 🆕 — Daily newsletter pipeline

### Intelligence & Monitoring
- `uptime_monitor_bot.py` — Site uptime every 15min
- `seo_rank_tracker_bot.py` — Ahrefs Mon+Thu
- `competitor_monitor_bot.py` — Weekly competitor tracking
- `mention_monitor_bot.py` — Brand mentions every 4h
- `reddit_monitor_bot.py` — Reddit every 6h
- `web_monitor_agent.py` — Page change detection
- `github_mcp_bot.py` — Workflow health every 30min
- `self_improvement_bot.py` — Weekly system review
- `events_scraper_bot.py` 🆕 — Daily NYC events

### Revenue
- `stripe_revenue_bot.py` — Daily revenue tracking
- `affiliate_tracker_bot.py` — 25+ affiliate programs (v3)
- `lead_pipeline_bot.py` — Apollo → HubSpot weekly
- `google_maps_scraper_bot.py` 🆕 — NYC lead scraping weekly
- `email_sequence_bot.py` 🆕 — Daily outbound sequences
- `alpha_vantage_bot.py` — Daily market data
- `bandwidth_income_bot.py` 🆕 — Passive income monitor

### Passive Income
- `kdp_book_generator.py` — Book outlines
- `kdp_full_pipeline_bot.py` 🆕 — Full book → publish pipeline
- `promptbase_seller_bot.py` — AI prompt packs
- `github_sponsors_setup.py` — Sponsor buttons

### Utilities
- `rag_memory_bot.py` — ChromaDB long-term memory
- `image_generator_bot.py` — GPT image generation

---

## ⚙️ WORKFLOW SCHEDULE (20 active)

| Time | Workflow |
|------|----------|
| Every 15 min | Uptime Monitor |
| Every 30 min | GitHub Monitor |
| Every 2 hours | Bandwidth Income Monitor |
| Every 4 hours | Mention Monitor |
| Every 6 hours | Reddit Monitor |
| Daily 5am ET | Events Scraper |
| Daily 6am ET | YouTube Shorts Bot |
| Daily 7am ET | Daily Operations (Gmail triage) |
| Daily 7am ET | News Digest |
| Daily 8am ET | Stripe Revenue |
| Daily 8am ET | Email Sequences |
| Daily 8am ET | Alpha Vantage Market Data |
| Daily 9am ET | Beehiiv Newsletter |
| Daily 10am ET | Multi-Platform Poster |
| Daily 4pm ET | Multi-Platform (afternoon) |
| Mon+Thu | SEO Monitor |
| Monday 9am | Affiliate Tracker (25+ programs) |
| Tuesday noon | Lead Pipeline |
| Wednesday 9am | KDP Book Generator |
| Sunday 10am | Google Maps Lead Scraper |
| Sunday 11pm | Competitor Monitor |
| Sunday | Self-Improvement Engine |
| Monday 8am | Weekly KPI Report |
| On push | Deploy Site to Netlify |

---

## 🔑 SECRETS TO CONFIGURE (13 new)

These are needed to activate new bots. All bots run gracefully without them.

| Secret Name | Where to Get | Priority |
|-------------|--------------|----------|
| BEEHIIV_API_KEY | beehiiv.com → Settings → API | HIGH |
| BEEHIIV_PUB_ID | beehiiv.com → Publication ID | HIGH |
| GOOGLE_MAPS_API_KEY | console.cloud.google.com → Places API | HIGH |
| TICKETMASTER_API_KEY | developer.ticketmaster.com (free) | MEDIUM |
| EVENTBRITE_API_KEY | eventbrite.com/platform (free) | MEDIUM |
| GUARDIAN_API_KEY | open-platform.theguardian.com (free) | MEDIUM |
| REDDIT_CLIENT_ID | reddit.com/prefs/apps (free) | MEDIUM |
| REDDIT_CLIENT_SECRET | reddit.com/prefs/apps | MEDIUM |
| REDDIT_USERNAME | Your Reddit username | MEDIUM |
| REDDIT_PASSWORD | Your Reddit password | MEDIUM |
| HONEYGAIN_EMAIL | honeygain.com account email | LOW |
| HONEYGAIN_PASS | honeygain.com account password | LOW |
| EARNAPP_API_KEY | earnapp.com → settings | LOW |

---

## 💡 AFFILIATE PORTFOLIO (25+ programs in v3)

Categories: Newsletter, AI Tools, Social, Bandwidth Sharing, Hosting, SEO, Design, Publishing, Education, DePIN

**Highest Priority:**
- Beehiiv (25-50% recurring)
- ElevenLabs (22% recurring)  
- Publer (25% recurring — our own tool)
- Honeygain referrals ($5/signup + 10% of earnings)
- Grass/Nodepay DePIN (token upside)

---

## 🌐 SITE FEATURES (nyspotlightreport.com)

- ✅ Auto-updating news (32+ real articles, Guardian + NewsAPI)
- ✅ Entertainment stocks ticker (DIS, NFLX, PARA, AMC, WBD, SPOT, LYV)
- ✅ Market open/closed status indicator
- ✅ Newsletter signup → HubSpot CRM
- ✅ Full SEO package (OG, Twitter cards, JSON-LD schema)
- ✅ Personalization engine (tracks reader preferences)
- ✅ Social proof ticker
- ✅ 8-minute auto-refresh
- ⏳ Claude editorial copy (activates once Anthropic spend limit raised)

---

## 🔥 NEXT ACTIONS (Priority Order)

1. **TODAY**: Raise Anthropic spend limit → console.anthropic.com/settings/limits → $5
2. **TODAY**: Add GUARDIAN_API_KEY to GitHub secrets (get free key at open-platform.theguardian.com)
3. **THIS WEEK**: Sign up for Beehiiv → add API keys → newsletter starts auto-publishing
4. **THIS WEEK**: Get Google Maps API key (free $200/mo credit) → leads start flowing
5. **OPTIONAL**: Set up money4band Docker → $30-80/mo passive immediately

---

*Generated by SCT Agency Bot System — Updated automatically*

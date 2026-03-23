# ProFlow Platform Architecture
## Enterprise SaaS Product — NY Spotlight Report

### Product: ProFlow AI Content Engine
- **Web Dashboard**: nyspotlightreport.com/portal/ (React app)
- **Desktop App**: PWA installable via Chrome/Edge (manifest.json + sw.js)
- **Mobile App**: PWA installable on iOS/Android (same manifest)
- **API**: Netlify Functions (REST)

### White-Labeled Services (Replacing 3rd Party)
| ProFlow Service | Replaces | Monthly Savings | Status |
|----------------|----------|----------------|--------|
| ProFlow Content Engine | Jasper ($49), Copy.ai ($49) | $98/mo | BUILT |
| ProFlow Social Studio | Publer ($12), Hootsuite ($49) | $61/mo | BUILT |
| ProFlow SEO Monitor | Ahrefs Lite ($29) | $29/mo | PARTIAL |
| ProFlow Lead Finder | Apollo ($49) | $49/mo | BUILT (Vibe Prospecting) |
| ProFlow CRM | HubSpot Starter ($20) | $20/mo | BUILT (Supabase) |
| ProFlow Newsletter | ConvertKit ($29) | $29/mo | BUILT (Beehiiv free) |
| ProFlow Analytics | Databox ($49) | $49/mo | BUILT |
| ProFlow Watchdog | UptimeRobot ($7) | $7/mo | BUILT |
| **TOTAL SAVINGS** | | **$342/mo per customer** | |

### Customer Experience Flow
1. Customer signs up at nyspotlightreport.com/proflow/
2. Stripe processes payment → webhook fires
3. Welcome email sends (nodemailer via Gmail)
4. Customer portal account created (Supabase)
5. Content engine configured for their niche (Claude API)
6. First content batch published within 48 hours
7. Customer logs into portal to see their dashboard
8. Daily content published automatically
9. Weekly performance reports emailed
10. Monthly strategy review

### Upsell Architecture
- Starter ($97) → Growth upsell shown in portal sidebar
- Growth ($297) → Agency upsell + add-on cards
- In-portal upsells: Video Pack (+$100), Lead Gen (+$200), SEO Boost (+$150)
- Upgrade button in nav, settings, and gated feature pages
- Email upsell sequences at day 7, day 14, day 30

### Revenue Model
- Customer pays $97-$497/mo
- ~10% covers tool costs (API calls, infrastructure)
- ~90% is profit
- Upsell add-ons pure margin

### Tech Stack (All Owned/Free)
- Frontend: Static HTML/CSS/JS on Netlify (free)
- Backend: Netlify Functions (free tier)
- Database: Supabase (free tier)
- AI: Anthropic Claude API (pay per use ~$20/mo)
- Email: Gmail SMTP (free)
- Payments: Stripe (2.9% + 30¢ per tx)
- CI/CD: GitHub Actions (free)
- Monitoring: Ultra Watchdog (self-built)
- Domain: nyspotlightreport.com (owned)

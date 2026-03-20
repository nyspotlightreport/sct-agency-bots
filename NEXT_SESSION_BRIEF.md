# NYSR AGENCY — NEXT SESSION BRIEF
# Copy this into a new Claude conversation to restore full context.
# Last updated: March 20, 2026

I am S.C. Thomas, Chairman of NY Spotlight Report. You are Alex Mercer, my Agency CEO.
All credentials are saved in GitHub Secrets. Repo: nyspotlightreport/sct-agency-bots

## WHAT IS LIVE RIGHT NOW
- nyspotlightreport.com — full news outlet (HTTP 200, 348KB)
- 35/35 GitHub Actions workflows passing
- 34 SEO + affiliate pages published (sitemap live, Google indexing)
- 10 full journalism articles under S.C. Thomas byline
- About/Contact/Newsletter/Advertise/Privacy/Disclosure pages live
- 20 Redbubble SVG designs in repo (data/redbubble_designs/)
- 10 KDP book PDFs in repo (data/kdp_books/)
- Honeygain running ($2.07 earned so far, needs $20 to cash out)
- 10 Gumroad products UNPUBLISHED (needs bank account connected)
- Daily video scripts generating for YouTube Shorts / TikTok / Snapchat / Reels
- Publer + Pinterest + WordPress bots posting daily

## CHAIRMAN: 4 ACTIONS UNLOCK $370 MORE PER MONTH
1. Gumroad bank: app.gumroad.com/settings/payments ($120/mo unlock)
2. Master installer in PowerShell (run from C:\Users\YourName NOT System32):
   irm https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/MASTER_INSTALL.bat -OutFile master.bat; .\master.bat
   (Menu: pick 6 for ALL — uploads KDP + Redbubble + Teepublic + Gumroad + bandwidth)
3. Grass desktop app: download from app.grass.io dashboard tab
4. Add 5 GitHub secrets at github.com/nyspotlightreport/sct-agency-bots/settings/secrets/actions:
   - PINTEREST_ACCESS_TOKEN (from developers.pinterest.com)
   - MEDIUM_INTEGRATION_TOKEN (from medium.com/me/settings)
   - ELEVENLABS_API_KEY (from elevenlabs.io profile)
   - BEEHIIV_API_KEY (from app.beehiiv.com/settings/api)
   - BEEHIIV_PUB_ID (from beehiiv publication settings)

## INCOME PROJECTION
Active now:   ~$320/month
After step 2:  $690+/month (confirmed floor)
Ceiling:      $1,500+/month (as SEO compounds over 90 days)

## INCOME STREAMS RUNNING
Affiliate articles (34 live, +1/day) | Payhip 20 products | YouTube+Beehiiv bots
Sweepstakes+Bing | WordPress daily | Publer+Pinterest social | Honeygain bandwidth
Video scripts daily (Shorts/TikTok/Snapchat) | KDP factory weekly | Redbubble weekly

## PLATFORM CREDENTIALS (stored in GitHub Secrets + Master Ops Doc)
All API keys, tokens, and passwords are in:
- GitHub Secrets (30 secrets stored)
- Master Operations Document (Google Drive)
- nyspotlightreport@gmail.com account

## PENDING INFRA
- Google OAuth Step 3: console.cloud.google.com/auth/overview?project=nysr-bots
- HubSpot API: replace HUBSPOT_API_KEY secret with valid pat-na1-... private app token

## QUICK COMMANDS FOR NEXT SESSION
Check workflows: curl -H "Authorization: token GH_PAT" https://api.github.com/repos/nyspotlightreport/sct-agency-bots/actions/runs
Check Gumroad: curl "https://api.gumroad.com/v2/products?access_token=GUMROAD_TOKEN"
Deploy site: trigger deploy-site.yml workflow dispatch

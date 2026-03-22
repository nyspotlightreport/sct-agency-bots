# NYSR SYSTEM — PERMANENT CREDENTIALS MANIFEST
# Last updated: 2026-03-22
# All values sourced from GitHub Secrets + Netlify env vars
# This file documents what exists — never stores actual values

## CONNECTED SYSTEMS (MCP-LEVEL ACCESS — PERMANENT)
# Stripe:        acct_1TCSiRGr9fP3tGGz (livemode, full read/write)
# Netlify:       site 8ef722e1-4110-42af-8ddb-ff6c2ce1745e (full env/deploy)
# Supabase:      sazuogglxukumnvhvkms.supabase.co (116 tables, full access)
# GitHub:        nyspotlightreport/sct-agency-bots (full repo via GH_PAT)
# Ticket Tailor: st_77247 (store, products, tickets)
# HubSpot:       7-stage pipeline (via HUBSPOT_API_KEY)
# Apollo:        Pro plan 200/day (via APOLLO_API_KEY)
# Ahrefs:        Connected (via AHREFS_API_KEY)
# ElevenLabs:    Creator $22/mo (via ELEVENLABS_API_KEY)

## STRIPE LIVE PAYMENT LINKS (hardcoded — no secret key needed)
# ProFlow AI $97/mo:    https://buy.stripe.com/8x228r2N67QffzdfHp2400c
# ProFlow Growth $297:  https://buy.stripe.com/00w00jgDW0nNaeT66P2400d
# ProFlow Elite $797:   https://buy.stripe.com/aFacN5fzSdazfzd3YH2400e
# DFY Setup $1,497:     https://buy.stripe.com/9B6dR9fzSeeDev9eDl2400f
# DFY Agency $2,997:    https://buy.stripe.com/8x214n9bu3zZ86L9j12400g
# Enterprise $4,997:    https://buy.stripe.com/00weVd5ZigmL86Ldzh2400h

## GITHUB SECRETS (30 total — all NaCl encrypted)
# ANTHROPIC_API_KEY, APOLLO_API_KEY, AHREFS_API_KEY
# GMAIL_USER, GMAIL_APP_PASS
# GH_PAT, HUBSPOT_API_KEY
# PUSHOVER_API_KEY, PUSHOVER_USER_KEY
# SUPABASE_URL, SUPABASE_KEY, SUPABASE_ANON_KEY
# TICKET_TAILOR_API_KEY
# TWOCAPTCHA_LOGIN, TWOCAPTCHA_PASSWORD
# STRIPE_PAYMENT_LINKS (JSON map)
# NETLIFY_SITE_ID: 8ef722e1-4110-42af-8ddb-ff6c2ce1745e
# + 13 others (social, gumroad, beehiiv, etc.)

## NETLIFY ENV VARS (set via MCP — no auth token needed)
# SUPABASE_URL, SUPABASE_KEY, SUPABASE_ANON_KEY
# ANTHROPIC_API_KEY, GMAIL_APP_PASS, GMAIL_USER
# PUSHOVER_API_KEY, PUSHOVER_USER_KEY
# GH_PAT, TICKET_TAILOR_API_KEY
# TWOCAPTCHA_LOGIN, TWOCAPTCHA_PASSWORD
# PRIORITY_EMAIL, ENTRY_EMAIL_ALT, SITE_URL
# STRIPE_ACCOUNT_ID
# NEWSAPI_KEY, OPENAI_API_KEY, ALPHA_VANTAGE_API_KEY

## PERMANENT ACCESS MODEL
# No NETLIFY_AUTH_TOKEN needed → use Netlify MCP directly
# No STRIPE_SECRET_KEY needed → use Stripe MCP + hardcoded payment links
# All other APIs → GitHub Secrets → workflow env vars
# Self-healing: guardian_self_healing.yml monitors every 30min
# RLHF: ai_intelligence_layer.yml runs 4x daily
# Everything else: 100 active workflows, all scheduled

# 🚀 NYSR Passive Income Stack — Setup Guide
## One-time setup. Earns forever.

---

## ⚡ STEP 1: Bandwidth Sharing (30 min setup → $40-110/month passive)

### What you need:
- A computer/server that stays on 24/7 (home PC, Raspberry Pi, old laptop)
- Docker installed: https://docs.docker.com/get-docker/

### Setup:
```bash
# 1. Clone the repo
git clone https://github.com/nyspotlightreport/sct-agency-bots
cd sct-agency-bots/passive-income

# 2. Configure credentials
cp .env.example .env
nano .env  # Fill in your credentials (see signups below)

# 3. Start ALL apps simultaneously
docker-compose -f docker-compose.passive.yml up -d

# 4. Check status
docker-compose -f docker-compose.passive.yml ps
```

### Sign up for each platform (all free):
| Platform | Signup URL | Referral Code | Monthly Est |
|----------|-----------|---------------|-------------|
| EarnApp | https://earnapp.com/i/NYSR | | $3-8 |
| Honeygain | https://r.honeygain.me/NYSPOTLIGHT | | $2-5 |
| IPRoyal Pawns | https://iproyal.com/pawns | | $3-8 |
| PacketStream | https://packetstream.io | | $2-5 |
| Repocket | https://repocket.co | | $3-6 |
| Peer2Profit | https://peer2profit.com | | $2-4 |
| Traffmonetizer | https://traffmonetizer.com | | $2-4 |
| Grass | https://app.getgrass.io/?ref=NYSR | | $5-15 |
| **TOTAL** | | | **$22-55/IP** |

---

## ⚡ STEP 2: DePIN Token Networks (10 min → tokens with upside)

These are newer networks. You earn tokens that could increase in value.

### Grass (Web3 bandwidth sharing)
1. Sign up: https://app.getgrass.io
2. Install Chrome extension OR run via Docker (in docker-compose above)
3. Stay connected = earn GRASS tokens
4. **Why important**: 8.5M users, backed by major VCs, token has significant upside

### Nodepay
1. Sign up: https://nodepay.ai
2. Download app or Chrome extension
3. Earn NC tokens + APY staking rewards

---

## ⚡ STEP 3: Digital Product Platforms (30 min → $50-400/month)

### Gumroad (ALREADY HAVE ACCOUNT)
```bash
# Just run this — it creates all 20 products automatically
cd sct-agency-bots
python bots/gumroad_product_creator.py
```
✅ Done. Products live at gumroad.com/nyspotlightreport

### Etsy Digital Downloads
1. Go to etsy.com/sell
2. Create seller account (free)
3. List same 20 ProFlow products ($0.20/listing = $4 total)
4. Expected: $50-300/month from Etsy's organic search traffic

### PromptBase (AI Prompts)
1. Sign up at promptbase.com
2. Create 5-10 prompt packs from our existing 50 ChatGPT Prompts product
3. List at $2.99-$4.99 each
4. Platform takes 20% commission

---

## ⚡ STEP 4: Stock Media (2 hrs setup → $50-200/month growing)

### Adobe Stock Contributor
1. Sign up: contributor.stock.adobe.com
2. Upload AI-generated images (Midjourney, Stable Diffusion, DALL-E)
3. Categories that sell: business, technology, diversity, nature, finance
4. Earn 33% royalty per download

### Shutterstock Contributor  
1. Sign up: submit.shutterstock.com
2. Same images as Adobe Stock
3. Earn 15-40% based on volume

---

## ⚡ STEP 5: Amazon KDP Books (1 hr → royalties forever)

Books are auto-generated weekly via GitHub Actions.
Upload the PDFs from data/kdp_books/ to kdp.amazon.com

1. Go to kdp.amazon.com → Bookshelf → + Paperback
2. Title / description / keywords are in the .json file alongside each PDF
3. Price: $6.99-$9.99 paperback, $2.99 Kindle
4. Check "Expanded Distribution" for maximum reach

---

## ⚡ STEP 6: GitHub Sponsors (15 min → passive donations)

1. Go to github.com/sponsors/nyspotlightreport
2. Click "Get started with GitHub Sponsors"
3. Add a FUNDING.yml to every repo
4. Share in README files

---

## 💰 PROJECTED TOTAL AFTER ALL SETUPS

| Stream | Monthly Low | Monthly High |
|--------|-------------|--------------|
| Bandwidth (2 IPs) | $44 | $110 |
| Gumroad | $100 | $400 |
| Etsy | $50 | $300 |
| KDP Books (10 titles) | $50 | $200 |
| Adobe/Shutterstock | $30 | $200 |
| Bing Rewards | $5 | $15 |
| Sweepstakes (wins) | $0 | $500 |
| Grass/Nodepay tokens | $10 | $50+ |
| PromptBase | $20 | $100 |
| **TOTAL NEW STREAMS** | **$309** | **$1,875** |
| **+ Existing (YT/Beehiiv/Affs)** | **+$200** | **+$2,000** |
| **GRAND TOTAL** | **$509** | **$3,875/mo** |

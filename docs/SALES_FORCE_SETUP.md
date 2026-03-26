# Sales Force Setup Guide

## Overview
Recruitment, onboarding, commission structure, and NY legal requirements for the NY Spotlight Report commission sales force.

---

## 1. Recruitment Channels

### Closify (closify.com)
- Post commission-only sales roles under "Media / Publishing"
- Target closers with B2B experience in advertising, sponsorships, or media sales
- Job title: "Commission Sales Rep -- NY Spotlight Report"
- Highlight: uncapped commissions, editorial publication, NYC territory

### CommissionCrowd (commissioncrowd.com)
- List as a "Media & Publishing" opportunity
- Set territory to NYC Metro + Long Island
- Enable "Remote OK" with in-person meeting requirements for enterprise deals

### Additional Channels
- **LinkedIn** -- Post in NYC Sales Professionals groups
- **Indeed** -- Commission-only filter, NYC metro area
- **Referral bonuses** -- $200 bonus for reps who refer a closer that makes 3+ sales
- **Local networking** -- NYC Chamber of Commerce events, BNI chapters

---

## 2. Commission Structure

### Standard Tiers

| Tier | Monthly Revenue | Commission Rate |
|------|----------------|-----------------|
| Base | $0 - $2,000 | 15% |
| Silver | $2,001 - $5,000 | 18% |
| Gold | $5,001 - $10,000 | 20% |
| Platinum | $10,001+ | 25% |

### Product Commissions

| Product | Price Range | Rep Commission |
|---------|------------|---------------|
| Sponsored editorial feature | $500 - $2,000 | 15-25% (tier-based) |
| Newsletter sponsorship | $250 - $750 | 15-25% |
| Event coverage package | $1,000 - $5,000 | 15-25% |
| Annual advertising contract | $5,000 - $25,000 | 20% flat |
| Affiliate product referral | Varies | 10% of affiliate revenue |

### Payout Schedule
- Commissions calculated on the 1st of each month for prior month sales
- Payout via Stripe Connect on the 15th (net-15)
- Minimum payout threshold: $50
- Refunded sales within 30 days deducted from next payout

### Bonuses
- **First sale bonus**: $100 for first closed deal
- **Streak bonus**: 5 consecutive sales = extra 2% on all 5
- **Quarterly leader**: Top rep gets $500 bonus

---

## 3. Onboarding Checklist

1. Sign Independent Contractor Agreement (ICA)
2. Complete W-9 form
3. Set up Stripe Connect account for payouts
4. Receive unique referral code (used in Stripe metadata for attribution)
5. Access to sales deck, media kit, and rate card
6. 30-minute onboarding call with Sales Director
7. Access to CRM dashboard (Supabase-based)
8. First-week shadow session with experienced rep

---

## 4. New York State Legal Requirements

### Independent Contractor Classification
New York follows the ABC test and common-law factors:
- **A**: Free from control and direction in performing work
- **B**: Performs work outside the usual course of the hiring entity's business
- **C**: Customarily engaged in an independently established trade

### Required Documentation
- Written Independent Contractor Agreement
- W-9 (Request for Taxpayer Identification Number)
- No non-compete clauses (unenforceable for ICs in NY)
- Clear statement that rep is NOT an employee

### Tax Obligations
- Company issues 1099-NEC for reps earning $600+ annually
- Reps responsible for their own self-employment tax
- No withholding by company
- Quarterly estimated tax payments recommended for reps

### NYC-Specific
- NYC does NOT require a separate business license for commission-only sales reps
- Freelance Isn't Free Act: payments must be made by agreed-upon date (net-15)
- Written contract required for engagements over $800

### Compliance Checklist
- [ ] ICA signed with clear IC language
- [ ] W-9 collected before first payout
- [ ] No minimum hours or fixed schedule imposed
- [ ] Rep uses own equipment and methods
- [ ] Rep can work for other companies simultaneously
- [ ] Payment tied to results, not hours
- [ ] 1099-NEC issued by January 31 for prior tax year

---

## 5. Sales Tools and Resources

### CRM Access
- Dashboard: Supabase-based rep portal
- Track leads, sales, and commissions in real time
- Commission tracker bot runs daily (commission_tracker.py)

### Sales Materials
- Media kit PDF (brand overview, audience demographics, rate card)
- Case studies from past sponsored features
- Sample editorial features for prospects to review
- One-pager for cold outreach

### Prospect Lists
- Pre-built lists in data/sales/prospects.json
- Industries: restaurants, salons, real estate, law firms, fitness
- Territory: NYC Metro + Long Island

---

## 6. Performance Expectations

- Minimum 5 qualified outreach attempts per week
- Minimum 1 closed deal per month after ramp period (60 days)
- Reps inactive for 90+ days moved to "inactive" status
- Quarterly performance review with Sales Director

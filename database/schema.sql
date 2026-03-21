-- NYSR Mega-Agency Database Schema v1.0
-- Run this in Supabase SQL editor at: https://app.supabase.com
-- Free tier: 500MB storage, 2GB bandwidth, unlimited API calls

-- ═══════════════════════════════════════════════════════
-- CONTACTS TABLE — the core of the CRM
-- ═══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS contacts (
  id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email           TEXT UNIQUE,
  name            TEXT,
  title           TEXT,
  company         TEXT,
  phone           TEXT,
  linkedin        TEXT,
  website         TEXT,
  industry        TEXT,
  employees       INTEGER,
  
  -- Pipeline
  stage           TEXT DEFAULT 'LEAD'
                  CHECK (stage IN ('LEAD','PROSPECT','QUALIFIED','PROPOSAL','NEGOTIATION','CLOSED_WON','CLOSED_LOST')),
  stage_changed_at TIMESTAMPTZ,
  stage_reason    TEXT,
  
  -- Scoring
  score           INTEGER DEFAULT 0 CHECK (score >= 0 AND score <= 100),
  grade           TEXT CHECK (grade IN ('A','B','C','D')),
  priority        TEXT CHECK (priority IN ('HIGH','MEDIUM','LOW')),
  icp             TEXT,  -- which ICP they match
  
  -- Metadata  
  source          TEXT DEFAULT 'apollo',
  hubspot_id      TEXT,
  apollo_id       TEXT,
  tags            TEXT[],
  notes           TEXT,
  last_contacted  TIMESTAMPTZ,
  next_action     TEXT,
  next_action_date DATE,
  
  -- Tracking
  last_updated    TIMESTAMPTZ DEFAULT NOW(),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════
-- DEALS TABLE — tracks revenue opportunities
-- ═══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS deals (
  id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  contact_id      UUID REFERENCES contacts(id),
  
  -- Deal info
  title           TEXT NOT NULL,
  product         TEXT CHECK (product IN ('proflow_starter','proflow_growth','proflow_agency','dfy_essential','dfy_growth','lead_gen_starter','lead_gen_growth','dfy_bot_setup','custom')),
  value           DECIMAL(10,2),
  recurring       BOOLEAN DEFAULT false,
  
  -- Stage
  stage           TEXT DEFAULT 'PROPOSAL'
                  CHECK (stage IN ('PROPOSAL','NEGOTIATION','CLOSED_WON','CLOSED_LOST')),
  probability     DECIMAL(3,2) DEFAULT 0.25,
  
  -- Timeline
  expected_close  DATE,
  actual_close    DATE,
  
  -- Stripe
  stripe_payment_link TEXT,
  stripe_session_id   TEXT,
  paid            BOOLEAN DEFAULT false,
  
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════
-- ACTIVITIES TABLE — all interactions logged
-- ═══════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS activities (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  contact_id  UUID REFERENCES contacts(id),
  deal_id     UUID REFERENCES deals(id),
  
  type        TEXT CHECK (type IN ('email_sent','email_opened','email_replied','call','meeting','note','stage_change','proposal_sent','contract_sent','payment_received')),
  subject     TEXT,
  body        TEXT,
  outcome     TEXT,
  
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════
-- PIPELINE VIEW — real-time pipeline visibility
-- ═══════════════════════════════════════════════════════
CREATE OR REPLACE VIEW pipeline_summary AS
SELECT 
  c.stage,
  COUNT(*) as contact_count,
  ROUND(AVG(c.score)) as avg_score,
  COUNT(d.id) as deal_count,
  COALESCE(SUM(d.value), 0) as pipeline_value,
  COUNT(CASE WHEN c.priority = 'HIGH' THEN 1 END) as high_priority_count
FROM contacts c
LEFT JOIN deals d ON d.contact_id = c.id AND d.stage NOT IN ('CLOSED_LOST')
GROUP BY c.stage
ORDER BY 
  CASE c.stage
    WHEN 'LEAD' THEN 1
    WHEN 'PROSPECT' THEN 2
    WHEN 'QUALIFIED' THEN 3
    WHEN 'PROPOSAL' THEN 4
    WHEN 'NEGOTIATION' THEN 5
    WHEN 'CLOSED_WON' THEN 6
    WHEN 'CLOSED_LOST' THEN 7
  END;

-- ═══════════════════════════════════════════════════════
-- REVENUE VIEW — MRR tracking
-- ═══════════════════════════════════════════════════════
CREATE OR REPLACE VIEW revenue_summary AS
SELECT
  DATE_TRUNC('month', actual_close) as month,
  COUNT(*) as deals_closed,
  SUM(value) as total_revenue,
  SUM(CASE WHEN recurring THEN value ELSE 0 END) as mrr_added,
  SUM(CASE WHEN NOT recurring THEN value ELSE 0 END) as one_time_revenue
FROM deals
WHERE stage = 'CLOSED_WON' AND actual_close IS NOT NULL
GROUP BY DATE_TRUNC('month', actual_close)
ORDER BY month DESC;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_contacts_stage ON contacts(stage);
CREATE INDEX IF NOT EXISTS idx_contacts_score ON contacts(score DESC);
CREATE INDEX IF NOT EXISTS idx_contacts_priority ON contacts(priority);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_deals_contact ON deals(contact_id);
CREATE INDEX IF NOT EXISTS idx_activities_contact ON activities(contact_id);

-- Row Level Security (free tier supports this)
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE deals ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "service_role_all" ON contacts FOR ALL USING (true);
CREATE POLICY "service_role_all" ON deals FOR ALL USING (true);
CREATE POLICY "service_role_all" ON activities FOR ALL USING (true);

-- ═══════════════════════════════════════════════════════
-- SAMPLE DATA — 3 starter contacts to test with
-- ═══════════════════════════════════════════════════════
INSERT INTO contacts (email, name, title, company, stage, score, grade, priority, icp, source)
VALUES 
  ('test.ceo@startup.com', 'Alex Chen', 'CEO', 'ContentCo', 'LEAD', 82, 'A', 'HIGH', 'dfy_agency', 'manual'),
  ('marketing@agency.com', 'Sarah Kim', 'Marketing Director', 'Digital Agency NYC', 'PROSPECT', 71, 'A', 'HIGH', 'proflow_ai', 'manual'),
  ('founder@ecom.com', 'Mike Ross', 'Founder', 'ShopFast', 'QUALIFIED', 65, 'B', 'MEDIUM', 'dfy_agency', 'manual')
ON CONFLICT (email) DO NOTHING;

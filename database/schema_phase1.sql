-- Phase 1 Customer Acquisition Layer Schema
-- Run this in Supabase SQL Editor after schema.sql

-- Journey tracking
CREATE TABLE IF NOT EXISTS journey_steps (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id    UUID REFERENCES contacts(id),
  journey_key   TEXT NOT NULL,
  step_num      INT NOT NULL,
  subject       TEXT,
  body          TEXT,
  sent_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Scheduled social posts
CREATE TABLE IF NOT EXISTS scheduled_posts (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  platform    TEXT NOT NULL,
  content     TEXT,
  status      TEXT DEFAULT 'draft',
  scheduled_for TIMESTAMPTZ,
  posted_at   TIMESTAMPTZ,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- SEO opportunities
CREATE TABLE IF NOT EXISTS seo_opportunities (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  keyword              TEXT NOT NULL,
  page_position        INT DEFAULT 0,
  estimated_traffic    INT DEFAULT 0,
  brief                JSONB,
  status               TEXT DEFAULT 'pending',
  content_url          TEXT,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- A/B tests
CREATE TABLE IF NOT EXISTS ab_tests (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  page_name   TEXT NOT NULL,
  page_path   TEXT,
  goal        TEXT,
  variants    JSONB,
  status      TEXT DEFAULT 'running',
  winner_id   TEXT,
  started_at  TIMESTAMPTZ DEFAULT NOW(),
  ended_at    TIMESTAMPTZ
);

-- A/B test events
CREATE TABLE IF NOT EXISTS ab_test_events (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_id     UUID REFERENCES ab_tests(id),
  variant_id  TEXT,
  converted   BOOLEAN DEFAULT FALSE,
  recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Health scores (extend contacts)
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS health_score   INT DEFAULT 50;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS health_risk    TEXT DEFAULT 'UNKNOWN';
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS health_action  TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS journey_key    TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS journey_step   INT DEFAULT 0;

-- Performance metrics (extend)
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS touch_count    INT DEFAULT 0;

-- RLS policies for new tables
ALTER TABLE journey_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE seo_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "service_role_all_journey_steps" ON journey_steps FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "service_role_all_scheduled_posts" ON scheduled_posts FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "service_role_all_seo" ON seo_opportunities FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "service_role_all_ab_tests" ON ab_tests FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "service_role_all_ab_events" ON ab_test_events FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Useful indexes
CREATE INDEX IF NOT EXISTS idx_journey_contact ON journey_steps(contact_id);
CREATE INDEX IF NOT EXISTS idx_journey_key ON journey_steps(journey_key);
CREATE INDEX IF NOT EXISTS idx_health_risk ON contacts(health_risk);
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_status ON scheduled_posts(status);

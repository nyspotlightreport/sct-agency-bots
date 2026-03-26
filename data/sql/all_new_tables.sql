-- NYSR Agency — All New Tables
-- Paste this entire block in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS audit_history (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT,
  dimension_num INTEGER,
  dimension_name TEXT,
  level INTEGER,
  status TEXT,
  value TEXT,
  notes TEXT,
  repair_attempted BOOLEAN DEFAULT FALSE,
  repair_succeeded BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS repair_log (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT,
  dimension_name TEXT,
  repair_type TEXT,
  status TEXT,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS learning_patterns (
  id BIGSERIAL PRIMARY KEY,
  dimension_name TEXT,
  failure_count_30d INTEGER DEFAULT 0,
  repair_success_rate NUMERIC DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_reps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  phone TEXT,
  stripe_connect_account_id TEXT,
  commission_rate_subscription NUMERIC DEFAULT 1.00,
  commission_rate_dfy NUMERIC DEFAULT 0.15,
  residual_rate NUMERIC DEFAULT 0.10,
  residual_months INTEGER DEFAULT 12,
  status TEXT DEFAULT 'pending',
  source TEXT DEFAULT 'closify',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rep_sales (
  id BIGSERIAL PRIMARY KEY,
  rep_id UUID REFERENCES sales_reps(id),
  stripe_session_id TEXT UNIQUE,
  customer_email TEXT NOT NULL,
  plan TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS commissions (
  id BIGSERIAL PRIMARY KEY,
  rep_id UUID REFERENCES sales_reps(id),
  sale_id BIGINT REFERENCES rep_sales(id),
  commission_type TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,
  stripe_transfer_id TEXT,
  status TEXT DEFAULT 'pending',
  period_month TEXT,
  paid_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS affiliate_partners (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  referral_code TEXT UNIQUE NOT NULL,
  commission_rate NUMERIC DEFAULT 0.20,
  total_earned_cents INTEGER DEFAULT 0,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS partnerships (
  id BIGSERIAL PRIMARY KEY,
  partner_name TEXT NOT NULL,
  partner_type TEXT,
  contact_email TEXT,
  status TEXT DEFAULT 'outreach_sent',
  contacted_at TIMESTAMPTZ,
  replied_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_run ON audit_history(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rep_sales_rep ON rep_sales(rep_id);
CREATE INDEX IF NOT EXISTS idx_commissions_rep ON commissions(rep_id);
CREATE INDEX IF NOT EXISTS idx_commissions_status ON commissions(status);

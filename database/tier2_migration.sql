-- TIER 2 MIGRATION: Voice Conversations + Client Dashboard Tables
-- Run this in Supabase Dashboard > SQL Editor
-- URL: https://supabase.com/dashboard/project/YOUR_PROJECT/sql/new

-- 1. Voice conversation logging
CREATE TABLE IF NOT EXISTS voice_conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  call_sid TEXT NOT NULL,
  from_number TEXT,
  department TEXT CHECK (department IN ('sales','support','general')),
  turn INTEGER DEFAULT 0,
  caller_text TEXT,
  ai_response TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_voice_conv_call ON voice_conversations(call_sid);
CREATE INDEX IF NOT EXISTS idx_voice_conv_dept ON voice_conversations(department);

-- 2. Client users for dashboard login
CREATE TABLE IF NOT EXISTS client_users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT NOT NULL,
  company TEXT,
  plan TEXT DEFAULT 'starter',
  role TEXT DEFAULT 'client',
  active BOOLEAN DEFAULT true,
  stripe_customer_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_login TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_client_users_email ON client_users(email);

-- 3. Client content tracking
CREATE TABLE IF NOT EXISTS client_content (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id UUID REFERENCES client_users(id) ON DELETE CASCADE,
  type TEXT CHECK (type IN ('blog','social','newsletter','image','video','ad')),
  title TEXT NOT NULL,
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft','scheduled','published','failed')),
  platform TEXT,
  word_count INTEGER,
  seo_score INTEGER,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_client_content_client ON client_content(client_id);

-- 4. Client analytics (daily snapshots)
CREATE TABLE IF NOT EXISTS client_analytics (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id UUID REFERENCES client_users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  page_views INTEGER DEFAULT 0,
  unique_visitors INTEGER DEFAULT 0,
  leads_generated INTEGER DEFAULT 0,
  social_engagement INTEGER DEFAULT 0,
  voice_calls INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(client_id, date)
);
CREATE INDEX IF NOT EXISTS idx_client_analytics ON client_analytics(client_id, date);

-- 5. Client social posts
CREATE TABLE IF NOT EXISTS client_social_posts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id UUID REFERENCES client_users(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  content TEXT,
  status TEXT DEFAULT 'scheduled' CHECK (status IN ('draft','scheduled','published','failed')),
  likes INTEGER DEFAULT 0,
  comments INTEGER DEFAULT 0,
  shares INTEGER DEFAULT 0,
  impressions INTEGER DEFAULT 0,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_client_social ON client_social_posts(client_id);

-- 6. Enable Row Level Security
ALTER TABLE voice_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_social_posts ENABLE ROW LEVEL SECURITY;

-- 7. Service role policies (allow full access for backend)
CREATE POLICY IF NOT EXISTS service_all_voice ON voice_conversations FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS service_all_users ON client_users FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS service_all_content ON client_content FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS service_all_analytics ON client_analytics FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS service_all_social ON client_social_posts FOR ALL USING (true);

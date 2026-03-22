// netlify/functions/lead-capture.js
// UPGRADED: Now immediately tags lead for nurture sequence enrollment
// AND triggers apollo_7touch_sequence via GitHub Actions dispatch
// Gap closed: lead-capture → nurture sequence was MISSING connection

exports.handler = async (event) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };
  if (event.httpMethod === 'OPTIONS') return { statusCode: 200, headers, body: '' };
  if (event.httpMethod !== 'POST') return { statusCode: 405, headers, body: JSON.stringify({ error: 'Method not allowed' }) };

  try {
    const data = JSON.parse(event.body || '{}');
    const { name, email, niche, goal, source } = data;
    if (!email) return { statusCode: 400, headers, body: JSON.stringify({ error: 'Email required' }) };

    const SUPA_URL = process.env.SUPABASE_URL;
    const SUPA_KEY = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;
    const PUSH_API = process.env.PUSHOVER_API_KEY;
    const PUSH_USER= process.env.PUSHOVER_USER_KEY;
    const HS_KEY   = process.env.HUBSPOT_API_KEY;
    const GH_PAT   = process.env.GH_PAT;
    const REPO     = 'nyspotlightreport/sct-agency-bots';

    const results  = { email, source: source || 'website', saved: [] };
    const ts       = new Date().toISOString();

    // Score based on source (high-intent sources get higher score)
    const sourceScores = { 'webinar': 75, 'audit': 70, 'free-plan': 60, 'agency': 65, 'proflow': 65, 'website': 40 };
    const score = sourceScores[source] || 40;

    // 1. Save to Supabase — tag for nurture enrollment
    if (SUPA_URL && SUPA_KEY) {
      try {
        const r = await fetch(`${SUPA_URL}/rest/v1/contacts`, {
          method: 'POST',
          headers: { 'apikey': SUPA_KEY, 'Authorization': `Bearer ${SUPA_KEY}`,
                     'Content-Type': 'application/json', 'Prefer': 'return=minimal' },
          body: JSON.stringify({
            email, name: name || null, niche: niche || null, goal: goal || null,
            source: source || 'website', stage: 'LEAD', score,
            tags: ['nurture_enroll', `source_${source||'website'}`],
            created_at: ts
          })
        });
        if (r.ok || r.status === 409) results.saved.push('supabase');
      } catch(e) { results.supabase_error = e.message; }
    }

    // 2. HubSpot
    if (HS_KEY) {
      try {
        await fetch('https://api.hubapi.com/crm/v3/objects/contacts', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${HS_KEY}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ properties: { email, firstname: name || '', company: niche || '',
            lifecyclestage: 'lead', lead_source: source || 'website', hs_lead_status: 'NEW' } })
        });
        results.saved.push('hubspot');
      } catch(e) {}
    }

    // 3. Trigger nurture sequence enrollment immediately
    if (GH_PAT) {
      try {
        await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/seven_engine_close_system.yml/dispatches`, {
          method: 'POST',
          headers: { 'Authorization': `token ${GH_PAT}`, 'Accept': 'application/vnd.github.v3+json',
                     'Content-Type': 'application/json' },
          body: JSON.stringify({ ref: 'main' })
        });
        results.saved.push('nurture_triggered');
      } catch(e) {}
    }

    // 4. Pushover alert
    if (PUSH_API && PUSH_USER) {
      try {
        await fetch('https://api.pushover.net/1/messages.json', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: PUSH_API, user: PUSH_USER,
            title: `🎯 New Lead! Score: ${score}`,
            message: `${email}\nSource: ${source||'website'} | Score: ${score}\nNiche: ${niche||'unknown'}\nNurture: enrolled`
          })
        });
        results.saved.push('pushover');
      } catch(e) {}
    }

    return { statusCode: 200, headers, body: JSON.stringify({ success: true, ...results }) };
  } catch (err) {
    return { statusCode: 500, headers, body: JSON.stringify({ error: err.message }) };
  }
};

// netlify/functions/lead-capture.js
// P0 FIX: This function was missing — every site form was silently 404-ing.
// Reese Morgan / Casey Lin — this MUST be monitored by guardian_self_healing.yml

exports.handler = async (event) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, headers, body: JSON.stringify({ error: 'Method not allowed' }) };
  }

  try {
    const data = JSON.parse(event.body || '{}');
    const { name, email, niche, goal, source } = data;

    if (!email) {
      return { statusCode: 400, headers, body: JSON.stringify({ error: 'Email required' }) };
    }

    const SUPA_URL  = process.env.SUPABASE_URL;
    const SUPA_KEY  = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;
    const PUSH_API  = process.env.PUSHOVER_API_KEY;
    const PUSH_USER = process.env.PUSHOVER_USER_KEY;
    const HS_KEY    = process.env.HUBSPOT_API_KEY;

    const results = { email, source: source || 'website', saved: [] };
    const ts = new Date().toISOString();

    // 1. Supabase — primary CRM
    if (SUPA_URL && SUPA_KEY) {
      try {
        const r = await fetch(`${SUPA_URL}/rest/v1/contacts`, {
          method: 'POST',
          headers: {
            'apikey': SUPA_KEY,
            'Authorization': `Bearer ${SUPA_KEY}`,
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
          },
          body: JSON.stringify({
            email,
            name:   name   || null,
            niche:  niche  || null,
            goal:   goal   || null,
            source: source || 'website',
            stage:  'LEAD',
            score:  40,
            tags:   ['website-lead'],
            created_at: ts
          })
        });
        // 409 = duplicate email, still counts as success
        if (r.ok || r.status === 409) results.saved.push('supabase');
        else results.supabase_status = r.status;
      } catch(e) {
        results.supabase_error = e.message;
      }
    }

    // 2. HubSpot — pipeline sync
    if (HS_KEY) {
      try {
        await fetch('https://api.hubapi.com/crm/v3/objects/contacts', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${HS_KEY}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            properties: {
              email,
              firstname:       name  || '',
              company:         niche || '',
              lifecyclestage:  'lead',
              lead_source:     source || 'website',
              hs_lead_status:  'NEW'
            }
          })
        });
        results.saved.push('hubspot');
      } catch(e) {
        // Non-fatal — Supabase is primary
      }
    }

    // 3. Pushover — Chairman alert
    if (PUSH_API && PUSH_USER) {
      try {
        await fetch('https://api.pushover.net/1/messages.json', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            token:   PUSH_API,
            user:    PUSH_USER,
            title:   '🎯 New NYSR Lead!',
            message: `${email}\nName: ${name || 'unknown'}\nSource: ${source || 'website'}\nNiche: ${niche || 'unknown'}\nGoal: ${goal || 'unknown'}`
          })
        });
        results.saved.push('pushover');
      } catch(e) {
        // Non-fatal
      }
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ success: true, ...results })
    };

  } catch (err) {
    console.error('lead-capture error:', err);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: err.message })
    };
  }
};

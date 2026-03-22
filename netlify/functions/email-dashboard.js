// netlify/functions/email-dashboard.js
// Server-side API for email intelligence dashboard — no DB creds in frontend

exports.handler = async (event) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json'
  };

  const SUPA_URL = process.env.SUPABASE_URL;
  const SUPA_KEY = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;

  try {
    // Get recent emails
    const r = await fetch(
      `${SUPA_URL}/rest/v1/email_inbox?order=processed_at.desc&limit=100&select=category,from_email,subject,ai_summary,forwarded,processed_at`,
      { headers: { 'apikey': SUPA_KEY, 'Authorization': `Bearer ${SUPA_KEY}` } }
    );
    const emails = await r.json();

    // Calculate stats
    const today = new Date();
    today.setHours(0,0,0,0);
    const todayEmails = (emails || []).filter(e =>
      e.processed_at && new Date(e.processed_at) >= today
    );

    const stats = {
      total:     todayEmails.length,
      revenue:   todayEmails.filter(e => e.category === 'REVENUE').length,
      urgent:    todayEmails.filter(e => ['URGENT','LEGAL'].includes(e.category)).length,
      forwarded: todayEmails.filter(e => e.forwarded).length,
      killed:    todayEmails.filter(e => ['NEWSLETTER','AUTO','SPAM'].includes(e.category)).length,
    };

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ emails: emails || [], stats })
    };
  } catch(e) {
    return { statusCode: 500, headers, body: JSON.stringify({ error: e.message }) };
  }
};

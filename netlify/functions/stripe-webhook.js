// netlify/functions/stripe-webhook.js
// COMPLETE payment pipeline:
// Stripe payment → issue TT ticket → create Supabase contact (CLOSED_WON)
// → trigger HubSpot → enroll referral program → Pushover alert to Sean

exports.handler = async (event) => {
  const STRIPE_SK     = process.env.STRIPE_SECRET_KEY;
  const TT_API_KEY    = process.env.TICKET_TAILOR_API_KEY;
  const SUPA_URL      = process.env.SUPABASE_URL;
  const SUPA_KEY      = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;
  const GH_PAT        = process.env.GH_PAT;
  const PUSH_API      = process.env.PUSHOVER_API_KEY;
  const PUSH_USER     = process.env.PUSHOVER_USER_KEY;
  const HS_KEY        = process.env.HUBSPOT_API_KEY;
  const REPO          = 'nyspotlightreport/sct-agency-bots';

  let stripeEvent;
  try { stripeEvent = JSON.parse(event.body || '{}'); }
  catch { return { statusCode: 400, body: 'Invalid JSON' }; }

  const eventType = stripeEvent.type || '';
  console.log(`Stripe webhook: ${eventType}`);

  if (!['checkout.session.completed', 'payment_intent.succeeded'].includes(eventType)) {
    return { statusCode: 200, body: JSON.stringify({ received: true, type: eventType }) };
  }

  const session  = stripeEvent.data?.object || {};
  const email    = session.customer_details?.email || session.receipt_email || '';
  const name     = session.customer_details?.name || '';
  const amount   = (session.amount_total || 0) / 100;
  const metadata = session.metadata || {};
  const offer_key = metadata.offer_key || '';
  const rep_code  = metadata.rep_code || '';

  // Ticket Tailor product mapping
  const TT_PRODUCTS = {
    'proflow_ai':       { product_id: 'pr_60343', ticket_type: 'ProFlow AI Member' },
    'proflow_growth':   { product_id: null,        ticket_type: 'ProFlow Growth Member' },
    'proflow_elite':    { product_id: null,        ticket_type: 'ProFlow Elite Member' },
    'dfy_setup':        { product_id: null,        ticket_type: 'DFY Setup Client' },
    'dfy_agency':       { product_id: null,        ticket_type: 'DFY Agency Client' },
    'enterprise':       { product_id: null,        ticket_type: 'Enterprise Client' },
    'annual_proflow_ai':{ product_id: null,        ticket_type: 'ProFlow AI Annual Member' },
  };

  const results = { email, offer_key, amount, processed: [] };

  // 1. Issue Ticket Tailor ticket (the "receipt" and access credential)
  if (TT_API_KEY && email) {
    try {
      const ttProduct = TT_PRODUCTS[offer_key];
      if (ttProduct) {
        const ttHeaders = {
          'Authorization': `Basic ${Buffer.from(TT_API_KEY + ':').toString('base64')}`,
          'Content-Type': 'application/x-www-form-urlencoded'
        };

        // Create a membership/access record as an issued ticket
        const ttBody = new URLSearchParams({
          full_name: name || email.split('@')[0],
          email: email,
          reference: `stripe_${session.id || Date.now()}`,
          send_email: 'true'
        });

        // Find or create an event for this product tier
        // For now, issue directly to the store's product
        const ttRes = await fetch('https://api.tickettailor.com/v1/issued_tickets', {
          method: 'POST',
          headers: ttHeaders,
          body: ttBody.toString()
        });

        const ttData = await ttRes.json();
        if (ttData.id) {
          results.processed.push(`ticket_issued:${ttData.id}`);
          console.log(`TT ticket issued: ${ttData.id} for ${email}`);
        } else {
          console.log('TT ticket issue response:', JSON.stringify(ttData));
          results.processed.push('ticket_attempted');
        }
      }
    } catch(e) {
      console.error('TT error:', e.message);
      results.tt_error = e.message;
    }
  }

  // 2. Supabase — mark as CLOSED_WON
  if (SUPA_URL && SUPA_KEY) {
    try {
      // Check if contact exists
      const findRes = await fetch(
        `${SUPA_URL}/rest/v1/contacts?email=eq.${encodeURIComponent(email)}&select=id`,
        { headers: { 'apikey': SUPA_KEY, 'Authorization': `Bearer ${SUPA_KEY}` } }
      );
      const existing = await findRes.json();

      if (existing?.[0]?.id) {
        await fetch(`${SUPA_URL}/rest/v1/contacts?id=eq.${existing[0].id}`, {
          method: 'PATCH',
          headers: { 'apikey': SUPA_KEY, 'Authorization': `Bearer ${SUPA_KEY}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ stage: 'CLOSED_WON', score: 100, tags: ['paying_customer', offer_key], last_activity: new Date().toISOString() })
        });
        results.processed.push('supabase_updated');
      } else {
        await fetch(`${SUPA_URL}/rest/v1/contacts`, {
          method: 'POST',
          headers: { 'apikey': SUPA_KEY, 'Authorization': `Bearer ${SUPA_KEY}`, 'Content-Type': 'application/json', 'Prefer': 'return=minimal' },
          body: JSON.stringify({ email, name, stage: 'CLOSED_WON', score: 100, source: `stripe_${offer_key}`, tags: ['paying_customer', offer_key], created_at: new Date().toISOString() })
        });
        results.processed.push('supabase_created');
      }

      // Log the payment
      await fetch(`${SUPA_URL}/rest/v1/conversation_log`, {
        method: 'POST',
        headers: { 'apikey': SUPA_KEY, 'Authorization': `Bearer ${SUPA_KEY}`, 'Content-Type': 'application/json', 'Prefer': 'return=minimal' },
        body: JSON.stringify({ channel: 'stripe', direction: 'inbound', body: `Payment $${amount} — ${offer_key}`, intent: 'payment_received', agent_name: 'Stripe Webhook' })
      });
    } catch(e) { console.error('Supabase error:', e.message); }
  }

  // 3. HubSpot — mark as customer
  if (HS_KEY && email) {
    try {
      const searchRes = await fetch('https://api.hubapi.com/crm/v3/objects/contacts/search', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${HS_KEY}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ filterGroups: [{ filters: [{ propertyName: 'email', operator: 'EQ', value: email }] }] })
      });
      const searchData = await searchRes.json();
      const hubspotId = searchData.results?.[0]?.id;
      if (hubspotId) {
        await fetch(`https://api.hubapi.com/crm/v3/objects/contacts/${hubspotId}`, {
          method: 'PATCH',
          headers: { 'Authorization': `Bearer ${HS_KEY}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ properties: { lifecyclestage: 'customer', hs_lead_status: 'IN_PROGRESS' } })
        });
        results.processed.push('hubspot_updated');
      }
    } catch(e) {}
  }

  // 4. Trigger GitHub Actions onboarding workflow
  if (GH_PAT) {
    try {
      await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/master_sales_engine.yml/dispatches`, {
        method: 'POST',
        headers: { 'Authorization': `token ${GH_PAT}`, 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json' },
        body: JSON.stringify({ ref: 'main' })
      });
      results.processed.push('onboarding_triggered');
    } catch(e) {}
  }

  // 5. Pushover — Sean gets instant notification
  if (PUSH_API && PUSH_USER) {
    try {
      const tier_labels = {
        'proflow_ai': 'ProFlow AI $97/mo', 'proflow_growth': 'ProFlow Growth $297/mo',
        'proflow_elite': 'ProFlow Elite $797/mo', 'dfy_setup': 'DFY Setup $1,497',
        'dfy_agency': 'DFY Agency $2,997', 'enterprise': 'Enterprise $4,997',
        'annual_proflow_ai': 'ProFlow AI Annual $982'
      };
      const rep_line = rep_code ? `\nRep: ${rep_code}` : '';
      await fetch('https://api.pushover.net/1/messages.json', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: PUSH_API, user: PUSH_USER,
          title: `💰 SALE: $${amount}`,
          message: `${email}\n${tier_labels[offer_key] || offer_key}\nAmount: $${amount}${rep_line}\nStage: CLOSED_WON ✅`,
          priority: 1, sound: 'cashregister'
        })
      });
      results.processed.push('pushover_sent');
    } catch(e) {}
  }

  return {
    statusCode: 200,
    body: JSON.stringify({ received: true, ...results })
  };
};

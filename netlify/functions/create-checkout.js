// netlify/functions/create-checkout.js
// Creates Stripe Checkout Sessions for NYSR offers.
// Architecture: Stripe collects payment → webhook issues TT ticket
// Zero Ticket Tailor payment integration needed. Bypassed entirely.

exports.handler = async (event) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };
  if (event.httpMethod === 'OPTIONS') return { statusCode: 200, headers, body: '' };
  if (event.httpMethod !== 'POST') return { statusCode: 405, headers, body: '{}' };

  const STRIPE_SK = process.env.STRIPE_SECRET_KEY;
  if (!STRIPE_SK) return { statusCode: 500, headers, body: JSON.stringify({ error: 'Stripe not configured' }) };

  let body;
  try { body = JSON.parse(event.body || '{}'); } catch { return { statusCode: 400, headers, body: '{}' }; }

  const { offer_key, customer_email, rep_code, source } = body;

  // Complete offer catalog — all 7 tiers
  const OFFERS = {
    'proflow_ai': {
      name: 'ProFlow AI — $97/month',
      description: 'Full AI content + marketing automation. Social, blog, email, SEO — all automated.',
      amount: 9700,
      mode: 'subscription',
      interval: 'month',
      tt_product_id: 'pr_60343',
      metadata: { tier: 'proflow_ai', rep_code: rep_code || '' }
    },
    'proflow_growth': {
      name: 'ProFlow Growth — $297/month',
      description: 'Everything in ProFlow AI plus advanced outreach, lead scoring, and CRM automation.',
      amount: 29700,
      mode: 'subscription',
      interval: 'month',
      metadata: { tier: 'proflow_growth', rep_code: rep_code || '' }
    },
    'proflow_elite': {
      name: 'ProFlow Elite — $797/month',
      description: 'Hands-on AI agency. 4 strategy meetings per month. Full system customization.',
      amount: 79700,
      mode: 'subscription',
      interval: 'month',
      metadata: { tier: 'proflow_elite', rep_code: rep_code || '' }
    },
    'dfy_setup': {
      name: 'DFY Setup — $1,497',
      description: 'Done-for-you AI content system setup. Live in 14 days guaranteed.',
      amount: 149700,
      mode: 'payment',
      metadata: { tier: 'dfy_setup', rep_code: rep_code || '' }
    },
    'dfy_agency': {
      name: 'DFY Agency — $2,997 Setup',
      description: 'Full agency-grade AI system. Custom build + monthly retainer.',
      amount: 299700,
      mode: 'payment',
      metadata: { tier: 'dfy_agency', rep_code: rep_code || '' }
    },
    'enterprise': {
      name: 'Enterprise — $4,997',
      description: 'Enterprise AI automation. 10 guaranteed meetings in 90 days.',
      amount: 499700,
      mode: 'payment',
      metadata: { tier: 'enterprise', rep_code: rep_code || '' }
    },
    'annual_proflow_ai': {
      name: 'ProFlow AI Annual — $982 (Save $182)',
      description: 'ProFlow AI billed annually. Best value.',
      amount: 98200,
      mode: 'payment',
      metadata: { tier: 'annual_proflow_ai', rep_code: rep_code || '' }
    },
  };

  const offer = OFFERS[offer_key];
  if (!offer) return { statusCode: 400, headers, body: JSON.stringify({ error: `Unknown offer: ${offer_key}` }) };

  const SITE = 'https://nyspotlightreport.com';

  try {
    // Build line items
    const price_data = {
      currency: 'usd',
      product_data: {
        name: offer.name,
        description: offer.description,
        metadata: offer.metadata,
      },
      unit_amount: offer.amount,
    };

    if (offer.mode === 'subscription') {
      price_data.recurring = { interval: offer.interval };
    }

    const session_params = new URLSearchParams();
    session_params.append('mode', offer.mode);
    session_params.append('line_items[0][price_data][currency]', 'usd');
    session_params.append('line_items[0][price_data][product_data][name]', offer.name);
    session_params.append('line_items[0][price_data][product_data][description]', offer.description);
    session_params.append('line_items[0][price_data][unit_amount]', String(offer.amount));
    session_params.append('line_items[0][quantity]', '1');

    if (offer.mode === 'subscription') {
      session_params.append('line_items[0][price_data][recurring][interval]', offer.interval);
    }

    session_params.append('success_url', `${SITE}/store/success?session_id={CHECKOUT_SESSION_ID}`);
    session_params.append('cancel_url', `${SITE}/store/`);
    session_params.append('metadata[offer_key]', offer_key);
    session_params.append('metadata[rep_code]', rep_code || '');
    session_params.append('metadata[source]', source || 'store');

    if (customer_email) {
      session_params.append('customer_email', customer_email);
    }

    // Allow promotion codes for discounts
    session_params.append('allow_promotion_codes', 'true');

    // Collect billing address for compliance
    session_params.append('billing_address_collection', 'auto');

    const stripeRes = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${STRIPE_SK}`,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: session_params.toString()
    });

    const session = await stripeRes.json();

    if (session.error) {
      console.error('Stripe error:', session.error);
      return { statusCode: 400, headers, body: JSON.stringify({ error: session.error.message }) };
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        url: session.url,
        session_id: session.id
      })
    };

  } catch(e) {
    console.error('Checkout error:', e.message);
    return { statusCode: 500, headers, body: JSON.stringify({ error: e.message }) };
  }
};

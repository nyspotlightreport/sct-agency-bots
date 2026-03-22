import { serve } from "https://deno.land/std@0.177.0/http/server.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "";
const SUPABASE_KEY = Deno.env.get("SUPABASE_SERVICE_KEY") || Deno.env.get("SUPABASE_KEY") || "";
const PUSHOVER_API = Deno.env.get("PUSHOVER_API_KEY") || "";
const PUSHOVER_USR = Deno.env.get("PUSHOVER_USER_KEY") || "";

const TIER_MAP: Record<string, string> = {
  "price_proflow_ai":     "proflow_ai",
  "price_proflow_growth": "proflow_growth",
  "price_proflow_elite":  "proflow_elite",
  "price_dfy_setup":      "dfy_setup",
  "price_dfy_agency":     "dfy_agency",
  "price_pilot":          "pilot",
};

const TIER_VALUES: Record<string, number> = {
  "proflow_ai":     97,
  "proflow_growth": 297,
  "proflow_elite":  797,
  "dfy_setup":      1497,
  "dfy_agency":     4997,
  "pilot":          497,
};

async function supaInsert(table: string, data: Record<string, unknown>) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${table}`, {
    method: "POST",
    headers: {
      "apikey": SUPABASE_KEY,
      "Authorization": `Bearer ${SUPABASE_KEY}`,
      "Content-Type": "application/json",
      "Prefer": "return=minimal"
    },
    body: JSON.stringify(data)
  });
  return res.ok;
}

async function pushNotify(title: string, message: string) {
  if (!PUSHOVER_API) return;
  await fetch("https://api.pushover.net/1/messages.json", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token: PUSHOVER_API, user: PUSHOVER_USR, title, message, priority: 0 })
  }).catch(() => {});
}

async function handlePayment(session: Record<string, unknown>) {
  const email    = (session.customer_details as Record<string,string>)?.email || "";
  const name     = (session.customer_details as Record<string,string>)?.name || "";
  const priceId  = session.metadata?.price_id as string || "";
  const tier     = TIER_MAP[priceId] || "proflow_ai";
  const amount   = TIER_VALUES[tier] || 97;
  const now      = new Date().toISOString();

  // 1. Upsert contact as CLOSED_WON
  await supaInsert("contacts", {
    email, name,
    stage: "CLOSED_WON",
    source: "stripe_webhook",
    journey_key: "onboarding",
    converted_at: now,
    lifetime_value: amount,
    tags: [tier.replace("_","-"), "paying-customer"],
    score: 200,
    priority: "HIGH",
    notes: `Stripe payment: ${tier} $${amount}`
  });

  // 2. Log revenue
  await supaInsert("revenue_daily", {
    date: now.split("T")[0],
    amount,
    source: tier,
    description: `${name} — ${tier}`
  });

  // 3. Trigger onboarding sequence in outreach_sequences
  await supaInsert("outreach_sequences", {
    sequence_name: "onboarding_30d",
    status: "active",
    channel: "email",
    notes: `Auto-enrolled after Stripe payment — tier: ${tier}`,
    next_touch_at: now
  });

  // 4. Log analytics event
  await supaInsert("analytics_events", {
    event_name: "payment_completed",
    event_category: "revenue",
    properties: JSON.stringify({ tier, amount, email })
  });

  // 5. Notify Sean — info only, no action needed
  await pushNotify(
    `💰 New ${tier} customer!`,
    `${name} (${email})
Plan: ${tier} — $${amount}
Auto-onboarding fired. No action needed.`
  );
}

serve(async (req) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });

  const body = await req.text();
  let event: Record<string, unknown>;
  try { event = JSON.parse(body); }
  catch { return new Response("Invalid JSON", { status: 400 }); }

  const type    = event.type as string;
  const session = (event.data as Record<string, unknown>)?.object as Record<string, unknown>;

  if (type === "checkout.session.completed" || type === "payment_intent.succeeded") {
    await handlePayment(session);
  }

  return new Response(JSON.stringify({ received: true }), {
    headers: { "Content-Type": "application/json" }
  });
});

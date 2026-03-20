// Newsletter Subscribe Handler - stores in Netlify + HubSpot
exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method not allowed" };
  }

  const HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type"
  };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers: HEADERS, body: "" };
  }

  let body = {};
  try { body = JSON.parse(event.body || "{}"); } catch(e) {}
  const email = (body.email || "").trim().toLowerCase();
  const name  = (body.name  || "").trim();

  if (!email || !email.includes("@")) {
    return { statusCode: 400, headers: HEADERS, body: JSON.stringify({ error: "Invalid email" }) };
  }

  const results = {};

  // 1. HubSpot CRM — add as contact
  const HS_KEY = process.env.HUBSPOT_API_KEY || "";
  if (HS_KEY) {
    try {
      const nameParts = name.split(" ");
      const r = await fetch("https://api.hubapi.com/crm/v3/objects/contacts", {
        method: "POST",
        headers: { "Authorization": `Bearer ${HS_KEY}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          properties: {
            email,
            firstname: nameParts[0] || "",
            lastname:  nameParts.slice(1).join(" ") || "",
            lead_status: "NEW",
            hs_lead_status: "NEW",
            lifecyclestage: "subscriber",
            source: "NY Spotlight Report Website"
          }
        }),
        signal: AbortSignal.timeout(8000)
      });
      results.hubspot = r.status === 201 ? "added" : `http_${r.status}`;
    } catch(e) { results.hubspot = "error: " + e.message; }
  }

  // 2. Log to console (Netlify function logs)
  console.log(`📧 NEW SUBSCRIBER: ${email} | name: ${name || "unknown"} | hs: ${results.hubspot}`);

  return {
    statusCode: 200,
    headers: HEADERS,
    body: JSON.stringify({
      success: true,
      message: "Subscribed!",
      email,
      results
    })
  };
};

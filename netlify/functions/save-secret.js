// Save OAuth Token as GitHub Secret
// Triggers a GitHub Actions workflow that uses Python/PyNaCl for proper encryption
// Route: /api/save-secret

exports.handler = async (event, context) => {
  const CORS = {
    "Access-Control-Allow-Origin": "https://nyspotlightreport.com",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS"
  };
  if (event.httpMethod === "OPTIONS") return { statusCode: 200, headers: CORS, body: "" };
  if (event.httpMethod !== "POST")    return { statusCode: 405, headers: CORS, body: "Method not allowed" };

  const GH_TOKEN = process.env.GH_PAT || "";
  const REPO     = "nyspotlightreport/sct-agency-bots";

  if (!GH_TOKEN) {
    return { statusCode: 500, headers: CORS, body: JSON.stringify({ error: "GH_PAT not configured on server" }) };
  }

  let body;
  try { body = JSON.parse(event.body || "{}"); }
  catch { return { statusCode: 400, headers: CORS, body: JSON.stringify({ error: "Invalid JSON" }) }; }

  const secrets = body.secrets || {};
  const entries = Object.entries(secrets).filter(([k,v]) => k && v);
  if (!entries.length) {
    return { statusCode: 400, headers: CORS, body: JSON.stringify({ error: "No secrets provided" }) };
  }

  try {
    // Build inputs for the GitHub Actions workflow
    // We pass secret_name and secret_value as workflow_dispatch inputs
    // The workflow uses PyNaCl to encrypt properly
    const results = {};
    
    for (const [secretName, secretValue] of entries) {
      const res = await fetch(
        `https://api.github.com/repos/${REPO}/actions/workflows/save-oauth-token.yml/dispatches`,
        {
          method: "POST",
          headers: {
            Authorization: `token ${GH_TOKEN}`,
            "Content-Type": "application/json",
            Accept: "application/vnd.github.v3+json"
          },
          body: JSON.stringify({
            ref: "main",
            inputs: {
              secret_name:  secretName,
              secret_value: secretValue
            }
          })
        }
      );
      results[secretName] = res.status === 204 ? "queued" : `error_${res.status}`;
    }

    return {
      statusCode: 200,
      headers: CORS,
      body: JSON.stringify({ success: true, results, message: "Secret is being saved via GitHub Actions (takes ~30s)" })
    };
  } catch (err) {
    return { statusCode: 500, headers: CORS, body: JSON.stringify({ error: err.message }) };
  }
};

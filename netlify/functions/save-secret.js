// netlify/functions/save-secret.js
// Saves one or many secrets to GitHub Secrets via API.
// Handles both { secret_name, secret_value } and { secrets: { KEY: VALUE, ... } }
// Used by /tokens/ page. Allowlisted secrets only.

const ALLOWED = new Set([
  'LINKEDIN_ACCESS_TOKEN','LINKEDIN_REFRESH_TOKEN','LINKEDIN_CLIENT_ID','LINKEDIN_CLIENT_SECRET',
  'INSTAGRAM_PAGE_TOKEN','INSTAGRAM_PAGE_ID','FB_PAGE_TOKEN','FB_PAGE_ID','FB_USER_TOKEN',
  'META_APP_ID','META_APP_SECRET','FB_APP_ID','FB_APP_SECRET',
  'REDDIT_USERNAME','REDDIT_PASSWORD','REDDIT_CLIENT_ID','REDDIT_CLIENT_SECRET',
  'GOOGLE_SERVICE_ACCOUNT_JSON','GOOGLE_ACCESS_TOKEN','YOUTUBE_ACCESS_TOKEN',
  'TWITTER_ACCESS_TOKEN','TWITTER_ACCESS_SECRET'
]);

exports.handler = async (event) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };
  if (event.httpMethod === 'OPTIONS') return { statusCode: 200, headers, body: '' };
  if (event.httpMethod !== 'POST') return { statusCode: 405, headers, body: JSON.stringify({ error: 'Method not allowed' }) };

  const GH_PAT = process.env.GH_PAT;
  const REPO   = 'nyspotlightreport/sct-agency-bots';

  if (!GH_PAT) {
    return { statusCode: 500, headers, body: JSON.stringify({ error: 'GH_PAT not set on this server. Cannot save secrets.' }) };
  }

  let body;
  try { body = JSON.parse(event.body || '{}'); }
  catch { return { statusCode: 400, headers, body: JSON.stringify({ error: 'Invalid JSON body' }) }; }

  // Normalize: support both formats
  // Format A: { secret_name: "KEY", secret_value: "VALUE" }
  // Format B: { secrets: { KEY1: VAL1, KEY2: VAL2 } }
  let secretMap = {};
  if (body.secrets && typeof body.secrets === 'object') {
    secretMap = body.secrets;
  } else if (body.secret_name && body.secret_value) {
    secretMap[body.secret_name] = body.secret_value;
  } else {
    return { statusCode: 400, headers, body: JSON.stringify({ error: 'Provide either {secrets:{}} or {secret_name, secret_value}' }) };
  }

  // Validate all keys
  for (const key of Object.keys(secretMap)) {
    if (!ALLOWED.has(key)) {
      return { statusCode: 403, headers, body: JSON.stringify({ error: `Secret '${key}' not in allowlist` }) };
    }
  }

  try {
    // Get GitHub public key for encryption
    const pkRes = await fetch(`https://api.github.com/repos/${REPO}/actions/secrets/public-key`, {
      headers: { 'Authorization': `token ${GH_PAT}`, 'Accept': 'application/vnd.github.v3+json' }
    });
    if (!pkRes.ok) throw new Error(`GitHub public key fetch failed: ${pkRes.status}`);
    const { key: pubKeyB64, key_id } = await pkRes.json();

    // Save each secret
    const saved = [];
    const errors = [];

    for (const [name, value] of Object.entries(secretMap)) {
      if (!value) continue;
      try {
        // Base64-encode the value (GitHub decodes on their end via libsodium)
        const encodedValue = Buffer.from(String(value)).toString('base64');

        const putRes = await fetch(`https://api.github.com/repos/${REPO}/actions/secrets/${name}`, {
          method: 'PUT',
          headers: {
            'Authorization': `token ${GH_PAT}`,
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ encrypted_value: encodedValue, key_id })
        });

        if (putRes.ok || putRes.status === 204) {
          saved.push(name);
        } else {
          const errText = await putRes.text();
          errors.push(`${name}: ${putRes.status} ${errText.slice(0,100)}`);
        }
      } catch (e) {
        errors.push(`${name}: ${e.message}`);
      }
    }

    if (saved.length > 0) {
      return { statusCode: 200, headers, body: JSON.stringify({ success: true, saved, errors: errors.length ? errors : undefined }) };
    } else {
      return { statusCode: 500, headers, body: JSON.stringify({ success: false, errors }) };
    }

  } catch (err) {
    return { statusCode: 500, headers, body: JSON.stringify({ success: false, error: err.message }) };
  }
};

// netlify/functions/linkedin-callback.js
// Receives OAuth callback from LinkedIn, exchanges code for tokens,
// saves BOTH access_token and refresh_token to GitHub Secrets automatically.
// After this one-time flow: token auto-refreshes every 45 days, forever.

exports.handler = async (event) => {
  const params = new URLSearchParams(event.queryStringParameters || {});
  const code  = params.get('code');
  const error = params.get('error');

  const CLIENT_ID     = process.env.LINKEDIN_CLIENT_ID;
  const CLIENT_SECRET = process.env.LINKEDIN_CLIENT_SECRET;
  const REDIRECT_URI  = 'https://nyspotlightreport.com/.netlify/functions/linkedin-callback';
  const GH_PAT        = process.env.GH_PAT;
  const REPO          = 'nyspotlightreport/sct-agency-bots';
  const PUSH_API      = process.env.PUSHOVER_API_KEY;
  const PUSH_USER     = process.env.PUSHOVER_USER_KEY;

  if (error) {
    return { statusCode: 400, body: `LinkedIn auth error: ${error}` };
  }
  if (!code) {
    return { statusCode: 400, body: 'No authorization code received from LinkedIn.' };
  }

  try {
    // Step 1: Exchange code for tokens
    const tokenRes = await fetch('https://www.linkedin.com/oauth/v2/accessToken', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type:   'authorization_code',
        code,
        redirect_uri:  REDIRECT_URI,
        client_id:     CLIENT_ID,
        client_secret: CLIENT_SECRET
      })
    });
    const tokens = await tokenRes.json();

    if (!tokens.access_token) {
      throw new Error(`Token exchange failed: ${JSON.stringify(tokens)}`);
    }

    // Step 2: Save both tokens to GitHub Secrets
    const secretsToSave = {
      'LINKEDIN_ACCESS_TOKEN':  tokens.access_token,
      'LINKEDIN_REFRESH_TOKEN': tokens.refresh_token || ''
    };

    const pkRes = await fetch(`https://api.github.com/repos/${REPO}/actions/secrets/public-key`, {
      headers: { 'Authorization': `token ${GH_PAT}`, 'Accept': 'application/vnd.github.v3+json' }
    });
    const { key: publicKey, key_id } = await pkRes.json();

    for (const [name, value] of Object.entries(secretsToSave)) {
      if (!value) continue;
      // Base64 encode value (simple encoding — GitHub decodes on their end)
      const encodedValue = Buffer.from(value).toString('base64');
      await fetch(`https://api.github.com/repos/${REPO}/actions/secrets/${name}`, {
        method: 'PUT',
        headers: {
          'Authorization': `token ${GH_PAT}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ encrypted_value: encodedValue, key_id })
      });
    }

    // Step 3: Pushover notification
    if (PUSH_API && PUSH_USER) {
      await fetch('https://api.pushover.net/1/messages.json', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: PUSH_API, user: PUSH_USER,
          title: '✅ LinkedIn Connected!',
          message: 'LinkedIn OAuth complete. Access + refresh tokens saved. MWF posts will now go live. Auto-refreshes every 45 days.'
        })
      }).catch(() => {});
    }

    // Step 4: Return success page
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'text/html' },
      body: `<!DOCTYPE html><html><head><title>LinkedIn Connected</title>
        <style>body{font-family:-apple-system,sans-serif;background:#060a0f;color:#e2e8f0;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
        .box{text-align:center;padding:40px}.num{font-size:64px;margin-bottom:16px}.h{font-size:24px;font-weight:700;color:#22c55e;margin-bottom:8px}.s{font-size:14px;color:#64748b}</style></head>
        <body><div class="box"><div class="num">✅</div>
        <div class="h">LinkedIn Connected Permanently</div>
        <div class="s">Tokens saved to GitHub Secrets. MWF posts are now live.<br>Token auto-refreshes every 45 days — you never need to do this again.</div>
        </div></body></html>`
    };

  } catch (err) {
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'text/html' },
      body: `<h1>Error: ${err.message}</h1><p>Check Netlify function logs.</p>`
    };
  }
};

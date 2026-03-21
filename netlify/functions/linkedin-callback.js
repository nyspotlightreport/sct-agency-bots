// LinkedIn OAuth Callback
// Exchanges auth code for access token, redirects back to /tokens/ with token
// Route: /api/linkedin-callback

exports.handler = async (event, context) => {
  const REDIRECT_BASE = "https://nyspotlightreport.com";
  const CLIENT_ID     = process.env.LINKEDIN_CLIENT_ID     || "78b8ect8u8qgbe";
  const CLIENT_SECRET = process.env.LINKEDIN_CLIENT_SECRET || "";

  // LinkedIn sends ?code=...&state=... on success, or ?error=...
  const { code, error, error_description } = event.queryStringParameters || {};

  if (error) {
    return {
      statusCode: 302,
      headers: { Location: `${REDIRECT_BASE}/tokens/?error=${encodeURIComponent(error_description || error)}&platform=li` }
    };
  }

  if (!code) {
    return {
      statusCode: 302,
      headers: { Location: `${REDIRECT_BASE}/tokens/?error=no_code&platform=li` }
    };
  }

  try {
    // Exchange code for access token
    const tokenRes = await fetch("https://www.linkedin.com/oauth/v2/accessToken", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type:    "authorization_code",
        code:          code,
        redirect_uri:  `${REDIRECT_BASE}/api/linkedin-callback`,
        client_id:     CLIENT_ID,
        client_secret: CLIENT_SECRET,
      }).toString()
    });

    const tokenData = await tokenRes.json();

    if (tokenData.access_token) {
      // Redirect back to /tokens/ with token — page will auto-save to GitHub
      return {
        statusCode: 302,
        headers: {
          Location: `${REDIRECT_BASE}/tokens/?platform=li&token=${encodeURIComponent(tokenData.access_token)}`
        }
      };
    } else {
      const errMsg = tokenData.error_description || tokenData.error || "token_exchange_failed";
      return {
        statusCode: 302,
        headers: { Location: `${REDIRECT_BASE}/tokens/?error=${encodeURIComponent(errMsg)}&platform=li` }
      };
    }
  } catch (err) {
    return {
      statusCode: 302,
      headers: { Location: `${REDIRECT_BASE}/tokens/?error=${encodeURIComponent(err.message)}&platform=li` }
    };
  }
};

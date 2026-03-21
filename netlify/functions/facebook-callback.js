// Facebook OAuth Callback
// Exchanges auth code for page access token, redirects back to /tokens/
// Route: /api/facebook-callback

exports.handler = async (event, context) => {
  const REDIRECT_BASE = "https://nyspotlightreport.com";
  const APP_ID        = process.env.FACEBOOK_APP_ID     || "1319442660014439";
  const APP_SECRET    = process.env.FACEBOOK_APP_SECRET || "";

  const { code, error, error_description } = event.queryStringParameters || {};

  if (error) {
    return {
      statusCode: 302,
      headers: { Location: `${REDIRECT_BASE}/tokens/?error=${encodeURIComponent(error_description || error)}&platform=fb` }
    };
  }

  if (!code) {
    return {
      statusCode: 302,
      headers: { Location: `${REDIRECT_BASE}/tokens/?error=no_code&platform=fb` }
    };
  }

  try {
    // Exchange code for short-lived user token
    const redirectUri = `${REDIRECT_BASE}/api/facebook-callback`;
    const tokenRes = await fetch(
      `https://graph.facebook.com/v21.0/oauth/access_token?` +
      `client_id=${APP_ID}&redirect_uri=${encodeURIComponent(redirectUri)}` +
      `&client_secret=${APP_SECRET}&code=${code}`
    );
    const tokenData = await tokenRes.json();

    if (!tokenData.access_token) {
      const errMsg = tokenData.error?.message || "token_exchange_failed";
      return {
        statusCode: 302,
        headers: { Location: `${REDIRECT_BASE}/tokens/?error=${encodeURIComponent(errMsg)}&platform=fb` }
      };
    }

    // Get pages the user manages
    const pagesRes = await fetch(
      `https://graph.facebook.com/v21.0/me/accounts?access_token=${tokenData.access_token}`
    );
    const pagesData = await pagesRes.json();
    const firstPage = pagesData.data?.[0];

    if (firstPage?.access_token) {
      // Use the page access token (permanent for most page operations)
      return {
        statusCode: 302,
        headers: {
          Location: `${REDIRECT_BASE}/tokens/?platform=fb&token=${encodeURIComponent(firstPage.access_token)}&page=${encodeURIComponent(firstPage.name || "Page")}`
        }
      };
    } else {
      // Fallback: return user token
      return {
        statusCode: 302,
        headers: {
          Location: `${REDIRECT_BASE}/tokens/?platform=fb&token=${encodeURIComponent(tokenData.access_token)}`
        }
      };
    }
  } catch (err) {
    return {
      statusCode: 302,
      headers: { Location: `${REDIRECT_BASE}/tokens/?error=${encodeURIComponent(err.message)}&platform=fb` }
    };
  }
};

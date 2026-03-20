exports.handler = async (event) => {
  const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY || "";
  
  if (!ANTHROPIC_KEY) {
    return { statusCode:200, headers:{"Content-Type":"application/json","Access-Control-Allow-Origin":"*"},
             body: JSON.stringify({error:"No ANTHROPIC_API_KEY"}) };
  }

  const models = ["claude-haiku-4-5-20251001","claude-3-5-haiku-20241022","claude-3-haiku-20240307"];
  const results = {};

  for (const model of models) {
    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method:"POST",
        headers:{"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","Content-Type":"application/json"},
        body: JSON.stringify({
          model, max_tokens:50,
          messages:[{role:"user",content:"Say: hello"}]
        }),
        signal: AbortSignal.timeout(10000)
      });
      const body = await res.text();
      results[model] = { status: res.status, body: body.substring(0,150) };
      if (res.status === 200) break; // found working model
    } catch(e) {
      results[model] = { error: e.message };
    }
  }

  return {
    statusCode:200,
    headers:{"Content-Type":"application/json","Access-Control-Allow-Origin":"*"},
    body: JSON.stringify({ results, key_prefix: ANTHROPIC_KEY.substring(0,8)+"..." })
  };
};

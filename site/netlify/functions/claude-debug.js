exports.handler = async (event) => {
  const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY || "";
  
  if (!ANTHROPIC_KEY) {
    return { statusCode:200, headers:{"Content-Type":"application/json"},
             body: JSON.stringify({error:"No ANTHROPIC_API_KEY", debug:true}) };
  }

  try {
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method:"POST",
      headers:{"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","Content-Type":"application/json"},
      body: JSON.stringify({
        model:"claude-haiku-4-5-20251001",max_tokens:200,
        messages:[{role:"user",content:'Reply with this exact JSON: [{"i":1,"k":"NYC Test","d":"Test deck sentence."}]'}]
      }),
      signal: AbortSignal.timeout(8000)
    });
    const cd  = await res.json();
    const raw = cd.content?.[0]?.text || "";
    return {
      statusCode:200,
      headers:{"Content-Type":"application/json","Access-Control-Allow-Origin":"*"},
      body: JSON.stringify({
        claude_status: res.status,
        claude_raw: raw,
        claude_model: cd.model,
        debug: true
      })
    };
  } catch(e) {
    return { statusCode:200, headers:{"Content-Type":"application/json"},
             body: JSON.stringify({error: e.message, debug:true}) };
  }
};

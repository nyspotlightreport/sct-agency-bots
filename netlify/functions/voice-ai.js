// netlify/functions/voice-ai.js
// ProFlow Voice AI — Real-time voice call handler
// Twilio calls this for every voice interaction.
const https = require('https');

const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY;
const ELEVEN_KEY = process.env.ELEVENLABS_API_KEY;

const AGENTS = {
  receptionist: {
    greeting: "Thank you for calling ProFlow by NY Spotlight Report. My name is Emma. How can I help you today?",
    system: "You are Emma, a warm professional receptionist. Keep responses under 2 sentences. Route callers to the right service.",
    voice: "Polly.Joanna"
  },
  sales_outbound: {
    greeting: "Hi, this is Michael from ProFlow. I noticed your agency could benefit from automated content. Do you have a moment?",
    system: "You are Michael, a consultative sales rep. Keep responses under 2 sentences. Goal: book a 15-min demo.",
    voice: "Polly.Matthew"
  },
  sales_inbound: {
    greeting: "Thanks for calling ProFlow! I'd love to learn about your business and find the right plan for you.",
    system: "You are handling inbound sales. Qualify the lead, match them to a plan, book a demo or start trial.",
    voice: "Polly.Joanna"
  },
  customer_support: {
    greeting: "Thank you for calling ProFlow support. I'm here to help. What's going on?",
    system: "You are a support specialist. Acknowledge, diagnose, solve. Keep responses under 2 sentences.",
    voice: "Polly.Joanna"
  }
};

function claudeRespond(system, userText) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      model: 'claude-sonnet-4-20250514', max_tokens: 150,
      system: system,
      messages: [{ role: 'user', content: userText }]
    });
    const req = https.request({
      hostname: 'api.anthropic.com', path: '/v1/messages', method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Length': Buffer.byteLength(data) }
    }, res => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(body).content[0].text); }
        catch (e) { resolve("Let me connect you with someone who can help."); }
      });
    });
    req.on('error', () => resolve("Let me transfer you to our team."));
    req.setTimeout(10000, () => { req.destroy(); resolve("One moment please."); });
    req.write(data); req.end();
  });
}

exports.handler = async (event) => {
  const params = event.queryStringParameters || {};
  const body = new URLSearchParams(event.body || '');
  const agentType = params.agent || 'receptionist';
  const action = params.action || 'greet';
  const agent = AGENTS[agentType] || AGENTS.receptionist;

  // Initial greeting
  if (action === 'greet' || !body.get('SpeechResult')) {
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'text/xml' },
      body: `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="${agent.voice}">${agent.greeting}</Say>
  <Gather input="speech" timeout="5" speechTimeout="auto" action="/.netlify/functions/voice-ai?agent=${agentType}&action=process" method="POST">
    <Say voice="${agent.voice}">Go ahead, I'm listening.</Say>
  </Gather>
</Response>`
    };
  }

  // Process speech input
  if (action === 'process') {
    const speechResult = body.get('SpeechResult') || '';
    const confidence = parseFloat(body.get('Confidence') || '0');

    if (!speechResult || confidence < 0.3) {
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'text/xml' },
        body: `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="${agent.voice}">I didn't quite catch that. Could you repeat that?</Say>
  <Gather input="speech" timeout="5" speechTimeout="auto" action="/.netlify/functions/voice-ai?agent=${agentType}&action=process" method="POST">
    <Say voice="${agent.voice}">I'm ready when you are.</Say>
  </Gather>
</Response>`
      };
    }

    // Get Claude response
    const aiResponse = await claudeRespond(agent.system, speechResult);

    // Check if the call should end
    const shouldEnd = /goodbye|bye|thank you|that's all|no thanks/i.test(speechResult);

    if (shouldEnd) {
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'text/xml' },
        body: `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="${agent.voice}">${aiResponse} Thank you for calling. Have a great day!</Say>
  <Hangup/>
</Response>`
      };
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'text/xml' },
      body: `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="${agent.voice}">${aiResponse}</Say>
  <Gather input="speech" timeout="5" speechTimeout="auto" action="/.netlify/functions/voice-ai?agent=${agentType}&action=process" method="POST">
    <Pause length="1"/>
  </Gather>
</Response>`
    };
  }

  // Transfer action
  if (action === 'transfer') {
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'text/xml' },
      body: `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="${agent.voice}">Let me connect you with our team. One moment please.</Say>
  <Dial>+16313751097</Dial>
</Response>`
    };
  }

  // Recording callback
  if (action === 'recording') {
    console.log('Recording available:', body.get('RecordingUrl'));
    return { statusCode: 200, body: 'OK' };
  }

  // Status callback
  if (action === 'status') {
    console.log('Call status:', body.get('CallStatus'), body.get('CallSid'));
    return { statusCode: 200, body: 'OK' };
  }

  return { statusCode: 200, headers: { 'Content-Type': 'text/xml' },
    body: '<Response><Say>ProFlow Voice AI is active.</Say></Response>' };
};

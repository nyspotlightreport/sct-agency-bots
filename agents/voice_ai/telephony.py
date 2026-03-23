#!/usr/bin/env python3
"""
agents/voice_ai/telephony.py — ProFlow Telephony Layer
Real phone call management via Twilio.
Handles: outbound dialing, inbound routing, call recording, DTMF, transfers.
"""
import os,json,logging,base64,time
from datetime import datetime
import urllib.request as urlreq,urllib.parse
log=logging.getLogger("telephony")

TWILIO_SID=os.environ.get("TWILIO_ACCOUNT_SID","")
TWILIO_TOKEN=os.environ.get("TWILIO_AUTH_TOKEN","")
TWILIO_PHONE=os.environ.get("TWILIO_PHONE_NUMBER","")
WEBHOOK_URL=os.environ.get("VOICE_WEBHOOK_URL","https://nyspotlightreport.com/.netlify/functions/voice-ai")

def twilio_api(path, data=None, method="POST"):
    """Call Twilio REST API."""
    if not TWILIO_SID: return {"error":"No Twilio credentials"}
    auth = base64.b64encode(f"{TWILIO_SID}:{TWILIO_TOKEN}".encode()).decode()
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/{path}"
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urlreq.Request(url, data=body, method=method,
        headers={"Authorization":f"Basic {auth}","Content-Type":"application/x-www-form-urlencoded"})
    try:
        with urlreq.urlopen(req, timeout=15) as r: return json.loads(r.read())
    except Exception as e: return {"error":str(e)[:200]}

def make_outbound_call(to_number, agent_type="sales_outbound", context=None):
    """Initiate an outbound call via Twilio."""
    twiml_url = f"{WEBHOOK_URL}?agent={agent_type}"
    if context: twiml_url += f"&ctx={urllib.parse.quote(json.dumps(context)[:500])}"
    result = twilio_api("Calls.json", {
        "To": to_number, "From": TWILIO_PHONE,
        "Url": twiml_url, "Record": "true",
        "RecordingStatusCallback": f"{WEBHOOK_URL}?action=recording",
        "StatusCallback": f"{WEBHOOK_URL}?action=status",
        "Timeout": "30", "MachineDetection": "DetectMessageEnd"
    })
    if "sid" in result:
        log.info(f"  OUTBOUND CALL: {to_number} → SID {result['sid']}")
        return {"call_sid":result["sid"],"status":"initiated","to":to_number,"agent":agent_type}
    return {"error":result.get("error","Failed to initiate call")}

def generate_twiml_greeting(agent_type="receptionist", greeting_text=None):
    """Generate TwiML for inbound call handling."""
    if not greeting_text:
        greetings = {
            "receptionist": "Thank you for calling. How can I help you today?",
            "sales_inbound": "Thanks for your interest. I'd love to learn about your business.",
            "customer_support": "Thank you for calling support. What can I help you with?",
            "appointment_setter": "Hi there. I can help you schedule an appointment.",
        }
        greeting_text = greetings.get(agent_type, "Thank you for calling. How can I help?")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" language="en-US">{greeting_text}</Say>
    <Gather input="speech" timeout="5" speechTimeout="auto" action="{WEBHOOK_URL}?agent={agent_type}&amp;action=process" method="POST">
        <Say voice="Polly.Joanna">I'm listening.</Say>
    </Gather>
    <Say voice="Polly.Joanna">I didn't catch that. Let me transfer you to someone who can help.</Say>
    <Redirect>{WEBHOOK_URL}?action=transfer</Redirect>
</Response>"""

def transfer_call(call_sid, to_number):
    """Transfer an active call to a human agent."""
    result = twilio_api(f"Calls/{call_sid}.json", {
        "Twiml": f'<Response><Dial>{to_number}</Dial></Response>'
    })
    log.info(f"  TRANSFER: {call_sid} → {to_number}")
    return result

def get_call_recording(call_sid):
    """Get recording URL for a completed call."""
    result = twilio_api(f"Calls/{call_sid}/Recordings.json", method="GET")
    if "recordings" in result and result["recordings"]:
        rec = result["recordings"][0]
        return f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Recordings/{rec['sid']}.mp3"
    return None

def get_active_calls():
    """List all currently active calls."""
    result = twilio_api("Calls.json?Status=in-progress", method="GET")
    if "calls" in result: return [{"sid":c["sid"],"to":c["to"],"duration":c["duration"],"status":c["status"]} for c in result["calls"]]
    return []

def buy_phone_number(area_code="631"):
    """Purchase a new phone number for the voice AI system."""
    available = twilio_api(f"AvailablePhoneNumbers/US/Local.json?AreaCode={area_code}&VoiceEnabled=true&Limit=1", method="GET")
    if "available_phone_numbers" in available and available["available_phone_numbers"]:
        number = available["available_phone_numbers"][0]["phone_number"]
        result = twilio_api("IncomingPhoneNumbers.json", {
            "PhoneNumber": number, "VoiceUrl": WEBHOOK_URL, "VoiceMethod": "POST"
        })
        if "sid" in result:
            log.info(f"  PURCHASED: {number}")
            return {"number":number,"sid":result["sid"]}
    return {"error":"No numbers available"}

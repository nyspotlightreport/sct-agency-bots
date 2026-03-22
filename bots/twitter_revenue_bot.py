#!/usr/bin/env python3
"""
bots/twitter_revenue_bot.py
Posts revenue-focused content to Twitter every scheduled run.
Each post includes store link or lead magnet link.
Runs daily but also attached to income_bots to maximize coverage.
"""
import os, json, urllib.request, urllib.parse, hmac, hashlib, base64, time
from datetime import datetime

TW_API_KEY = os.environ.get("TWITTER_API_KEY","")
TW_SECRET  = os.environ.get("TWITTER_API_SECRET","")
TW_AT      = os.environ.get("TWITTER_ACCESS_TOKEN","")
TW_ATS     = os.environ.get("TWITTER_ACCESS_SECRET","")
ANTHROPIC  = os.environ.get("ANTHROPIC_API_KEY","")

STORE = "https://nyspotlightreport.com/store/"

TWEET_TEMPLATES = [
    "Content is the #1 thing holding most businesses back.\n\nNot strategy. Not budget. Not team.\n\nActually creating it consistently.\n\nBuilt AI that does it automatically.\n\n→ {store}",
    "Hired a content team?\n\nOr bought ProFlow AI at $97/mo and let it post daily across 6 platforms automatically.\n\nThe math is not close.\n\n→ {store}",
    "What our AI posts for you every single day:\n\n• Twitter thread\n• LinkedIn article  \n• Blog post\n• Email newsletter\n• SEO content\n\nAll from one brief you write once.\n\n→ {store}",
    "Most marketing agencies charge $3,000/mo to do what our AI does for $97.\n\nNo contract. 30-day money back.\n\n→ {store}",
    "The businesses winning right now aren't creating more content manually.\n\nThey automated it.\n\nHere's how: {store}",
    "Tested ProFlow AI for 30 days:\n\nWeek 1: Setup\nWeek 2: First posts live\nWeek 3: Organic traffic ticked up\nWeek 4: First inbound lead from content\n\n$97/mo well spent → {store}",
]

def post_tweet(text):
    if not all([TW_API_KEY, TW_SECRET, TW_AT, TW_ATS]): return False
    url = 'https://api.twitter.com/2/tweets'
    nonce = base64.b64encode(os.urandom(32)).decode().rstrip('=')
    ts    = str(int(time.time()))
    oauth = {
        'oauth_consumer_key': TW_API_KEY,
        'oauth_nonce': nonce,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': ts,
        'oauth_token': TW_AT,
        'oauth_version': '1.0'
    }
    params_str = '&'.join(f"{urllib.parse.quote(k,'')}" + '=' + 
        f"{urllib.parse.quote(str(v),'')}" for k,v in sorted(oauth.items()))
    base = f"POST&{urllib.parse.quote(url,'')}&{urllib.parse.quote(params_str,'')}"
    key  = f"{urllib.parse.quote(TW_SECRET,'')}&{urllib.parse.quote(TW_ATS,'')}"
    sig  = base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    oauth['oauth_signature'] = sig
    auth = 'OAuth ' + ', '.join(f'{urllib.parse.quote(k,"")}="{urllib.parse.quote(v,"")}"' 
                                  for k,v in sorted(oauth.items()))
    try:
        req = urllib.request.Request(url, data=json.dumps({'text':text}).encode(),
            headers={'Authorization':auth,'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=15) as r: return r.status == 201
    except Exception as e:
        print(f"Tweet failed: {e}"); return False

def run():
    import random
    template = random.choice(TWEET_TEMPLATES)
    tweet    = template.format(store=STORE)
    ok = post_tweet(tweet)
    print(f"Tweet: {'✅ posted' if ok else '❌ failed'}")
    return {"posted": ok}

if __name__ == "__main__": run()

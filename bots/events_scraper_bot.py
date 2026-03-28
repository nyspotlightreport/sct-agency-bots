"""
events_scraper_bot.py — NYC Events Intelligence Bot
Scrapes Ticketmaster + Eventbrite for upcoming NYC events
→ Creates site content, social posts, and content opportunities
→ Identifies high-profile events for coverage pitches
Runs: Daily 5am ET
"""
import os, json, urllib.request, urllib.parse, datetime, time

class EventsScraperBot:
    def __init__(self):
        self.ticketmaster_key = os.environ.get("TICKETMASTER_API_KEY","")
        self.eventbrite_key   = os.environ.get("EVENTBRITE_API_KEY","")
        self.anthropic_key    = os.environ.get("ANTHROPIC_API_KEY","")
        self.publer_key       = os.environ.get("PUBLER_API_KEY","")
        self.publer_ws_id     = os.environ.get("PUBLER_WORKSPACE_ID","")

    def fetch_ticketmaster_events(self, days_ahead=14, max_events=20):
        """Get upcoming NYC events from Ticketmaster"""
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=days_ahead)

        if not self.ticketmaster_key:
            print("⚠️ No Ticketmaster key — using RSS fallback")
            return self._fetch_events_from_rss()

        try:
            params = {
                "apikey": self.ticketmaster_key,
                "city": "New York",
                "stateCode": "NY",
                "countryCode": "US",
                "size": max_events,
                "sort": "date,asc",
                "startDateTime": f"{today.isoformat()}T00:00:00Z",
                "endDateTime": f"{end_date.isoformat()}T23:59:59Z",
                "classificationName": "Music,Arts & Theatre,Sports"
            }
            url = "https://app.ticketmaster.com/discovery/v2/events.json?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())

            events = []
            for event in data.get("_embedded",{}).get("events",[]):
                venue = event.get("_embedded",{}).get("venues",[{}])[0]
                events.append({
                    "name": event.get("name",""),
                    "date": event.get("dates",{}).get("start",{}).get("localDate",""),
                    "venue": venue.get("name",""),
                    "url": event.get("url",""),
                    "genre": event.get("classifications",[{}])[0].get("genre",{}).get("name",""),
                    "price_min": event.get("priceRanges",[{}])[0].get("min","") if event.get("priceRanges") else "",
                    "source": "ticketmaster"
                })
            return events
        except Exception as e:
            print(f"Ticketmaster error: {e}")
            return self._fetch_events_from_rss()

    def _fetch_events_from_rss(self):
        """Fallback: NYC event RSS feeds"""
        events = []
        feeds = [
            "https://api.eventful.com/rest/events/search?location=New+York+City&date=Future&page_size=10",
        ]
        # Use NYC.gov events as free fallback
        try:
            req = urllib.request.Request(
                "https://www.nyc.gov/events/api/events?format=json&limit=10",
                headers={"User-Agent":"NYSpotlightBot/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            for event in (data if isinstance(data, list) else [])[:10]:
                events.append({
                    "name": event.get("name","") or event.get("title",""),
                    "date": event.get("startDate","") or event.get("date",""),
                    "venue": event.get("location","NYC"),
                    "url": event.get("url",""),
                    "source": "nyc_gov"
                })
        except Exception as _silent_e:
            import logging; logging.getLogger(__name__).error("Error in %s: %s", __file__, _silent_e)
        return events

    def fetch_eventbrite_events(self):
        """Get events from Eventbrite"""
        if not self.eventbrite_key:
            return []
        try:
            req = urllib.request.Request(
                f"https://www.eventbriteapi.com/v3/events/search/?location.address=New+York+City&location.within=5km&expand=venue,ticket_classes&sort_by=date&token={self.eventbrite_key}",
                headers={"User-Agent":"NYSpotlightBot/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            events = []
            for event in data.get("events",[])[:15]:
                events.append({
                    "name": event.get("name",{}).get("text",""),
                    "date": event.get("start",{}).get("local","")[:10],
                    "venue": event.get("venue",{}).get("name","NYC"),
                    "url": event.get("url",""),
                    "source": "eventbrite",
                    "is_free": event.get("is_free",False),
                    "capacity": event.get("capacity","")
                })
            return events
        except Exception as e:
            print(f"Eventbrite error: {e}")
            return []

    def identify_coverage_opportunities(self, events):
        """Use Claude to flag which events are worth covering"""
        if not self.anthropic_key or not events:
            return events[:5]  # Return top 5 by default

        event_list = "\n".join([f"- {e.get('name','')} | {e.get('date','')} | {e.get('venue','')}" for e in events[:15]])

        prompt = f"""You are an entertainment editor at NY Spotlight Report.
Review these upcoming NYC events and rank the top 5 for editorial coverage value.
Consider: celebrity factor, cultural impact, reader interest, newsworthiness.

Events:
{event_list}

Return ONLY a JSON array of 5 event names in order:
["Event Name 1", "Event Name 2", "Event Name 3", "Event Name 4", "Event Name 5"]"""

        try:
            req_data = json.dumps({
                "model":"claude-haiku-4-5-20251001","max_tokens":200,
                "messages":[{"role":"user","content":prompt}]
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=req_data,
                headers={"x-api-key":self.anthropic_key,"anthropic-version":"2023-06-01","Content-Type":"application/json"}
            )
            with urllib.request.urlopen(req, timeout=12) as r:
                resp = json.loads(r.read())
                raw = resp.get("content",[{}])[0].get("text","")
                import re
                match = re.search(r'\[[\s\S]*?\]', raw)
                if match:
                    top_names = json.loads(match.group())
                    top_events = [e for e in events if any(n.lower() in e.get("name","").lower() for n in top_names)]
                    return top_events[:5]
        except Exception as e:
            print(f"Claude ranking error: {e}")
        return events[:5]

    def generate_social_post(self, event):
        """Create social media post for an upcoming event"""
        name = event.get("name","NYC Event")
        date = event.get("date","")
        venue = event.get("venue","NYC")
        url = event.get("url","https://nyspotlightreport.com")

        return f"""🗽 COMING TO NYC: {name}

📅 {date}
📍 {venue}

Don't miss it → {url}

#NYC #NewYork #Entertainment #NYEvents #Broadway"""

    def create_publer_posts_for_events(self, events):
        """Schedule event posts to Publer"""
        if not self.publer_key:
            return 0

        posted = 0
        for i, event in enumerate(events[:5]):
            caption = self.generate_social_post(event)
            payload = json.dumps({
                "post": {
                    "workspace_id": self.publer_ws_id,
                    "type": "feed",
                    "status": "draft",
                    "content": caption
                }
            }).encode()

            req = urllib.request.Request(
                "https://api.publer.io/v1/posts",
                data=payload,
                headers={"Authorization":f"Bearer {self.publer_key}","Content-Type":"application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    posted += 1
            except Exception as e:
                print(f"Publer event post error: {e}")
            time.sleep(0.5)
        return posted

    def run(self):
        print("=== EVENTS SCRAPER BOT STARTING ===")
        all_events = []

        print("1. Fetching Ticketmaster events...")
        tm_events = self.fetch_ticketmaster_events()
        print(f"   Got {len(tm_events)} events")
        all_events.extend(tm_events)

        print("2. Fetching Eventbrite events...")
        eb_events = self.fetch_eventbrite_events()
        print(f"   Got {len(eb_events)} events")
        all_events.extend(eb_events)

        print(f"\nTotal: {len(all_events)} events found")

        print("3. Identifying coverage opportunities...")
        top_events = self.identify_coverage_opportunities(all_events)
        print(f"   Top picks: {[e.get('name','?')[:30] for e in top_events]}")

        print("4. Creating social posts in Publer...")
        posted = self.create_publer_posts_for_events(top_events)
        print(f"   Created {posted} Publer drafts")

        # Save all events
        with open("/tmp/nyc_events.json","w") as f:
            json.dump(all_events, f, indent=2)
        print(f"✅ Saved {len(all_events)} events to /tmp/nyc_events.json")

        return {"total_events":len(all_events),"top_picks":len(top_events),"posts_created":posted}

if __name__ == "__main__":
    bot = EventsScraperBot()
    bot.run()

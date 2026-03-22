"""
google_maps_scraper_bot.py — NYC Entertainment Lead Scraper
Scrapes Google Maps for entertainment businesses → HubSpot CRM → outreach pipeline
Categories: venues, theaters, clubs, studios, agencies, PR firms, promoters
Runs: Weekly Sunday 10am ET
Revenue: Sell leads OR use for direct outreach → $0.50-$5/lead
"""
import os, json, urllib.request, urllib.parse, time, datetime

class GoogleMapsScraperBot:
    def __init__(self):
        self.gmaps_key    = os.environ.get("GOOGLE_MAPS_API_KEY","")
        self.hubspot_key  = os.environ.get("HUBSPOT_API_KEY","")
        self.anthropic_key= os.environ.get("ANTHROPIC_API_KEY","")

        # NYC entertainment business categories to scrape
        self.search_queries = [
            "Broadway theater production company New York",
            "entertainment PR firm New York City",
            "music venue Manhattan",
            "film production company New York",
            "talent agency New York",
            "event promoter New York City",
            "nightclub Manhattan",
            "comedy club New York",
            "recording studio Brooklyn",
            "fashion showroom New York",
            "casting agency New York",
            "entertainment law firm New York",
            "concert venue New York",
            "arts gallery Chelsea New York",
            "luxury event venue Manhattan",
        ]

    def scrape_google_maps(self, query, max_results=20):
        """Use Google Places API to get businesses"""
        if not self.gmaps_key:
            print(f"⚠️ No Google Maps API key — using demo data for: {query[:40]}")
            return self._demo_leads(query)

        leads = []
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={urllib.parse.quote(query)}&key={self.gmaps_key}&type=establishment"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())

            for place in data.get("results",[])[:max_results]:
                place_id = place.get("place_id","")
                lead = {
                    "name": place.get("name",""),
                    "address": place.get("formatted_address",""),
                    "rating": place.get("rating",0),
                    "review_count": place.get("user_ratings_total",0),
                    "types": place.get("types",[]),
                    "place_id": place_id,
                    "query_category": query,
                    "source": "google_maps"
                }
                # Get details (phone, website)
                if place_id:
                    details = self._get_place_details(place_id)
                    lead.update(details)
                leads.append(lead)
                time.sleep(0.1)  # Rate limit
        except Exception as e:
            print(f"Maps error for '{query[:40]}': {e}")
        return leads

    def _get_place_details(self, place_id):
        """Get phone + website from Places Details API"""
        if not self.gmaps_key:
            return {}
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_phone_number,website,opening_hours,url&key={self.gmaps_key}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            result = data.get("result",{})
            return {
                "phone": result.get("formatted_phone_number",""),
                "website": result.get("website",""),
                "maps_url": result.get("url","")
            }
        except: return {}

    def _demo_leads(self, query):
        """Demo data when no API key"""
        return [
            {"name":"[Demo] NYC Entertainment Co","address":"123 Broadway, New York, NY","rating":4.5,
             "phone":"212-555-0100","website":"example.com","query_category":query,"source":"demo"},
        ]

    def score_lead(self, lead):
        """Score lead quality 1-10"""
        score = 5
        if lead.get("rating",0) >= 4.0: score += 2
        if lead.get("review_count",0) >= 50: score += 1
        if lead.get("website"): score += 1
        if lead.get("phone"): score += 1
        return min(score, 10)

    def generate_outreach_email(self, lead):
        """Use Claude to write personalized outreach for each lead"""
        if not self.anthropic_key:
            return f"Hi, I'm reaching out from NY Spotlight Report regarding potential media coverage for {lead.get('name','your business')}."

        prompt = f"""Write a 3-sentence cold outreach email for NY Spotlight Report (nyspotlightreport.com) to:
Business: {lead.get('name','')}
Category: {lead.get('query_category','')}
Rating: {lead.get('rating','')} stars

Goal: Get them to discuss media coverage, advertising, or partnership with our entertainment publication.
Tone: Professional, brief, value-first. No fluff.
Return ONLY the email body text, no subject line."""

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
                return resp.get("content",[{}])[0].get("text","")
        except Exception as e:
            return f"Hi, reaching out from NY Spotlight Report about coverage opportunities for {lead.get('name','')}."

    def push_to_hubspot(self, lead, outreach_email):
        """Add scraped lead as HubSpot company + contact"""
        if not self.hubspot_key:
            print(f"⚠️ No HubSpot key — lead: {lead.get('name','?')}")
            return False

        # Create company
        company_payload = json.dumps({
            "properties": {
                "name": lead.get("name",""),
                "domain": lead.get("website","").replace("https://","").replace("http://","").split("/")[0],
                "phone": lead.get("phone",""),
                "address": lead.get("address",""),
                "city": "New York",
                "state": "New York",
                "country": "United States",
                "lead_source": "Google Maps Scraper",
                "industry": "ENTERTAINMENT",
                "description": f"Source: {lead.get('query_category','')}\nRating: {lead.get('rating','')}★ ({lead.get('review_count','')} reviews)\nOutreach: {outreach_email[:200]}"
            }
        }).encode()

        req = urllib.request.Request(
            "https://api.hubapi.com/crm/v3/objects/companies",
            data=company_payload,
            headers={"Authorization":f"Bearer {self.hubspot_key}","Content-Type":"application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                result = json.loads(r.read())
                return result.get("id","")
        except urllib.error.HTTPError as e:
            if e.code == 409: return "exists"  # Already in CRM
            print(f"HubSpot company error: {e.code}")
            return False

    def save_leads_csv(self, all_leads):
        """Save leads to CSV for download/sale"""
        import csv, io
        output = io.StringIO()
        fieldnames = ["name","address","phone","website","rating","review_count","query_category","score","maps_url"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for lead in all_leads:
            writer.writerow(lead)
        csv_content = output.getvalue()
        with open("/tmp/nyc_entertainment_leads.csv","w") as f:
            f.write(csv_content)
        print(f"✅ Saved {len(all_leads)} leads to /tmp/nyc_entertainment_leads.csv")
        return csv_content

    def run(self):
        print("=== GOOGLE MAPS LEAD SCRAPER STARTING ===")
        all_leads = []
        high_value_leads = []

        # Scrape top 5 categories (rate limits)
        for query in self.search_queries[:5]:
            print(f"Scraping: {query[:50]}...")
            leads = self.scrape_google_maps(query, max_results=10)
            for lead in leads:
                lead["score"] = self.score_lead(lead)
            all_leads.extend(leads)
            time.sleep(1)  # Rate limiting

        # Deduplicate by name
        seen = set()
        unique_leads = []
        for lead in all_leads:
            key = lead.get("name","").lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique_leads.append(lead)

        # Score and filter high-value
        unique_leads.sort(key=lambda x: x.get("score",0), reverse=True)
        high_value_leads = [l for l in unique_leads if l.get("score",0) >= 7]

        print(f"\nTotal leads: {len(unique_leads)} | High-value: {len(high_value_leads)}")

        # Push top leads to HubSpot + generate outreach
        pushed = 0
        for lead in high_value_leads[:20]:  # Limit to top 20
            email = self.generate_outreach_email(lead)
            lead["outreach_email"] = email
            result = self.push_to_hubspot(lead, email)
            if result:
                pushed += 1
            time.sleep(0.5)

        # Save all to CSV
        self.save_leads_csv(unique_leads)

        print(f"\n✅ SCRAPER COMPLETE: {len(unique_leads)} leads found, {pushed} pushed to HubSpot")
        return {"total_leads":len(unique_leads),"high_value":len(high_value_leads),"hubspot_pushed":pushed}

if __name__ == "__main__":
    bot = GoogleMapsScraperBot()
    bot.run()

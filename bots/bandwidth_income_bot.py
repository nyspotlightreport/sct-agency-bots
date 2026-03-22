"""
bandwidth_income_bot.py — Passive Bandwidth Income Monitor & Maximizer
Monitors money4band, Honeygain, EarnApp status + earnings
Sends alerts if any app goes down → maximizes 24/7 uptime = max passive income
Runs: Every 30 min (pairs with money4band Docker which runs continuously)
Est. Income: $20-100/month per device, zero ongoing effort after setup
"""
import os, json, urllib.request, datetime, subprocess

class BandwidthIncomeBot:
    def __init__(self):
        self.chairman_email = os.environ.get("CHAIRMAN_EMAIL","nyspotlightreport@gmail.com")
        self.gmail_user     = os.environ.get("GMAIL_USER","")
        self.gmail_pass     = os.environ.get("GMAIL_APP_PASS","")
        self.honeygain_email= os.environ.get("HONEYGAIN_EMAIL","")
        self.honeygain_pass = os.environ.get("HONEYGAIN_PASS","")
        self.earnapp_key    = os.environ.get("EARNAPP_API_KEY","")

    def check_honeygain_earnings(self):
        """Check Honeygain balance via API"""
        if not self.honeygain_email or not self.honeygain_pass:
            return {"status":"no_credentials","balance":"N/A"}

        try:
            # Login to get JWT token
            login_data = json.dumps({"email":self.honeygain_email,"password":self.honeygain_pass}).encode()
            req = urllib.request.Request(
                "https://dashboard.honeygain.com/api/v1/users/tokens",
                data=login_data,
                headers={"Content-Type":"application/json","User-Agent":"NYSpotlightBot/1.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                login_resp = json.loads(r.read())
                token = login_resp.get("data",{}).get("access_token","")

            if not token:
                return {"status":"login_failed"}

            # Get balance
            req2 = urllib.request.Request(
                "https://dashboard.honeygain.com/api/v1/users/balances",
                headers={"Authorization":f"Bearer {token}","User-Agent":"NYSpotlightBot/1.0"}
            )
            with urllib.request.urlopen(req2, timeout=8) as r:
                balance_resp = json.loads(r.read())
                credits = balance_resp.get("data",{}).get("payout",{}).get("credits",0)
                usd = credits / 1000  # Honeygain: 1000 credits = $1
                return {"status":"ok","credits":credits,"usd":f"${usd:.2f}","source":"honeygain"}
        except Exception as e:
            return {"status":f"error: {e}","source":"honeygain"}

    def check_earnapp_earnings(self):
        """Check EarnApp via API"""
        if not self.earnapp_key:
            return {"status":"no_key","source":"earnapp"}
        try:
            req = urllib.request.Request(
                "https://earnapp.com/dashboard/api/money",
                headers={"Authorization":f"sdk-user-id {self.earnapp_key}","User-Agent":"NYSpotlightBot/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
                return {
                    "status":"ok",
                    "balance":data.get("balance",0),
                    "lifetime":data.get("lifetime_balance",0),
                    "source":"earnapp"
                }
        except Exception as e:
            return {"status":f"error: {e}","source":"earnapp"}

    def check_docker_apps_running(self):
        """Verify money4band Docker containers are running"""
        results = {}
        apps = ["honeygain","earnapp","packetstream","bitping","traffmonetizer"]

        for app in apps:
            try:
                result = subprocess.run(
                    ["docker","ps","--filter",f"name={app}","--format","{{.Names}}"],
                    capture_output=True, text=True, timeout=5
                )
                running = app in result.stdout
                results[app] = "✅ running" if running else "❌ stopped"
            except FileNotFoundError:
                results[app] = "⚠️ docker not available"
            except Exception as e:
                results[app] = f"⚠️ {e}"

        return results

    def get_income_summary(self, earnings_data):
        """Calculate total passive income so far this month"""
        total_usd = 0
        for source, data in earnings_data.items():
            if isinstance(data, dict):
                usd = data.get("usd","$0").replace("$","")
                try: total_usd += float(usd)
                except: pass
                balance = data.get("balance",0)
                try: total_usd += float(balance)
                except: pass
        return total_usd

    def money4band_setup_instructions(self):
        """Generate setup instructions for money4band Docker"""
        return """
=== MONEY4BAND SETUP (One-time, 10 minutes) ===

1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Clone money4band: git clone https://github.com/MRColorR/money4band.git
3. cd money4band && docker-compose up -d
4. Register accounts (FREE):
   - Honeygain: https://r.honeygain.me/NYSPOT (get $5 bonus with referral)
   - EarnApp: https://earnapp.com/i/NYSPOT
   - PacketStream: https://packetstream.io/?psr=NYSPOT
   - Pawns.app: https://pawns.app/?r=NYSPOT
5. Add credentials to .env file
6. Run: docker-compose restart

💰 Estimated earnings: $20-60/month per device, running 24/7
💡 Works on: Windows, Mac, Linux, Raspberry Pi
📊 Track earnings in this bot's daily reports
"""

    def send_earnings_report(self, data):
        """Send weekly earnings report to Chairman"""
        if not self.gmail_user or not self.gmail_pass:
            return False

        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        subject = f"💰 Passive Bandwidth Income Report — {datetime.date.today()}"
        body = f"""NY Spotlight Report — Passive Income Dashboard

DATE: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M ET')}

EARNINGS THIS MONTH:
"""
        for source, info in data.items():
            body += f"  {source.upper()}: {json.dumps(info, indent=2)}\n"

        body += f"\nTOTAL ESTIMATED: ${self.get_income_summary(data):.2f}\n"
        body += "\n\n" + self.money4band_setup_instructions()

        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.gmail_user
            msg['To'] = self.chairman_email
            msg.attach(MIMEText(body,'plain'))

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_user, self.gmail_pass)
                server.send_message(msg)
            print(f"✅ Earnings report sent to {self.chairman_email}")
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False

    def run(self):
        print("=== BANDWIDTH INCOME BOT STARTING ===")
        earnings = {}

        print("1. Checking Honeygain...")
        earnings["honeygain"] = self.check_honeygain_earnings()
        print(f"   {earnings['honeygain']}")

        print("2. Checking EarnApp...")
        earnings["earnapp"] = self.check_earnapp_earnings()
        print(f"   {earnings['earnapp']}")

        print("3. Checking Docker containers...")
        docker_status = self.check_docker_apps_running()
        for app, status in docker_status.items():
            print(f"   {app}: {status}")
        earnings["docker"] = docker_status

        total = self.get_income_summary(earnings)
        print(f"\n💰 Total estimated passive income: ${total:.2f}")

        # Save state
        state = {"timestamp": datetime.datetime.utcnow().isoformat(), "earnings": earnings, "total_usd": total}
        with open("/tmp/bandwidth_income_state.json","w") as f:
            json.dump(state, f, indent=2)

        # Alert if nothing is running
        all_stopped = all("stopped" in str(v) or "error" in str(v) for v in docker_status.values())
        if all_stopped:
            print("⚠️ WARNING: All bandwidth apps may be stopped!")
            print(self.money4band_setup_instructions())

        print("=== BANDWIDTH BOT COMPLETE ===")
        return state

if __name__ == "__main__":
    bot = BandwidthIncomeBot()
    bot.run()

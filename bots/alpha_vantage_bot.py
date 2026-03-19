#!/usr/bin/env python3
"""
ALPHA VANTAGE BOT v1.0 — S.C. Thomas Internal Agency
Pulls financial market data for content creation, alerts, and reports.
- Daily market summary for NY Spotlight Report content
- Stock/crypto price alerts
- Financial data for article context
- Feeds into news_digest_bot for financial content angles
Free tier: 25 requests/day | 500/day on standard free key
Schedule: Daily 8:00 AM ET
"""
import os, sys, json, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, ClaudeClient, AlertSystem, with_retry

class AlphaVantageBot(BaseBot):
    VERSION = "1.0.0"
    BASE    = "https://www.alphavantage.co/query"
    KEY     = os.getenv("ALPHA_VANTAGE_API_KEY", "")

    # Stocks/assets to track — customize these
    WATCHLIST = os.getenv("AV_WATCHLIST", "AAPL,MSFT,GOOGL,META,NVDA").split(",")
    CRYPTO    = os.getenv("AV_CRYPTO",    "BTC,ETH").split(",")

    def __init__(self):
        super().__init__("alpha-vantage")

    def _get(self, params: dict) -> dict:
        params["apikey"] = self.KEY
        url = f"{self.BASE}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent":"SCT-Agency/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    @with_retry(max_retries=2, delay=3.0)
    def get_quote(self, symbol: str) -> dict:
        """Get current stock quote"""
        data = self._get({"function": "GLOBAL_QUOTE", "symbol": symbol})
        q    = data.get("Global Quote", {})
        if not q:
            return {}
        return {
            "symbol":  symbol,
            "price":   float(q.get("05. price", 0)),
            "change":  float(q.get("09. change", 0)),
            "pct":     float(q.get("10. change percent", "0%").replace("%","")),
            "volume":  int(q.get("06. volume", 0)),
            "high":    float(q.get("03. high", 0)),
            "low":     float(q.get("04. low", 0)),
        }

    @with_retry(max_retries=2, delay=3.0)
    def get_crypto(self, symbol: str, market: str = "USD") -> dict:
        """Get crypto exchange rate"""
        data = self._get({
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": symbol,
            "to_currency": market
        })
        r = data.get("Realtime Currency Exchange Rate", {})
        if not r:
            return {}
        return {
            "symbol": symbol,
            "price":  float(r.get("5. Exchange Rate", 0)),
            "market": market,
            "time":   r.get("6. Last Refreshed", ""),
        }

    @with_retry(max_retries=2, delay=3.0)
    def get_market_sentiment(self, tickers: str = "AAPL") -> dict:
        """Get news sentiment for tickers"""
        data = self._get({
            "function": "NEWS_SENTIMENT",
            "tickers":  tickers,
            "limit":    "10"
        })
        return data.get("feed", [])

    def write_market_brief(self, quotes: list, crypto: list) -> str:
        """Use Claude to write a market brief for content"""
        if not quotes:
            return ""

        market_data = "\n".join([
            f"  {q['symbol']}: ${q['price']:,.2f} ({'+' if q['pct']>0 else ''}{q['pct']:.2f}%)"
            for q in quotes if q
        ])
        crypto_data = "\n".join([
            f"  {c['symbol']}: ${c['price']:,.2f}"
            for c in crypto if c
        ]) if crypto else "  N/A"

        system = "You are a financial journalist writing for NY Spotlight Report."
        prompt = f"""Write a 3-sentence market brief for today's content.

Stocks:
{market_data}

Crypto:
{crypto_data}

Write it as a punchy opening for a financial news post. Professional, direct, no fluff."""

        return ClaudeClient.complete_safe(
            system=system, user=prompt, max_tokens=200,
            fallback=f"Markets: {market_data}"
        )

    def execute(self) -> dict:
        if not self.KEY:
            self.logger.warning(
                "No ALPHA_VANTAGE_API_KEY set. "
                "Get free key at: alphavantage.co/support/#api-key"
            )
            return {"error": "No API key"}

        self.logger.info(f"Fetching data for {len(self.WATCHLIST)} symbols...")

        quotes = []
        for symbol in self.WATCHLIST[:5]:  # Conserve free tier quota
            q = self.get_quote(symbol.strip())
            if q:
                quotes.append(q)

        crypto_quotes = []
        for symbol in self.CRYPTO[:2]:
            c = self.get_crypto(symbol.strip())
            if c:
                crypto_quotes.append(c)

        # Write market brief
        brief = self.write_market_brief(quotes, crypto_quotes)

        # Queue for social posting
        if brief:
            pending = self.state.get("pending_posts", [])
            pending.append({
                "text":     brief,
                "platforms":["linkedin", "twitter"],
                "source":   "alpha_vantage"
            })
            self.state.set("pending_posts", pending)

        # Save data
        self.state.set("latest_market_data", {
            "stocks":    quotes,
            "crypto":    crypto_quotes,
            "brief":     brief,
            "timestamp": datetime.now().isoformat(),
        })

        # Alert with summary
        movers = [q for q in quotes if abs(q.get("pct", 0)) > 2]
        if movers:
            mover_text = " | ".join([
                f"{q['symbol']} {'+' if q['pct']>0 else ''}{q['pct']:.1f}%"
                for q in movers
            ])
            AlertSystem.send(
                subject  = f"📈 Market Movers: {mover_text}",
                body_html= f"""
<h3>Market Alert — {datetime.now().strftime('%b %d, %Y')}</h3>
<p><strong>Big Movers (+/-2%):</strong> {mover_text}</p>
<p><strong>Market Brief:</strong><br>{brief}</p>""",
                severity = "INFO"
            )

        self.log_summary(symbols_fetched=len(quotes))
        return {"quotes": len(quotes), "brief": bool(brief)}

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--quote",  type=str, help="Get quote for symbol (e.g. AAPL)")
    p.add_argument("--crypto", type=str, help="Get crypto price (e.g. BTC)")
    p.add_argument("--brief",  action="store_true", help="Generate market brief")
    args = p.parse_args()

    bot = AlphaVantageBot()
    if args.quote:
        q = bot.get_quote(args.quote.upper())
        print(f"{q['symbol']}: ${q['price']:,.2f} ({'+' if q['pct']>0 else ''}{q['pct']:.2f}%)")
    elif args.crypto:
        c = bot.get_crypto(args.crypto.upper())
        print(f"{c['symbol']}: ${c['price']:,.2f} USD")
    else:
        bot.run()

# SETUP:
# 1. Get free key: alphavantage.co/support/#api-key (takes 20 seconds)
# 2. Add to GitHub secrets as: ALPHA_VANTAGE_API_KEY
# 3. Optional: set AV_WATCHLIST="AAPL,MSFT,GOOGL" in secrets
# Free tier: 25 requests/day (more than enough for daily brief)

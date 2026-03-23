#!/usr/bin/env python3
"""
omega_content_intelligence.py — Predictive Content Engine
═════════════════════════════════════════════════════════

Next-gen content engine that replaces static content calendars with:
- Trend prediction (what topics will perform best this week)
- Cross-modal analysis (combine SEO data + social metrics + revenue attribution)
- Autonomous content strategy adjustment based on performance
- Multi-agent creative process (Strategist + Writer + Editor + SEO perspectives)

Schedule: Daily at 5 AM ET
"""

import os, sys, json, logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
log = logging.getLogger("omega_content")

from omega_capabilities import OmegaAgent, _supa, _claude


class OmegaContentIntelligence(OmegaAgent):
    ORG_ID   = "omega_content"
    NAME     = "Omega Content Intelligence"
    DIRECTOR = "S.C. Thomas"
    MISSION  = "Predict winning content, optimize strategy, maximize content-to-revenue conversion"
    VERSION  = "1.0.0"

    TOPIC_CATEGORIES = [
        "broadway", "film", "music", "fashion", "nyc_culture",
        "proflow_product", "ai_business", "passive_income",
    ]

    def execute(self) -> dict:
        results = {"items_processed": 0}

        # ── 1. Analyze Past Content Performance ──────────
        log.info("Analyzing content performance history...")
        content_data = _supa("GET", "analytics_events",
                            "?event=eq.page_view&order=timestamp.desc&limit=500"
                            "&select=page,timestamp") or []

        page_counts = {}
        if content_data and isinstance(content_data, list):
            for event in content_data:
                page = event.get("page", "")
                page_counts[page] = page_counts.get(page, 0) + 1

        top_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        results["top_performing_content"] = [{"page": p, "views": c} for p, c in top_pages]
        results["items_processed"] += 1

        # ── 2. Predict Trending Topics ───────────────────
        log.info("Predicting trending topics for this week...")
        trend_analysis = self.reasoning.reason(
            "Based on the current news cycle, entertainment industry trends, and NYC cultural events, "
            "what are the top 5 topics that will generate the most traffic and engagement this week? "
            "Consider: Broadway openings, film releases, music events, fashion weeks, viral moments.",
            context=f"Top performing content: {json.dumps(results['top_performing_content'][:10])}",
            depth="deep"
        )
        results["trending_topics"] = {
            "prediction": trend_analysis.get("conclusion", ""),
            "confidence": trend_analysis.get("confidence", 0),
            "reasoning": trend_analysis.get("recommended_action", ""),
        }
        results["items_processed"] += 1

        # ── 3. Multi-Agent Creative Strategy ─────────────
        log.info("Building content strategy from multiple perspectives...")
        strategy = self.swarm.gather_perspectives(
            f"Plan the content strategy for this week. "
            f"Top performing topics: {json.dumps([p for p, _ in top_pages[:5]])}. "
            f"Trending prediction: {trend_analysis.get('conclusion', '')[:300]}. "
            f"Goal: maximize traffic-to-subscriber conversion.",
            agent_roles=[
                "Content Strategist — audience engagement and editorial calendar",
                "SEO Specialist — keyword targeting and search intent",
                "Social Media Manager — platform-specific viral potential",
                "Revenue Analyst — content that drives ProFlow sign-ups",
            ]
        )
        results["content_strategy"] = {
            "consensus": strategy.get("consensus", ""),
            "action_plan": strategy.get("recommended_action", ""),
            "confidence": strategy.get("synthesis_confidence", 0),
        }
        results["items_processed"] += 1

        # ── 4. Generate Content Brief ────────────────────
        log.info("Generating optimized content briefs...")
        briefs = self._generate_content_briefs(results)
        results["content_briefs"] = briefs
        results["items_processed"] += 1

        # ── 5. Save Intelligence to Context ──────────────
        _supa("POST", "nysr_live_context", {
            "context_key": "content_intelligence",
            "context_value": json.dumps({
                "trending": results.get("trending_topics", {}),
                "strategy": results.get("content_strategy", {}),
                "briefs": briefs[:3],
            })[:3000],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

        log.info(f"Content intelligence complete: {len(briefs)} briefs generated")
        return results

    def _generate_content_briefs(self, analysis: dict) -> list:
        """Generate actionable content briefs based on all intelligence."""
        system = """You are an elite content strategist for NY Spotlight Report.
Generate 5 content briefs optimized for traffic + conversions.

Return JSON array:
[{
    "title": "Headline",
    "slug": "url-slug",
    "category": "broadway|film|music|fashion|nyc_culture|proflow|ai_business",
    "target_keywords": ["keyword1", "keyword2"],
    "hook": "First sentence that grabs attention",
    "angle": "What makes this piece unique",
    "cta": "Call to action for ProFlow",
    "estimated_traffic": "low|medium|high",
    "priority": 1
}]"""

        trending = analysis.get("trending_topics", {}).get("prediction", "")
        strategy = analysis.get("content_strategy", {}).get("consensus", "")
        top_content = json.dumps(analysis.get("top_performing_content", [])[:5])

        result = _claude(
            f"Trending topics: {trending[:500]}\n"
            f"Strategy: {strategy[:500]}\n"
            f"Past winners: {top_content}",
            system, model="claude-sonnet-4-20250514", max_tokens=2000, temperature=0.6
        )
        if not result: return []

        import re
        text = result.get("content", [{}])[0].get("text", "")
        try:
            return json.loads(re.sub(r"^```(?:json)?\n?|\n?```$", "", text.strip()))
        except Exception:
            return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [OMEGA-CONTENT] %(message)s")
    agent = OmegaContentIntelligence()
    results = agent.run()
    print(json.dumps(results, indent=2, default=str)[:3000])

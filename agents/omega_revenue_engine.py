#!/usr/bin/env python3
"""
omega_revenue_engine.py — Predictive Revenue Intelligence
══════════════════════════════════════════════════════════

Next-gen revenue engine that replaces static pipeline tracking with:
- AI-powered revenue forecasting with confidence intervals
- Anomaly detection on daily revenue (catch $0 days before they happen)
- Scenario modeling for pricing/outreach experiments
- Cross-modal analysis (email metrics + pipeline data + revenue)
- Swarm consensus from Sales, Content, and CRM perspectives

Schedule: Daily at 6 AM ET
"""

import os, sys, json, logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
log = logging.getLogger("omega_revenue")

from omega_capabilities import OmegaAgent, _supa, _claude
from agent_memory import AgentMemory


class OmegaRevenueEngine(OmegaAgent):
    ORG_ID   = "omega_revenue"
    NAME     = "Omega Revenue Engine"
    DIRECTOR = "S.C. Thomas"
    MISSION  = "Predict revenue, detect anomalies, optimize pipeline conversion"
    VERSION  = "1.0.0"

    def __init__(self):
        super().__init__()
        self.memory = AgentMemory("omega_revenue", default_ttl_days=90)

    def execute(self) -> dict:
        results = {"items_processed": 0}

        # Recall past revenue patterns
        past_context = self.memory.recall_as_context("revenue forecast anomaly pipeline", k=5)
        if past_context:
            log.info(f"Recalled past revenue patterns")

        # ── Gather revenue data ──────────────────────────
        revenue_raw = _supa("GET", "revenue_daily",
                           "?order=date.desc&limit=60&select=date,amount,source") or []
        if not revenue_raw:
            log.warning("No revenue data available")
            return results

        revenue_data = [{"date": r["date"], "value": r.get("amount", 0)}
                       for r in reversed(revenue_raw)]

        # ── 1. Revenue Forecast ──────────────────────────
        log.info("Forecasting revenue for next 14 days...")
        forecast = self.predict.forecast(revenue_data, "daily_revenue", 14)
        results["forecast"] = {
            "trend": forecast.get("trend"),
            "next_14_days": forecast.get("ai_enhanced_forecast", []),
            "total_predicted": sum(v for v in forecast.get("ai_enhanced_forecast", []) if isinstance(v, (int, float))),
            "reasoning": forecast.get("ai_reasoning", ""),
        }
        results["items_processed"] += 1

        # ── 2. Anomaly Detection ─────────────────────────
        log.info("Scanning for revenue anomalies...")
        anomalies = self.predict.detect_anomalies(revenue_data, "daily_revenue")
        results["anomalies"] = anomalies
        results["items_processed"] += 1

        if anomalies.get("anomaly_count", 0) > 0:
            # Reason about the anomaly
            reasoning = self.reasoning.reason(
                "Why did these revenue anomalies occur and what should we do?",
                context=json.dumps(anomalies)[:2000],
                depth="deep"
            )
            results["anomaly_reasoning"] = reasoning.get("conclusion", "")
            results["anomaly_action"] = reasoning.get("recommended_action", "")

        # ── 3. Pipeline Analysis ─────────────────────────
        log.info("Analyzing pipeline conversion...")
        pipeline = _supa("GET", "contacts",
                        "?select=stage,lead_score,created_at&stage=neq.CLOSED_LOST&limit=200") or []
        if pipeline and isinstance(pipeline, list):
            stages = {}
            for c in pipeline:
                stage = c.get("stage", "unknown")
                stages[stage] = stages.get(stage, 0) + 1

            hot = [c for c in pipeline if (c.get("lead_score") or 0) >= 70]

            results["pipeline"] = {
                "total": len(pipeline),
                "by_stage": stages,
                "hot_leads": len(hot),
            }
            results["items_processed"] += 1

        # ── 4. Multi-Perspective Revenue Strategy ────────
        log.info("Getting multi-agent revenue perspectives...")
        perspectives = self.swarm.gather_perspectives(
            f"Revenue is {forecast.get('trend', 'unknown')}. "
            f"14-day forecast: ${sum(forecast.get('ai_enhanced_forecast', []))} total. "
            f"Pipeline has {results.get('pipeline', {}).get('hot_leads', 0)} hot leads. "
            f"What's the best revenue play for the next 7 days?",
            agent_roles=[
                "Sales Director — outbound strategy expert",
                "Content Strategist — inbound/SEO expert",
                "CRM Manager — conversion optimization expert",
                "Revenue Operations — pricing and packaging expert",
            ]
        )
        results["strategy"] = {
            "consensus": perspectives.get("consensus", ""),
            "confidence": perspectives.get("synthesis_confidence", 0),
            "action": perspectives.get("recommended_action", ""),
        }
        results["items_processed"] += 1

        # ── 5. Scenario Modeling ─────────────────────────
        log.info("Modeling revenue scenarios...")
        current_avg = statistics_mean(revenue_data[-7:]) if len(revenue_data) >= 7 else 0
        scenarios = [
            {"name": "Double outreach", "description": f"2x cold email volume. Current avg: ${current_avg}/day",
             "variables": {"outreach_multiplier": 2}},
            {"name": "Price increase 20%", "description": "Raise ProFlow prices by 20%",
             "variables": {"price_change": 0.2}},
            {"name": "Launch referral program", "description": "10% commission for referrals",
             "variables": {"referral_commission": 0.1}},
        ]
        scenario_results = self.predict.scenario_model(
            {"current_revenue": current_avg, "pipeline": results.get("pipeline", {})},
            scenarios
        )
        results["scenarios"] = {
            "best": scenario_results.get("best_scenario", ""),
            "recommendation": scenario_results.get("overall_recommendation", ""),
        }
        results["items_processed"] += 1

        log.info(f"Revenue engine complete: forecast={forecast.get('trend')}, "
                f"anomalies={anomalies.get('anomaly_count', 0)}, "
                f"strategy_confidence={results['strategy'].get('confidence', 0)}")

        return results


def statistics_mean(data):
    values = [d.get("value", 0) for d in data]
    return sum(values) / len(values) if values else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [OMEGA-REV] %(message)s")
    agent = OmegaRevenueEngine()
    results = agent.run()
    print(json.dumps(results, indent=2, default=str)[:3000])

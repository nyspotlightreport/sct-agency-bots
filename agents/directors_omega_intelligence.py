#!/usr/bin/env python3
"""
directors_omega_intelligence.py — The Apex Intelligence Agent
═══════════════════════════════════════════════════════════════

The most advanced agent in the system. Coordinates all other agents,
performs system-wide reasoning, and makes strategic decisions using
every capability in the Omega framework.

Capabilities:
  - REAL-TIME REASONING: Processes events, quantifies uncertainty
  - AGENTIC: Full tool-use loops, autonomous task execution
  - MULTIMODAL: Combines text + data + metrics for cross-modal insights
  - GENERATIVE/PREDICTIVE: Revenue forecasting, anomaly detection, scenario modeling
  - SWARM INTELLIGENCE: Multi-agent coordination, consensus building
  - SELF-IMPROVING: Evolves its own strategies based on outcomes

Schedule: Every 4 hours
Mission: Maximize revenue, minimize risk, coordinate all agents optimally

S.C. Thomas — Chairman
"""

import os, sys, json, logging, time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
log = logging.getLogger("omega_director")

try:
    from omega_capabilities import (
        OmegaAgent, RealtimeReasoning, AgenticExecutor,
        MultimodalIntelligence, PredictiveEngine, SwarmIntelligence,
        _supa, _claude
    )
    from agent_memory import AgentMemory
except ImportError as e:
    log.error(f"Import failed: {e}")
    sys.exit(1)


class DirectorsOmegaIntelligence(OmegaAgent):
    ORG_ID   = "directors_omega"
    NAME     = "Director's Omega Intelligence"
    DIRECTOR = "S.C. Thomas"
    MISSION  = ("System-wide strategic intelligence: forecast revenue, detect anomalies, "
                "coordinate agents, identify opportunities, and make data-driven decisions "
                "using every advanced capability available.")
    VERSION  = "1.0.0"

    ENABLE_REASONING  = True
    ENABLE_AGENTIC    = True
    ENABLE_MULTIMODAL = True
    ENABLE_PREDICTIVE = True
    ENABLE_SWARM      = True

    def __init__(self):
        super().__init__()
        self.memory = AgentMemory("directors_omega", default_ttl_days=180)

    def execute(self) -> dict:
        results = {}

        # ── 0. RECALL PAST LEARNINGS ──────────────────────────
        log.info("Phase 0: Recalling past strategic insights...")
        past_insights = self.memory.recall_as_context(
            "revenue strategy anomalies pipeline opportunities", k=10
        )
        if past_insights:
            log.info(f"Recalled {past_insights.count('- [')} past memories")
            results["memory_context"] = past_insights[:500]

        # ── 1. GATHER SYSTEM STATE ────────────────────────────
        log.info("Phase 1: Gathering system-wide intelligence...")
        system_state = self._gather_system_state()
        results["system_state"] = {
            "agents_reporting": system_state.get("agent_count", 0),
            "revenue_7d": system_state.get("revenue_7d", 0),
            "pipeline_contacts": system_state.get("pipeline_count", 0),
        }

        # ── 2. PREDICTIVE ANALYTICS ──────────────────────────
        log.info("Phase 2: Running predictive analytics...")
        if system_state.get("revenue_history"):
            revenue_forecast = self.predict.forecast(
                system_state["revenue_history"], "daily_revenue", 7
            )
            results["revenue_forecast"] = {
                "next_7_days": revenue_forecast.get("ai_enhanced_forecast", []),
                "trend": revenue_forecast.get("trend", "unknown"),
                "confidence_range": {
                    "lower": revenue_forecast.get("confidence_lower", []),
                    "upper": revenue_forecast.get("confidence_upper", []),
                },
            }

            # Anomaly detection on revenue
            anomalies = self.predict.detect_anomalies(
                system_state["revenue_history"], "daily_revenue"
            )
            results["anomalies"] = anomalies
            if anomalies.get("anomaly_count", 0) > 0:
                self.record_error(
                    f"Revenue anomalies detected: {anomalies['anomaly_count']} anomalous days",
                    "warning"
                )

        # ── 3. MULTI-AGENT COORDINATION ──────────────────────
        log.info("Phase 3: Coordinating agent swarm...")
        agent_reports = self._get_agent_reports()
        if agent_reports:
            collective = self.swarm.collective_intelligence(agent_reports)
            results["collective_intelligence"] = {
                "emergent_insights": collective.get("emergent_insights", []),
                "contradictions": len(collective.get("contradictions", [])),
                "coordinated_actions": collective.get("coordinated_actions", []),
                "system_health": collective.get("system_health", 0),
            }

        # ── 4. STRATEGIC REASONING (with memory context) ────
        log.info("Phase 4: Strategic reasoning with uncertainty quantification...")
        strategic_question = self._formulate_strategic_question(system_state, results)
        context_with_memory = json.dumps(results)[:2000]
        if past_insights:
            context_with_memory += f"\n\n{past_insights}"
        reasoning = self.reasoning.reason(
            strategic_question,
            context=context_with_memory[:4000],
            depth="deep"
        )
        results["strategic_reasoning"] = {
            "conclusion": reasoning.get("conclusion", ""),
            "confidence": reasoning.get("confidence", 0),
            "uncertainties": reasoning.get("uncertainties", []),
            "recommended_action": reasoning.get("recommended_action", ""),
        }

        # ── 5. SCENARIO MODELING ─────────────────────────────
        log.info("Phase 5: Scenario modeling...")
        scenarios = self._generate_scenarios(system_state)
        if scenarios:
            scenario_results = self.predict.scenario_model(system_state, scenarios)
            results["scenarios"] = {
                "best_scenario": scenario_results.get("best_scenario", ""),
                "recommendation": scenario_results.get("overall_recommendation", ""),
                "count": len(scenario_results.get("scenarios", [])),
            }

        # ── 6. CROSS-MODAL SYNTHESIS ─────────────────────────
        log.info("Phase 6: Cross-modal synthesis...")
        text_context = self._get_text_context()
        if text_context and system_state:
            cross_modal = self.multimodal.cross_modal_reason(
                text_context,
                {"revenue": system_state.get("revenue_7d", 0),
                 "pipeline": system_state.get("pipeline_count", 0),
                 "agent_health": results.get("collective_intelligence", {}).get("system_health", 0)},
                "What is the single most important action to take right now to maximize revenue?"
            )
            results["cross_modal_synthesis"] = {
                "recommendation": cross_modal.get("synthesis", ""),
                "confidence": cross_modal.get("confidence", 0),
                "actions": cross_modal.get("actionable_recommendations", []),
            }

        # ── 7. GENERATE CHAIRMAN BRIEFING ────────────────────
        log.info("Phase 7: Generating Chairman briefing...")
        briefing = self._generate_briefing(results)
        results["briefing"] = briefing

        # Save briefing to Supabase
        _supa("POST", "chairman_briefing", {
            "briefing_type": "omega_intelligence",
            "content": briefing,
            "metrics": results,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        results["items_processed"] = sum([
            1 if results.get("revenue_forecast") else 0,
            1 if results.get("collective_intelligence") else 0,
            1 if results.get("strategic_reasoning") else 0,
            1 if results.get("scenarios") else 0,
            1 if results.get("cross_modal_synthesis") else 0,
        ])

        # ── 8. STORE LEARNINGS TO MEMORY ─────────────────
        log.info("Phase 8: Storing learnings to persistent memory...")
        strategic = results.get("strategic_reasoning", {})
        if strategic.get("conclusion") and strategic.get("confidence", 0) > 0.5:
            self.memory.store(
                topic="strategic_recommendation",
                content=strategic["conclusion"][:500],
                confidence=strategic["confidence"],
                tags=["strategy", "revenue", results.get("revenue_forecast", {}).get("trend", "")],
                category="strategy",
            )

        forecast = results.get("revenue_forecast", {})
        if forecast.get("trend"):
            self.memory.store(
                topic=f"revenue_trend_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                content=f"Revenue trend: {forecast['trend']}. 7-day forecast: {forecast.get('next_7_days', [])}",
                confidence=0.7,
                tags=["revenue", "forecast", forecast["trend"]],
                category="pattern",
                ttl_days=30,
            )

        anomalies = results.get("anomalies", {})
        if anomalies.get("anomaly_count", 0) > 0:
            self.memory.store(
                topic="revenue_anomaly_detected",
                content=f"{anomalies['anomaly_count']} anomalies. Action: {results.get('anomaly_action', 'investigate')}",
                confidence=0.8,
                tags=["anomaly", "revenue", "alert"],
                category="warning",
                ttl_days=14,
            )

        # Share key insights with other agents
        cross_modal = results.get("cross_modal_synthesis", {})
        if cross_modal.get("recommendation") and cross_modal.get("confidence", 0) > 0.5:
            for target in ["omega_revenue", "omega_content"]:
                self.memory.share(
                    target_agent=target,
                    topic="director_recommendation",
                    content=cross_modal["recommendation"][:300],
                    confidence=cross_modal["confidence"],
                    tags=["director", "strategy"],
                )

        # Cleanup old memories
        self.memory.forget_old(days=180)
        mem_stats = self.memory.get_stats()
        results["memory_stats"] = mem_stats
        log.info(f"Memory: {mem_stats.get('total', 0)} entries, avg confidence {mem_stats.get('avg_confidence', 0):.2f}")

        log.info(f"Omega Intelligence complete: {results['items_processed']} analyses performed")
        return results

    # ── DATA GATHERING ─────────────────────────────────────

    def _gather_system_state(self) -> dict:
        state = {}

        # Revenue (last 30 days)
        revenue = _supa("GET", "revenue_daily",
                        "?order=date.desc&limit=30&select=date,amount") or []
        if revenue:
            state["revenue_history"] = [{"date": r["date"], "value": r.get("amount", 0)}
                                        for r in reversed(revenue)]
            state["revenue_7d"] = sum(r.get("amount", 0) for r in revenue[:7])
            state["revenue_30d"] = sum(r.get("amount", 0) for r in revenue)

        # Pipeline
        contacts = _supa("GET", "contacts",
                         "?stage=neq.CLOSED_LOST&stage=neq.CLOSED_WON&select=id&limit=500") or []
        state["pipeline_count"] = len(contacts) if isinstance(contacts, list) else 0

        hot_leads = _supa("GET", "contacts",
                          "?lead_score=gte.70&stage=neq.CLOSED_WON&select=id&limit=100") or []
        state["hot_leads"] = len(hot_leads) if isinstance(hot_leads, list) else 0

        # Agent health
        recent_runs = _supa("GET", "agent_run_logs",
                            "?order=completed_at.desc&limit=50&select=agent_name,status,performance_score") or []
        if recent_runs and isinstance(recent_runs, list):
            state["agent_count"] = len(set(r.get("agent_name", "") for r in recent_runs))
            failed = [r for r in recent_runs if r.get("status") == "failed"]
            state["agent_failure_rate"] = round(len(failed) / len(recent_runs) * 100, 1)

        return state

    def _get_agent_reports(self) -> list:
        runs = _supa("GET", "agent_run_logs",
                     "?order=completed_at.desc&limit=30"
                     "&select=agent_name,status,performance_score,metrics,errors") or []
        if not runs or not isinstance(runs, list): return []

        reports = []
        seen = set()
        for r in runs:
            name = r.get("agent_name", "")
            if name not in seen:
                seen.add(name)
                reports.append({
                    "agent": name,
                    "status": r.get("status"),
                    "score": r.get("performance_score", 0),
                    "metrics": r.get("metrics", {}),
                    "errors": r.get("errors", []),
                })
        return reports[:15]

    def _formulate_strategic_question(self, state: dict, results: dict) -> str:
        revenue = state.get("revenue_7d", 0)
        pipeline = state.get("pipeline_count", 0)
        hot = state.get("hot_leads", 0)
        fail_rate = state.get("agent_failure_rate", 0)

        return (f"Given: ${revenue} revenue in 7 days, {pipeline} contacts in pipeline, "
                f"{hot} hot leads, {fail_rate}% agent failure rate. "
                f"Revenue trend: {results.get('revenue_forecast', {}).get('trend', 'unknown')}. "
                f"What is the highest-ROI strategic move for the next 48 hours?")

    def _generate_scenarios(self, state: dict) -> list:
        return [
            {"name": "Aggressive outreach", "description": "Triple cold outreach volume for 7 days",
             "variables": {"outreach_volume": 3, "cost_increase": 0.5}},
            {"name": "Content blitz", "description": "Publish 3x daily content + social",
             "variables": {"content_volume": 3, "engagement_goal": 2}},
            {"name": "Conversion optimization", "description": "Focus on closing hot leads only",
             "variables": {"focus": "hot_leads", "new_outreach": 0}},
            {"name": "Status quo", "description": "Continue current operations unchanged",
             "variables": {}},
        ]

    def _get_text_context(self) -> str:
        # Pull recent intelligence briefs
        briefs = _supa("GET", "nysr_live_context",
                       "?order=updated_at.desc&limit=3&select=context_key,context_value") or []
        if briefs and isinstance(briefs, list):
            return "\n".join(f"{b.get('context_key','')}: {str(b.get('context_value',''))[:300]}"
                           for b in briefs)
        return ""

    def _generate_briefing(self, results: dict) -> str:
        system = """You are the Chairman's briefing writer. Write a 5-sentence executive briefing.
Sentence 1: Revenue status and trend.
Sentence 2: Most important opportunity or risk.
Sentence 3: What the AI system recommends.
Sentence 4: Agent system health.
Sentence 5: One number the Chairman should know.

Be direct. No fluff. NYC-tough."""

        result = _claude(json.dumps(results)[:3000], system,
                        model="claude-haiku-4-5-20251001", max_tokens=300, temperature=0.5)
        if result:
            return result.get("content", [{}])[0].get("text", "Briefing unavailable")
        return "Briefing unavailable — API error"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s [OMEGA] %(message)s")
    agent = DirectorsOmegaIntelligence()
    results = agent.run()
    print(json.dumps(results, indent=2, default=str)[:5000])

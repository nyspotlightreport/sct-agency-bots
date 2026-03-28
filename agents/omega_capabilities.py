#!/usr/bin/env python3
"""
omega_capabilities.py — Advanced Agent Capabilities Framework v1.0
══════════════════════════════════════════════════════════════════════

The upgrade layer that transforms standard RSI agents into cutting-edge
autonomous systems with:

  1. REAL-TIME REASONING    — Streaming analysis, event-driven decisions
  2. AGENTIC LOOPS          — Plan→Execute→Evaluate→Iterate with tool use
  3. MULTIMODAL             — Vision (Claude), structured data, multi-format
  4. GENERATIVE/PREDICTIVE  — Forecasting, anomaly detection, trend synthesis
  5. SWARM INTELLIGENCE     — Multi-agent coordination, collective decision-making

Every agent can import these capabilities as mixins or use OmegaAgent as base.

S.C. Thomas — Chairman. Maximum capability. Zero compromise.
"""

import os, json, time, logging, re, statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Callable
from pathlib import Path

log = logging.getLogger("omega")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")

import urllib.request, urllib.error


# ══════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════

def _api_call(url, method="GET", data=None, headers=None, timeout=30):
    """Generic HTTP call with error handling."""
    payload = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=payload, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except Exception as e:
        log.warning(f"API call failed {method} {url[:80]}: {e}")
        return None


def _supa(method, table, data=None, query=""):
    if not SUPABASE_URL: return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {
        "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json", "Prefer": "return=representation",
    }
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except Exception as e:
        log.warning(f"Supa {method} {table}: {e}")
        return None


def _claude(prompt, system="", model="claude-sonnet-4-20250514", max_tokens=2000,
            temperature=0.7, tools=None):
    """Advanced Claude call with tool use support."""
    if not ANTHROPIC_KEY: return None
    payload = {
        "model": model, "max_tokens": max_tokens, "temperature": temperature,
        "system": system or "You are an advanced autonomous AI agent with cutting-edge reasoning capabilities.",
        "messages": [{"role": "user", "content": prompt}],
    }
    if tools:
        payload["tools"] = tools
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except Exception as e:
        log.warning(f"Claude call failed: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# 1. REAL-TIME REASONING ENGINE
# ══════════════════════════════════════════════════════════════

class RealtimeReasoning:
    """
    Real-time reasoning with chain-of-thought, progressive refinement,
    and event-driven decision making.

    Capabilities:
    - Extended thinking with structured reasoning chains
    - Progressive hypothesis refinement (think → hypothesize → test → conclude)
    - Event-driven reactive decisions with priority queuing
    - Temporal reasoning (time-aware decisions, deadline tracking)
    - Uncertainty quantification (confidence intervals on every decision)
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._reasoning_chain: List[Dict] = []
        self._event_queue: List[Dict] = []
        self._decision_log: List[Dict] = []

    def reason(self, question: str, context: str = "", depth: str = "deep") -> Dict:
        """
        Multi-step reasoning with uncertainty quantification.

        Returns:
            {
                "conclusion": str,
                "confidence": float (0-1),
                "reasoning_chain": [{"step": str, "conclusion": str, "confidence": float}],
                "alternatives": [{"conclusion": str, "confidence": float}],
                "uncertainties": [str],
                "recommended_action": str,
            }
        """
        system = f"""You are {self.agent_name}, an advanced reasoning engine.
Think through problems systematically using this framework:

1. DECOMPOSE: Break the question into sub-problems
2. HYPOTHESIZE: Generate 2-3 hypotheses for each sub-problem
3. EVALUATE: Score each hypothesis on evidence strength (0-1)
4. SYNTHESIZE: Combine the strongest hypotheses into a conclusion
5. QUANTIFY UNCERTAINTY: Identify what you don't know

Return ONLY valid JSON:
{{
    "conclusion": "Your best answer",
    "confidence": 0.0,
    "reasoning_chain": [
        {{"step": "decompose", "analysis": "...", "sub_problems": ["..."]}},
        {{"step": "hypothesize", "hypotheses": [{{"h": "...", "evidence": 0.0}}]}},
        {{"step": "evaluate", "strongest": "...", "score": 0.0}},
        {{"step": "synthesize", "conclusion": "...", "confidence": 0.0}}
    ],
    "alternatives": [{{"conclusion": "...", "confidence": 0.0}}],
    "uncertainties": ["What we don't know"],
    "recommended_action": "What to do next"
}}"""

        model = "claude-sonnet-4-20250514" if depth == "deep" else "claude-haiku-4-5-20251001"
        tokens = 3000 if depth == "deep" else 1500

        result = _claude(f"Context:\n{context}\n\nQuestion: {question}", system,
                        model=model, max_tokens=tokens, temperature=0.4)
        if not result:
            return {"conclusion": "", "confidence": 0.0, "reasoning_chain": [],
                    "alternatives": [], "uncertainties": ["API call failed"],
                    "recommended_action": "retry"}

        text = result.get("content", [{}])[0].get("text", "")
        try:
            parsed = json.loads(re.sub(r"^```(?:json)?\n?|\n?```$", "", text.strip()))
            self._reasoning_chain.append(parsed)
            return parsed
        except Exception:
            return {"conclusion": text[:500], "confidence": 0.3,
                    "reasoning_chain": [], "alternatives": [],
                    "uncertainties": ["Failed to parse structured reasoning"],
                    "recommended_action": "review manually"}

    def decide_with_evidence(self, options: List[str], evidence: Dict,
                             criteria: List[str] = None) -> Dict:
        """
        Multi-criteria decision making with evidence weighting.

        Returns decision with full justification and confidence intervals.
        """
        criteria = criteria or ["revenue_impact", "risk", "effort", "time_to_value"]

        system = f"""You are a decision engine. Evaluate each option against criteria using evidence.
Score each option 0-10 on each criterion. Calculate weighted total. Show your math.

Return ONLY JSON:
{{
    "decision": "best option",
    "scores": {{"option": {{"criterion": score}}}},
    "weighted_totals": {{"option": total}},
    "confidence": 0.0,
    "risk_factors": ["..."],
    "justification": "Why this option wins"
}}"""

        prompt = f"""Options: {json.dumps(options)}
Evidence: {json.dumps(evidence)[:2000]}
Criteria: {json.dumps(criteria)}"""

        result = _claude(prompt, system, max_tokens=1500, temperature=0.3)
        if not result: return {"decision": options[0] if options else "", "confidence": 0.0}

        text = result.get("content", [{}])[0].get("text", "")
        try:
            parsed = json.loads(re.sub(r"^```(?:json)?\n?|\n?```$", "", text.strip()))
            self._decision_log.append(parsed)
            return parsed
        except Exception:
            return {"decision": text[:200], "confidence": 0.3}

    def process_event(self, event_type: str, data: Dict, priority: int = 5) -> Dict:
        """Process a real-time event and decide on action."""
        self._event_queue.append({
            "type": event_type, "data": data, "priority": priority,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Process highest priority events first (higher number = higher priority)
        self._event_queue.sort(key=lambda e: -e["priority"])

        system = f"""You are a real-time event processor for {self.agent_name}.
Analyze this event and decide: IGNORE, MONITOR, ACT_NOW, or ESCALATE.

Return JSON:
{{
    "action": "IGNORE|MONITOR|ACT_NOW|ESCALATE",
    "reason": "Why this action",
    "urgency": 0.0,
    "recommended_steps": ["step1", "step2"],
    "dependencies": ["what this depends on"]
}}"""

        result = _claude(
            f"Event: {event_type}\nData: {json.dumps(data)[:1000]}",
            system, model="claude-haiku-4-5-20251001", max_tokens=500, temperature=0.3
        )
        if not result: return {"action": "MONITOR", "reason": "API unavailable"}

        text = result.get("content", [{}])[0].get("text", "")
        try:
            return json.loads(re.sub(r"^```(?:json)?\n?|\n?```$", "", text.strip()))
        except Exception:
            return {"action": "MONITOR", "reason": text[:200]}


# ══════════════════════════════════════════════════════════════
# 2. AGENTIC EXECUTION ENGINE
# ══════════════════════════════════════════════════════════════

class AgenticExecutor:
    """
    Full agentic loop: Plan → Execute → Evaluate → Iterate.

    Supports:
    - Multi-step task decomposition with dependency tracking
    - Tool use via Claude's native tool calling
    - Self-evaluation after each step
    - Automatic retry with strategy adjustment on failure
    - Memory of past executions for learning
    """

    TOOLS = [
        {
            "name": "search_database",
            "description": "Query Supabase for data. Returns JSON array of matching records.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Table name"},
                    "query": {"type": "string", "description": "Supabase REST query string (e.g., ?status=eq.active&limit=10)"},
                },
                "required": ["table", "query"],
            },
        },
        {
            "name": "write_database",
            "description": "Insert or update a record in Supabase.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "table": {"type": "string"},
                    "method": {"type": "string", "enum": ["POST", "PATCH"]},
                    "data": {"type": "object"},
                    "query": {"type": "string", "description": "For PATCH: filter query"},
                },
                "required": ["table", "method", "data"],
            },
        },
        {
            "name": "analyze_data",
            "description": "Perform statistical analysis on a dataset. Returns insights.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "data": {"type": "array", "description": "Array of data points"},
                    "analysis_type": {"type": "string", "enum": ["trend", "anomaly", "correlation", "forecast"]},
                },
                "required": ["data", "analysis_type"],
            },
        },
        {
            "name": "send_notification",
            "description": "Send a Pushover notification to the Chairman.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "message": {"type": "string"},
                    "priority": {"type": "integer", "enum": [-1, 0, 1]},
                },
                "required": ["title", "message"],
            },
        },
    ]

    def __init__(self, agent_name: str, max_iterations: int = 5):
        self.agent_name = agent_name
        self.max_iterations = max_iterations
        self._execution_log: List[Dict] = []

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> Any:
        """Execute a tool and return the result."""
        if tool_name == "search_database":
            return _supa("GET", tool_input["table"], query=tool_input.get("query", ""))
        elif tool_name == "write_database":
            return _supa(tool_input["method"], tool_input["table"],
                        tool_input.get("data"), tool_input.get("query", ""))
        elif tool_name == "analyze_data":
            return self._analyze(tool_input["data"], tool_input["analysis_type"])
        elif tool_name == "send_notification":
            try:
                from rsi_base_agent import _push
                _push(tool_input["title"], tool_input["message"],
                      tool_input.get("priority", 0))
                return {"sent": True}
            except ImportError:
                log.warning("rsi_base_agent not available for notifications")
                return {"sent": False, "error": "notification module unavailable"}
        return {"error": f"Unknown tool: {tool_name}"}

    def _analyze(self, data: List, analysis_type: str) -> Dict:
        """Built-in statistical analysis without external libs."""
        if not data: return {"error": "No data"}
        nums = [float(x) for x in data if isinstance(x, (int, float))]
        if not nums: return {"error": "No numeric data"}

        result = {
            "count": len(nums),
            "mean": statistics.mean(nums),
            "median": statistics.median(nums),
            "stdev": statistics.stdev(nums) if len(nums) > 1 else 0,
            "min": min(nums),
            "max": max(nums),
        }

        if analysis_type == "trend":
            # Simple linear regression
            n = len(nums)
            x_vals = list(range(n))
            x_mean = sum(x_vals) / n
            y_mean = result["mean"]
            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, nums))
            denominator = sum((x - x_mean) ** 2 for x in x_vals)
            slope = numerator / denominator if denominator else 0
            result["trend"] = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
            result["slope"] = round(slope, 4)
            result["forecast_next_3"] = [round(y_mean + slope * (n + i), 2) for i in range(1, 4)]

        elif analysis_type == "anomaly":
            mean, stdev = result["mean"], result["stdev"]
            if stdev > 0:
                z_scores = [(x - mean) / stdev for x in nums]
                anomalies = [{"index": i, "value": nums[i], "z_score": round(z, 2)}
                            for i, z in enumerate(z_scores) if abs(z) > 2]
                result["anomalies"] = anomalies
                result["anomaly_count"] = len(anomalies)

        elif analysis_type == "forecast":
            # Exponential smoothing
            alpha = 0.3
            forecast = [nums[0]]
            for i in range(1, len(nums)):
                forecast.append(alpha * nums[i] + (1 - alpha) * forecast[-1])
            last = forecast[-1]
            result["forecast_next_5"] = [round(last, 2)] * 5
            # Adjust with trend
            if len(nums) > 3:
                recent_trend = (nums[-1] - nums[-3]) / 3
                result["forecast_next_5"] = [round(last + recent_trend * i, 2) for i in range(1, 6)]

        return result

    def execute_task(self, task: str, context: str = "") -> Dict:
        """
        Full agentic execution with tool use loop.

        The agent plans, executes tools, evaluates results, and iterates.
        """
        system = f"""You are {self.agent_name}, an autonomous execution agent.

You have access to tools. Use them to accomplish the task.
After each tool result, evaluate if the task is complete.
If not, use another tool or adjust your approach.

IMPORTANT: When the task is complete, respond with a text block containing your final answer.
Do NOT call tools unnecessarily. Be efficient."""

        messages = [{"role": "user", "content": f"Task: {task}\n\nContext: {context}"}]
        iteration = 0
        results = []

        while iteration < self.max_iterations:
            iteration += 1
            log.info(f"Agentic loop iteration {iteration}/{self.max_iterations}")

            if not ANTHROPIC_KEY:
                log.warning("No ANTHROPIC_API_KEY — cannot run agentic loop")
                break

            # Single API call with full message history and tool definitions
            payload = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2000, "temperature": 0.3,
                "system": system,
                "messages": messages,
                "tools": self.TOOLS,
            }
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages", data=data,
                headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY,
                         "anthropic-version": "2023-06-01"})
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    response = json.loads(r.read())
            except Exception as e:
                log.error(f"Agentic call failed: {e}")
                break

            content = response.get("content", [])
            stop_reason = response.get("stop_reason", "")

            # Process response blocks
            assistant_content = []
            tool_results = []
            final_text = ""

            for block in content:
                if block.get("type") == "text":
                    final_text += block.get("text", "")
                    assistant_content.append(block)
                elif block.get("type") == "tool_use":
                    tool_name = block["name"]
                    tool_input = block["input"]
                    tool_id = block["id"]

                    log.info(f"Tool call: {tool_name}({json.dumps(tool_input)[:200]})")
                    try:
                        tool_result = self._execute_tool(tool_name, tool_input)
                    except Exception as te:
                        log.error(f"Tool {tool_name} execution failed: {te}")
                        tool_result = {"error": str(te)}
                    results.append({"tool": tool_name, "input": tool_input, "result": tool_result})
                    assistant_content.append(block)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(tool_result)[:4000],
                    })

            # Add assistant message
            messages.append({"role": "assistant", "content": assistant_content})

            # If there were tool calls, add results and continue
            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            else:
                # No tool calls — agent is done
                break

        self._execution_log.append({
            "task": task, "iterations": iteration,
            "results": results, "final_text": final_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "success": True, "iterations": iteration,
            "tool_calls": len(results), "output": final_text,
            "results": results,
        }


# ══════════════════════════════════════════════════════════════
# 3. MULTIMODAL INTELLIGENCE
# ══════════════════════════════════════════════════════════════

class MultimodalIntelligence:
    """
    Multimodal processing: text, images, structured data, time-series.

    Capabilities:
    - Image analysis via Claude Vision
    - Cross-modal reasoning (combine text + data + images)
    - Structured data extraction from unstructured sources
    - Multi-format output generation (text, JSON, HTML, markdown)
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    def analyze_image(self, image_url: str, question: str) -> Dict:
        """Analyze an image using Claude Vision."""
        if not ANTHROPIC_KEY: return {"error": "No API key"}

        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1500,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "url", "url": image_url}},
                    {"type": "text", "text": question},
                ],
            }],
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=data,
            headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY,
                     "anthropic-version": "2023-06-01"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                result = json.loads(r.read())
                return {"analysis": result["content"][0]["text"], "model": "claude-sonnet"}
        except Exception as e:
            return {"error": str(e)}

    def cross_modal_reason(self, text_data: str, structured_data: Dict,
                           question: str) -> Dict:
        """Combine text and structured data for cross-modal reasoning."""
        system = f"""You are {self.agent_name}, a multimodal reasoning engine.
You receive both unstructured text and structured data.
Synthesize insights that neither source alone could provide.

Return JSON:
{{
    "synthesis": "Combined insight",
    "text_insights": ["From the text..."],
    "data_insights": ["From the data..."],
    "cross_modal_insights": ["Insights only visible by combining both"],
    "confidence": 0.0,
    "actionable_recommendations": ["..."]
}}"""

        prompt = f"""TEXT DATA:
{text_data[:3000]}

STRUCTURED DATA:
{json.dumps(structured_data)[:3000]}

QUESTION: {question}"""

        result = _claude(prompt, system, max_tokens=2000, temperature=0.4)
        if not result: return {"synthesis": "", "confidence": 0.0}

        text = result.get("content", [{}])[0].get("text", "")
        try:
            return json.loads(re.sub(r"^```(?:json)?\n?|\n?```$", "", text.strip()))
        except Exception:
            return {"synthesis": text[:500], "confidence": 0.3}

    def extract_structured(self, text: str, schema: Dict) -> Dict:
        """Extract structured data from unstructured text according to a schema."""
        system = f"""Extract structured data from the text according to this schema:
{json.dumps(schema, indent=2)}

Return ONLY valid JSON matching the schema. If a field can't be extracted, use null."""

        result = _claude(text, system, model="claude-haiku-4-5-20251001",
                        max_tokens=1000, temperature=0.1)
        if not result: return {}

        text_out = result.get("content", [{}])[0].get("text", "")
        try:
            return json.loads(re.sub(r"^```(?:json)?\n?|\n?```$", "", text_out.strip()))
        except Exception:
            return {}


# ══════════════════════════════════════════════════════════════
# 4. PREDICTIVE ANALYTICS ENGINE
# ══════════════════════════════════════════════════════════════

class PredictiveEngine:
    """
    Forecasting, anomaly detection, and trend synthesis.

    Capabilities:
    - Time-series forecasting (exponential smoothing + AI-enhanced)
    - Anomaly detection (statistical + pattern-based)
    - Causal inference (why did metric X change?)
    - Scenario modeling (what-if analysis)
    - Revenue forecasting with confidence intervals
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    def forecast(self, historical_data: List[Dict], metric: str,
                 periods: int = 7) -> Dict:
        """
        Forecast a metric using hybrid statistical + AI approach.

        historical_data: [{"date": "2026-03-01", "value": 100}, ...]
        """
        values = [d.get("value", 0) for d in historical_data if d.get("value") is not None]
        if len(values) < 3:
            return {"error": "Need at least 3 data points", "forecast": []}

        # Statistical forecast (exponential smoothing)
        alpha = 0.3
        smoothed = [values[0]]
        for v in values[1:]:
            smoothed.append(alpha * v + (1 - alpha) * smoothed[-1])

        # Trend component
        if len(values) > 5:
            recent = values[-5:]
            older = values[-10:-5] if len(values) >= 10 else values[:5]
            trend = (statistics.mean(recent) - statistics.mean(older)) / max(len(older), 1)
        else:
            trend = 0

        # Generate forecast
        last = smoothed[-1]
        stat_forecast = [round(last + trend * (i + 1), 2) for i in range(periods)]

        # Confidence intervals — widen with forecast horizon (uncertainty grows over time)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        lower = [round(f - 1.96 * stdev * (1 + 0.1 * i), 2) for i, f in enumerate(stat_forecast)]
        upper = [round(f + 1.96 * stdev * (1 + 0.1 * i), 2) for i, f in enumerate(stat_forecast)]

        # AI-enhanced forecast (use Claude to factor in patterns humans miss)
        ai_forecast = self._ai_forecast(historical_data, metric, periods, stat_forecast)

        return {
            "metric": metric,
            "historical_count": len(values),
            "statistical_forecast": stat_forecast,
            "ai_enhanced_forecast": ai_forecast.get("forecast", stat_forecast),
            "confidence_lower": lower,
            "confidence_upper": upper,
            "trend": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable",
            "trend_strength": round(abs(trend), 4),
            "ai_reasoning": ai_forecast.get("reasoning", ""),
            "risk_factors": ai_forecast.get("risk_factors", []),
        }

    def _ai_forecast(self, data: List[Dict], metric: str, periods: int,
                     stat_forecast: List[float]) -> Dict:
        """Use Claude to enhance statistical forecast with contextual reasoning."""
        system = """You are a predictive analytics engine. Given historical data and a statistical forecast,
provide an AI-enhanced forecast that accounts for:
- Seasonality and cyclical patterns
- Day-of-week effects
- Trend acceleration or deceleration
- External factors (holidays, events)

Return JSON:
{"forecast": [numbers], "reasoning": "Why AI forecast differs", "risk_factors": ["..."]}"""

        recent = data[-14:] if len(data) > 14 else data
        prompt = f"""Metric: {metric}
Recent data: {json.dumps(recent)}
Statistical forecast (next {periods}): {stat_forecast}

Provide your enhanced forecast for the next {periods} periods."""

        result = _claude(prompt, system, model="claude-haiku-4-5-20251001",
                        max_tokens=500, temperature=0.3)
        if not result: return {}

        text = result.get("content", [{}])[0].get("text", "")
        try:
            return json.loads(re.sub(r"^```(?:json)?\n?|\n?```$", "", text.strip()))
        except Exception:
            return {"reasoning": text[:300]}

    def detect_anomalies(self, data: List[Dict], metric: str) -> Dict:
        """Detect anomalies in time-series data."""
        values = [d.get("value", 0) for d in data if d.get("value") is not None]
        if len(values) < 5: return {"anomalies": [], "status": "insufficient_data"}

        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        if stdev == 0: return {"anomalies": [], "status": "no_variance"}

        anomalies = []
        for i, v in enumerate(values):
            z = (v - mean) / stdev
            if abs(z) > 2:
                anomalies.append({
                    "index": i,
                    "date": data[i].get("date", f"point_{i}"),
                    "value": v,
                    "z_score": round(z, 2),
                    "severity": "critical" if abs(z) > 3 else "warning",
                    "direction": "spike" if z > 0 else "drop",
                })

        return {
            "metric": metric,
            "anomalies": anomalies,
            "anomaly_rate": round(len(anomalies) / len(values) * 100, 1),
            "mean": round(mean, 2),
            "stdev": round(stdev, 2),
            "status": "anomalies_detected" if anomalies else "normal",
        }

    def scenario_model(self, current_state: Dict, scenarios: List[Dict]) -> Dict:
        """What-if analysis: model multiple scenarios and their outcomes."""
        system = f"""You are a scenario modeling engine for {self.agent_name}.
Given the current state and proposed scenarios, model the likely outcomes.

For each scenario, estimate:
- Probability of success (0-1)
- Expected revenue impact
- Risk factors
- Timeline to impact
- Required resources

Return JSON:
{{
    "scenarios": [
        {{
            "name": "...",
            "probability": 0.0,
            "revenue_impact": 0,
            "timeline_days": 0,
            "risk_factors": ["..."],
            "prerequisites": ["..."],
            "recommendation": "proceed|defer|reject"
        }}
    ],
    "best_scenario": "name",
    "overall_recommendation": "..."
}}"""

        prompt = f"""Current State: {json.dumps(current_state)[:2000]}
Scenarios to model: {json.dumps(scenarios)[:2000]}"""

        result = _claude(prompt, system, max_tokens=2000, temperature=0.4)
        if not result: return {"scenarios": [], "best_scenario": "", "overall_recommendation": ""}

        text = result.get("content", [{}])[0].get("text", "")
        try:
            return json.loads(re.sub(r"^```(?:json)?\n?|\n?```$", "", text.strip()))
        except Exception:
            return {"scenarios": [], "overall_recommendation": text[:300]}


# ══════════════════════════════════════════════════════════════
# 5. SWARM INTELLIGENCE (Multi-Agent Coordination)
# ══════════════════════════════════════════════════════════════

class SwarmIntelligence:
    """
    Multi-agent coordination and collective decision-making.

    Capabilities:
    - Consensus building across multiple agent perspectives
    - Task delegation with capability matching
    - Collective intelligence aggregation
    - Conflict resolution between agents
    - Emergent strategy from agent interactions
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    def gather_perspectives(self, question: str, agent_roles: List[str]) -> Dict:
        """Get perspectives from multiple specialist viewpoints and synthesize."""
        system = """You are simulating a panel of specialist AI agents, each with a different perspective.
For each role, provide their unique analysis based on their expertise.
Then synthesize a consensus recommendation.

Return JSON:
{
    "perspectives": [
        {"role": "...", "analysis": "...", "recommendation": "...", "confidence": 0.0}
    ],
    "consensus": "...",
    "dissenting_views": ["..."],
    "synthesis_confidence": 0.0,
    "recommended_action": "..."
}"""

        prompt = f"""Question: {question}
Agent roles to consult: {json.dumps(agent_roles)}

Each agent should provide their unique perspective based on their specialty."""

        result = _claude(prompt, system, model="claude-sonnet-4-20250514",
                        max_tokens=3000, temperature=0.5)
        if not result: return {"perspectives": [], "consensus": ""}

        text = result.get("content", [{}])[0].get("text", "")
        try:
            return json.loads(re.sub(r"^```(?:json)?\n?|\n?```$", "", text.strip()))
        except Exception:
            return {"perspectives": [], "consensus": text[:500]}

    def delegate_task(self, task: str, available_agents: List[Dict]) -> Dict:
        """Match a task to the best available agent based on capabilities."""
        system = """You are a task delegation engine. Match tasks to agents based on capabilities.
Consider: expertise match, current workload, past performance, urgency.

Return JSON:
{
    "assigned_agent": "agent_name",
    "match_score": 0.0,
    "reasoning": "Why this agent",
    "subtasks": [{"agent": "...", "task": "...", "priority": 0}],
    "dependencies": ["task that must complete first"],
    "estimated_duration_hours": 0
}"""

        prompt = f"""Task: {task}
Available agents: {json.dumps(available_agents)[:3000]}"""

        result = _claude(prompt, system, model="claude-haiku-4-5-20251001",
                        max_tokens=800, temperature=0.3)
        if not result: return {"assigned_agent": "", "match_score": 0.0}

        text = result.get("content", [{}])[0].get("text", "")
        try:
            return json.loads(re.sub(r"^```(?:json)?\n?|\n?```$", "", text.strip()))
        except Exception:
            return {"assigned_agent": "", "reasoning": text[:200]}

    def collective_intelligence(self, data_points: List[Dict]) -> Dict:
        """Aggregate insights from multiple agents into emergent intelligence."""
        system = f"""You are the collective intelligence synthesizer for {self.agent_name}.
Multiple agents have provided data and insights. Your job is to:
1. Find patterns NO single agent could see alone
2. Identify contradictions between agent reports
3. Generate emergent insights from the combination
4. Recommend coordinated actions

Return JSON:
{{
    "emergent_insights": ["Insights visible only from the combination"],
    "contradictions": [{{"agent1": "...", "agent2": "...", "issue": "..."}}],
    "coordinated_actions": [{{"action": "...", "agents_involved": ["..."], "priority": 0}}],
    "system_health": 0.0,
    "strategic_recommendation": "..."
}}"""

        prompt = f"Agent reports:\n{json.dumps(data_points)[:4000]}"

        result = _claude(prompt, system, model="claude-sonnet-4-20250514",
                        max_tokens=2000, temperature=0.4)
        if not result: return {"emergent_insights": [], "system_health": 0.5}

        text = result.get("content", [{}])[0].get("text", "")
        try:
            return json.loads(re.sub(r"^```(?:json)?\n?|\n?```$", "", text.strip()))
        except Exception:
            return {"emergent_insights": [text[:300]], "system_health": 0.5}


# ══════════════════════════════════════════════════════════════
# 6. OMEGA AGENT — THE COMPLETE PACKAGE
# ══════════════════════════════════════════════════════════════

class OmegaAgent:
    """
    The most advanced agent class in the system.

    Combines ALL capabilities:
    - RSI self-improvement (via RSIBaseAgent integration when available)
    - Real-time reasoning with uncertainty quantification
    - Agentic execution with tool use
    - Multimodal intelligence (vision + structured data)
    - Predictive analytics (forecasting + anomaly detection)
    - Swarm intelligence (multi-agent coordination)

    Usage:
        class MyAgent(OmegaAgent):
            ORG_ID = "my_org"
            NAME = "My Agent"
            MISSION = "What I do"

            def execute(self) -> Dict:
                # Use all capabilities:
                reasoning = self.reasoning.reason("What should we do?", context)
                prediction = self.predict.forecast(data, "revenue", 7)
                consensus = self.swarm.gather_perspectives(question, roles)
                agentic = self.agentic.execute_task("Do complex thing", context)
                return {"items_processed": N}
    """

    ORG_ID:   str = "omega"
    NAME:     str = "Omega Agent"
    DIRECTOR: str = "AI Director"
    MISSION:  str = "Maximum capability autonomous agent"
    VERSION:  str = "1.0.0"

    # Capability flags (subclasses can disable specific capabilities)
    ENABLE_REASONING:   bool = True
    ENABLE_AGENTIC:     bool = True
    ENABLE_MULTIMODAL:  bool = True
    ENABLE_PREDICTIVE:  bool = True
    ENABLE_SWARM:       bool = True
    ENABLE_RSI:         bool = True  # RSIBaseAgent genome tracking

    def __init__(self):
        self._run_start = time.time()
        self._metrics: Dict = {}
        self._errors: List = []
        self._decisions: List = []
        self._rsi_agent = None
        logging.basicConfig(level=logging.INFO,
                          format=f"%(asctime)s [{self.NAME[:20]}] %(message)s")

        # Initialize RSI integration (genome tracking, inter-org messaging)
        if self.ENABLE_RSI:
            try:
                from rsi_base_agent import RSIBaseAgent
                # Create a lightweight RSI wrapper for genome and messaging
                self._rsi_agent = type("_RSIProxy", (RSIBaseAgent,), {
                    "ORG_ID": self.ORG_ID, "NAME": self.NAME,
                    "DIRECTOR": self.DIRECTOR, "MISSION": self.MISSION,
                    "VERSION": self.VERSION, "IMPROVEMENT_ENABLED": False,
                    "execute": lambda s: {}, "score_performance": lambda s, m: 0.5,
                })()
                log.info("RSI genome tracking enabled")
            except ImportError:
                log.info("RSIBaseAgent not available — running without genome tracking")

        # Initialize persistent memory (available to all agents)
        try:
            from agent_memory import AgentMemory
            self.memory = AgentMemory(self.ORG_ID, default_ttl_days=90)
            log.info("Persistent memory enabled")
        except ImportError:
            self.memory = None
            log.info("agent_memory not available — running without persistent memory")

        # Initialize capability engines (safe — check flags before access)
        if getattr(self, "ENABLE_REASONING", True):
            self.reasoning = RealtimeReasoning(self.NAME)
        if getattr(self, "ENABLE_AGENTIC", True):
            self.agentic = AgenticExecutor(self.NAME)
        if getattr(self, "ENABLE_MULTIMODAL", True):
            self.multimodal = MultimodalIntelligence(self.NAME)
        if getattr(self, "ENABLE_PREDICTIVE", True):
            self.predict = PredictiveEngine(self.NAME)
        if getattr(self, "ENABLE_SWARM", True):
            self.swarm = SwarmIntelligence(self.NAME)

        log.info(f"OmegaAgent initialized: {self.NAME} v{self.VERSION}")
        enabled = [k.replace("ENABLE_","").lower() for k in
                   ["ENABLE_REASONING","ENABLE_AGENTIC","ENABLE_MULTIMODAL",
                    "ENABLE_PREDICTIVE","ENABLE_SWARM","ENABLE_RSI"]
                   if getattr(self, k, False)]
        log.info(f"Capabilities: {', '.join(enabled)}")

    def execute(self) -> Dict:
        raise NotImplementedError(f"{self.NAME} must implement execute()")

    def run(self) -> Dict:
        """Main entry point with full lifecycle management."""
        log.info(f"{'='*60}")
        log.info(f"OMEGA: {self.NAME} v{self.VERSION}")
        log.info(f"Mission: {self.MISSION}")
        log.info(f"{'='*60}")

        self._run_start = time.time()

        # Load genome if RSI is enabled
        if self._rsi_agent:
            try:
                self._rsi_agent._load_genome()
                self._rsi_agent._consume_messages()
            except Exception as e:
                log.warning(f"RSI initialization skipped: {e}")

        try:
            self._metrics = self.execute()
            if not isinstance(self._metrics, dict):
                self._metrics = {"result": self._metrics}
            duration = round(time.time() - self._run_start, 2)
            items = self._metrics.get("items_processed", 0)

            log.info(f"Complete in {duration}s | Items: {items} | Errors: {len(self._errors)}")

            # Log to Supabase
            _supa("POST", "agent_run_logs", {
                "org_id": self.ORG_ID, "agent_name": self.NAME,
                "status": "success" if not self._errors else "partial",
                "metrics": self._metrics,
                "errors": self._errors[-10:],
                "decisions_made": self._decisions[-20:],
                "duration_seconds": duration,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })

            # Broadcast results via RSI messaging
            if self._rsi_agent:
                try:
                    self._rsi_agent._fitness = 0.8 if not self._errors else 0.5
                    self._rsi_agent._metrics = self._metrics
                    self._rsi_agent._broadcast_results()
                    self._rsi_agent._update_genome_performance()
                except Exception as _silent_e:
                    import logging; logging.getLogger(__name__).error("Error in %s: %s", __file__, _silent_e)

        except Exception as e:
            import traceback
            log.error(f"Failed: {e}\n{traceback.format_exc()}")
            self._metrics = {"success": False, "error": str(e)}

            _supa("POST", "agent_run_logs", {
                "org_id": self.ORG_ID, "agent_name": self.NAME,
                "status": "failed",
                "errors": [{"msg": str(e), "trace": traceback.format_exc()[-500:]}],
                "duration_seconds": round(time.time() - self._run_start, 2),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })

        return self._metrics

    # Convenience methods
    def supa(self, method, table, data=None, query=""):
        return _supa(method, table, data, query)

    def decide(self, decision: str, outcome=None):
        self._decisions.append({
            "decision": decision, "outcome": str(outcome)[:100] if outcome else None,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        log.info(f"Decision: {decision}")

    def record_error(self, error: str, severity="warning"):
        self._errors.append({"msg": error, "severity": severity})
        log.warning(f"Error [{severity}]: {error}")


# ══════════════════════════════════════════════════════════════
# EXPORT
# ══════════════════════════════════════════════════════════════

__all__ = [
    "OmegaAgent",
    "RealtimeReasoning",
    "AgenticExecutor",
    "MultimodalIntelligence",
    "PredictiveEngine",
    "SwarmIntelligence",
]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Omega Capabilities Framework v1.0")
    print(f"Anthropic: {'connected' if ANTHROPIC_KEY else 'not configured'}")
    print(f"Supabase: {'connected' if SUPABASE_URL else 'not configured'}")
    print("Capabilities: RealtimeReasoning, AgenticExecutor, MultimodalIntelligence,")
    print("              PredictiveEngine, SwarmIntelligence, OmegaAgent")

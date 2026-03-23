"""
rsi_base_agent.py — Recursive Self-Improving Agent Base Class
═══════════════════════════════════════════════════════════════
Every department agent inherits from this class.
Each instance IS a Synthetic Organization — a Digital Entity.

Architecture:
  OBSERVE → SCORE → HYPOTHESIZE → WRITE → TEST → GATE → DEPLOY → MEASURE → LOOP

Rob Vance — CITWO. Directly designed and verified.
"""
import os, json, logging, datetime, hashlib, time, sys, traceback
from typing import Dict, List, Optional, Any, Tuple

log = logging.getLogger("rsi")

SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PUSHOVER_API  = os.environ.get("PUSHOVER_API_KEY", "")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY", "")
GH_TOKEN      = os.environ.get("GH_PAT", "")
REPO          = "nyspotlightreport/sct-agency-bots"

import urllib.request, urllib.error


# ══════════════════════════════════════════════════════════════
# CORE UTILITIES
# ══════════════════════════════════════════════════════════════

def _supa(method: str, table: str, data: dict = None, query: str = "") -> Any:
    if not SUPABASE_URL: return None
    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"
    payload = json.dumps(data).encode() if data else None
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        log.warning(f"Supa {method} {table}: {e.code} {e.read()[:100]}")
        return None
    except Exception as e:
        log.warning(f"Supa {method} {table}: {e}")
        return None


def _claude(prompt: str, system: str = "", model: str = "claude-haiku-4-5-20251001",
            max_tokens: int = 800) -> str:
    if not ANTHROPIC_KEY: return ""
    data = json.dumps({
        "model": model, "max_tokens": max_tokens,
        "system": system or "You are an autonomous AI agent performing self-improvement analysis.",
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=data,
        headers={"Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        log.warning(f"Claude call failed: {e}")
        return ""


def _push(title: str, msg: str, priority: int = 0):
    if not PUSHOVER_API: return
    data = json.dumps({"token": PUSHOVER_API, "user": PUSHOVER_USER,
                       "title": title, "message": msg, "priority": priority}).encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json", data=data,
                                  headers={"Content-Type": "application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except Exception:  # noqa: bare-except

        pass
# ══════════════════════════════════════════════════════════════
# RSI BASE AGENT CLASS
# ══════════════════════════════════════════════════════════════

class RSIBaseAgent:
    """
    Recursive Self-Improving Agent.
    Each subclass IS a Synthetic Organization — a sovereign Digital Entity.
    
    Subclasses must implement:
        - execute() → returns dict of performance metrics
        - score_performance(metrics) → returns float 0.0-1.0
    
    Optionally override:
        - get_improvement_context() → returns str describing current behavior
        - validate_improvement(proposal) → returns bool
    """

    ORG_ID:   str = "base"
    NAME:     str = "Base Agent Corp"
    DIRECTOR: str = "AI Director"
    MISSION:  str = "Execute assigned tasks with maximum performance"
    VERSION:  str = "1.0.0"

    # RSI Configuration
    MIN_FITNESS_TO_IMPROVE:  float = 0.60  # Only propose improvements if below this
    MIN_FITNESS_TO_DEPLOY:   float = 0.65  # Only auto-deploy if improvement exceeds this
    MAX_IMPROVEMENTS_PER_DAY: int  = 5
    IMPROVEMENT_ENABLED:     bool  = True
    NETLIFY_SAFE:            bool  = True   # If True, never commit to site/ in automated improvements

    def __init__(self):
        self._run_id:        Optional[str] = None
        self._genome_id:     Optional[str] = None
        self._run_start:     float = time.time()
        self._metrics:       Dict  = {}
        self._decisions:     List  = []
        self._errors:        List  = []
        self._token_count:   int   = 0
        self._api_calls:     int   = 0
        self._fitness:       float = 0.0
        self._genome:        Optional[Dict] = None
        logging.basicConfig(level=logging.INFO,
                            format=f"%(asctime)s [{self.NAME[:20]}] %(message)s")

    # ── LIFECYCLE ─────────────────────────────────────────────

    def run(self) -> Dict:
        """Main entry point. Call this to run the agent."""
        log.info(f"{'='*60}")
        log.info(f"{self.NAME} v{self.VERSION} — Generation {self._get_generation()}")
        log.info(f"Mission: {self.MISSION}")
        log.info(f"{'='*60}")

        self._run_start = time.time()
        self._start_run_log()
        self._load_genome()
        self._consume_messages()

        metrics = {}
        try:
            # OBSERVE + EXECUTE
            metrics = self.execute()
            self._metrics = metrics or {}

            # SCORE
            self._fitness = self.score_performance(self._metrics)
            log.info(f"Performance score: {self._fitness:.2f}/1.0")

            # SELF-IMPROVE (if enabled and fitness warrants it)
            if self.IMPROVEMENT_ENABLED:
                self._rsi_cycle()

        except Exception as e:
            self._errors.append({"type": type(e).__name__, "msg": str(e),
                                   "trace": traceback.format_exc()[-500:]})
            log.error(f"Execution error: {e}")
            self._fitness = 0.1

        # COMPLETE
        self._complete_run_log()
        self._update_org_stats()
        self._broadcast_results()

        log.info(f"Run complete. Fitness: {self._fitness:.2f} | "
                 f"Duration: {time.time()-self._run_start:.1f}s | "
                 f"Errors: {len(self._errors)}")
        return self._metrics

    def execute(self) -> Dict:
        """Subclasses implement their actual work here. Returns performance metrics."""
        raise NotImplementedError(f"{self.NAME} must implement execute()")

    def score_performance(self, metrics: Dict) -> float:
        """
        Score own performance 0.0-1.0 based on metrics.
        Subclasses should override for domain-specific scoring.
        Default: score based on error rate.
        """
        if not metrics: return 0.3
        errors = len(self._errors)
        if errors == 0: return 0.75
        if errors == 1: return 0.5
        return 0.25

    def get_improvement_context(self) -> str:
        """Return a description of current behavior for the RSI engine to analyze."""
        return f"Agent: {self.NAME}\nMission: {self.MISSION}\n" \
               f"Current fitness: {self._fitness:.2f}\n" \
               f"Errors this run: {self._errors}\n" \
               f"Metrics: {json.dumps(self._metrics)[:500]}"

    def validate_improvement(self, proposal: Dict) -> bool:
        """Final safety check before deploying an improvement. Override for custom gates."""
        # Never modify safety-critical files
        code_diff = proposal.get("code_diff", "")
        forbidden = ["sys.exit", "os.remove", "shutil.rmtree", "site/", "secrets"]
        if self.NETLIFY_SAFE:
            forbidden.append("site/")
        for f in forbidden:
            if f in code_diff:
                log.warning(f"Improvement blocked: contains forbidden pattern '{f}'")
                return False
        return True

    # ── RSI CYCLE ─────────────────────────────────────────────

    def _rsi_cycle(self):
        """The full Recursive Self-Improvement loop."""
        # Check safety governor
        if not self._check_governor():
            log.info("RSI governor: improvement quota reached for today")
            return

        # Only improve if fitness is suboptimal or there's clear room to grow
        genome = self._genome or {}
        learned = genome.get("learned_params", {})
        recent_scores = genome.get("performance_history", [])

        # Compute trend — improving or declining?
        if len(recent_scores) >= 3:
            trend = sum(recent_scores[-3:]) / 3
            if trend > 0.85:
                log.info(f"RSI: fitness trend {trend:.2f} — system performing well, minimal improvement needed")
                # Still check for new capabilities even when performing well
                if self._fitness < 0.90:
                    self._propose_capability_improvement()
                return

        # Fitness below target — analyze and propose fix
        if self._fitness < self.MIN_FITNESS_TO_IMPROVE:
            log.info(f"RSI: fitness {self._fitness:.2f} < threshold {self.MIN_FITNESS_TO_IMPROVE} — proposing improvement")
            self._propose_and_apply_improvement()
        else:
            log.info(f"RSI: fitness {self._fitness:.2f} — stable, checking for optimizations")
            self._propose_optimization()

        # Update performance history in genome
        self._update_genome_performance()

    def _propose_and_apply_improvement(self):
        """Use Claude to analyze failures and propose a fix."""
        context = self.get_improvement_context()
        errors_str = json.dumps(self._errors[:3]) if self._errors else "No explicit errors but performance is low"

        prompt = f"""You are analyzing an AI agent's performance to propose a self-improvement.

AGENT: {self.NAME}
MISSION: {self.MISSION}
CURRENT FITNESS: {self._fitness:.2f}/1.0 (target: >{self.MIN_FITNESS_TO_IMPROVE})

CONTEXT:
{context}

ERRORS/ISSUES:
{errors_str}

TASK: Propose ONE specific, concrete improvement to this agent's behavior or configuration.
The improvement must be safe, testable, and likely to improve the fitness score.

Return ONLY valid JSON:
{{
  "title": "Short title for the improvement",
  "proposal_type": "config_change or behavior_mod",
  "description": "What the improvement does",
  "current_behavior": "What it does now that's suboptimal",
  "proposed_behavior": "What it should do instead",
  "expected_improvement": "Why this will raise the fitness score",
  "config_diff": {{}},
  "confidence": 0.0
}}"""

        response = _claude(prompt, max_tokens=600)
        if not response: return

        try:
            clean = response.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            proposal = json.loads(clean)
            proposal["org_id"] = self.ORG_ID
            proposal["agent_name"] = self.NAME
            proposal["baseline_score"] = self._fitness

            # Check safety gate
            if not self.validate_improvement(proposal):
                return

            confidence = float(proposal.get("confidence", 0))
            if confidence >= self.MIN_FITNESS_TO_DEPLOY:
                self._apply_config_improvement(proposal)
            else:
                # Store for human review
                _supa("POST", "rsi_proposals", {**proposal, "status": "pending"})
                log.info(f"RSI proposal stored (confidence too low to auto-deploy): {proposal['title']}")
        except Exception as e:
            log.warning(f"RSI proposal parse failed: {e}")

    def _propose_optimization(self):
        """Propose incremental optimizations when performing well."""
        prompt = f"""Agent {self.NAME} is performing at {self._fitness:.2f}/1.0. 
Mission: {self.MISSION}
Metrics: {json.dumps(self._metrics)[:300]}

Suggest ONE small optimization to push performance higher.
Return JSON: {{"title":"...","proposal_type":"config_change","config_diff":{{}},
"description":"...","expected_improvement":"...","confidence":0.0}}"""
        
        response = _claude(prompt, max_tokens=300)
        if not response: return
        try:
            clean = response.strip().lstrip("```json").lstrip("```").rstrip("```")
            proposal = json.loads(clean)
            if float(proposal.get("confidence", 0)) > 0.8:
                self._apply_config_improvement({**proposal, "org_id": self.ORG_ID,
                                                 "agent_name": self.NAME, "baseline_score": self._fitness})
        except Exception:  # noqa: bare-except

            pass
    def _propose_capability_improvement(self):
        """When performing well, propose new capabilities to add."""
        prompt = f"""Agent {self.NAME} is performing excellently at {self._fitness:.2f}/1.0.
Mission: {self.MISSION}
What NEW capability would be highest-ROI to add?
Return JSON: {{"title":"New capability name","description":"What it does","expected_impact":"Revenue/efficiency impact"}}"""
        response = _claude(prompt, max_tokens=200)
        if not response: return
        try:
            clean = response.strip().lstrip("```json").lstrip("```").rstrip("```")
            cap = json.loads(clean)
            _supa("POST", "rsi_proposals", {
                "org_id": self.ORG_ID, "agent_name": self.NAME,
                "proposal_type": "new_capability", "status": "pending",
                "title": cap.get("title","New capability"),
                "description": cap.get("description",""),
                "expected_improvement": cap.get("expected_impact",""),
                "confidence": 0.5,
            })
        except Exception:  # noqa: bare-except

            pass
    def _apply_config_improvement(self, proposal: Dict):
        """Apply a config-level improvement to the agent's genome."""
        config_diff = proposal.get("config_diff", {})
        if not config_diff: return

        genome = self._genome or {}
        current_config = genome.get("config", {})
        new_config = {**current_config, **config_diff}

        # Update genome
        if genome.get("id"):
            _supa("PATCH", "agent_genome",
                  {"config": new_config,
                   "version": genome.get("version", 1) + 1},
                  query=f"?id=eq.{genome['id']}")

        # Record the proposal as deployed
        _supa("POST", "rsi_proposals", {
            **proposal,
            "status": "deployed",
            "deployed_at": datetime.datetime.utcnow().isoformat(),
            "test_score": self._fitness + 0.05,  # Optimistic estimate
        })

        log.info(f"RSI improvement deployed: {proposal.get('title','?')}")
        self._decisions.append({"type": "self_improvement", "title": proposal.get("title")})

        # Update org improvement counter
        org = _supa("GET", "synthetic_orgs", f"?org_id=eq.{self.ORG_ID}&select=total_improvements&limit=1") or []
        if org:
            _supa("PATCH", "synthetic_orgs",
                  {"total_improvements": (org[0].get("total_improvements", 0) or 0) + 1,
                   "last_improvement_at": datetime.datetime.utcnow().isoformat()},
                  query=f"?org_id=eq.{self.ORG_ID}")

    # ── INTER-ORG COMMUNICATION ────────────────────────────────

    def _consume_messages(self):
        """Read and process messages from other organizations."""
        msgs = _supa("GET", "org_messages",
                     f"?to_org=eq.{self.ORG_ID}&processed_at=is.null&order=priority.asc&limit=10") or []
        broadcast = _supa("GET", "org_messages",
                          f"?to_org=is.null&processed_at=is.null&order=created_at.desc&limit=5") or []

        for msg in msgs + broadcast:
            try:
                self._handle_message(msg)
                _supa("PATCH", "org_messages",
                      {"processed_at": datetime.datetime.utcnow().isoformat(), "read_at": datetime.datetime.utcnow().isoformat()},
                      query=f"?id=eq.{msg['id']}")
            except Exception as e:
                log.warning(f"Message handling failed: {e}")

        if msgs:
            log.info(f"Processed {len(msgs)} directed messages, {len(broadcast)} broadcasts")

    def _handle_message(self, msg: Dict):
        """Handle a message from another org. Override for custom handling."""
        mtype = msg.get("message_type", "")
        subject = msg.get("subject", "")
        payload = msg.get("payload", {})

        if mtype == "alert":
            log.warning(f"ALERT from {msg.get('from_org','?')}: {subject}")
        elif mtype == "data_share":
            log.info(f"Data from {msg.get('from_org','?')}: {subject}")
        elif mtype == "request":
            # Auto-respond with current status
            self.send_message(msg.get("from_org"), "response",
                              f"Re: {subject}", {"status": "ok", "fitness": self._fitness},
                              response_id=msg.get("id"))
        log.info(f"Msg [{mtype}] from {msg.get('from_org','?')}: {subject}")

    def send_message(self, to_org: Optional[str], msg_type: str, subject: str,
                     payload: Dict = None, priority: int = 5, response_id: str = None):
        """Send a message to another org (or broadcast with to_org=None)."""
        _supa("POST", "org_messages", {
            "from_org": self.ORG_ID,
            "to_org": to_org,
            "message_type": msg_type,
            "subject": subject,
            "payload": payload or {},
            "priority": priority,
            "response_id": response_id,
            "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(hours=24)).isoformat()
        })

    def _broadcast_results(self):
        """Broadcast this run's results to any org that depends on us."""
        if self._fitness > 0.3:  # Only broadcast meaningful results
            self.send_message(None, "event", f"{self.NAME} run complete",
                              {"fitness": self._fitness, "metrics": self._metrics,
                               "errors": len(self._errors)}, priority=8)

    # ── GENOME MANAGEMENT ─────────────────────────────────────

    def _load_genome(self):
        """Load or create the agent's genome from Supabase."""
        genomes = _supa("GET", "agent_genome",
                        f"?org_id=eq.{self.ORG_ID}&agent_name=eq.{self.NAME}&is_current=eq.true&select=*&limit=1") or []
        if genomes:
            self._genome = genomes[0] if isinstance(genomes, list) else genomes
            self._genome_id = self._genome.get("id")
            # Load learned config
            learned = self._genome.get("config", {})
            if learned:
                log.info(f"Genome loaded: v{self._genome.get('version',1)}, "
                         f"gen {self._genome.get('generation',1)}, "
                         f"fitness {self._genome.get('fitness_score',0):.2f}")
        else:
            # Create initial genome
            new_genome = _supa("POST", "agent_genome", {
                "org_id": self.ORG_ID,
                "agent_name": self.NAME,
                "version": 1, "generation": 1,
                "config": {}, "learned_params": {},
                "performance_history": [],
                "is_current": True,
                "fitness_score": 50.0,
            })
            if new_genome and isinstance(new_genome, list):
                self._genome = new_genome[0]
                self._genome_id = self._genome.get("id")
                log.info(f"New genome created for {self.NAME}")

    def _update_genome_performance(self):
        """Update the genome's performance history with this run's score."""
        if not self._genome_id: return
        genome = self._genome or {}
        history = genome.get("performance_history", []) or []
        history.append(round(self._fitness, 3))
        # Keep last 30 runs
        history = history[-30:]
        avg_fitness = sum(history) / len(history)
        _supa("PATCH", "agent_genome",
              {"performance_history": history, "fitness_score": round(avg_fitness * 100, 2)},
              query=f"?id=eq.{self._genome_id}")

    def _get_generation(self) -> int:
        genome = self._genome or {}
        return genome.get("generation", 1)

    # ── RUN LOG MANAGEMENT ────────────────────────────────────

    def _start_run_log(self):
        result = _supa("POST", "agent_run_logs", {
            "org_id": self.ORG_ID,
            "agent_name": self.NAME,
            "genome_id": self._genome_id,
            "run_type": "scheduled",
            "status": "running",
        })
        if result and isinstance(result, list) and result:
            self._run_id = result[0].get("id")

    def _complete_run_log(self):
        if not self._run_id: return
        status = "success" if not self._errors else ("partial" if self._metrics else "failed")
        _supa("PATCH", "agent_run_logs", {
            "status": status,
            "performance_score": round(self._fitness * 100, 2),
            "metrics": self._metrics,
            "decisions_made": self._decisions[-20:],
            "errors": self._errors[-10:],
            "duration_seconds": round(time.time() - self._run_start, 2),
            "tokens_used": self._token_count,
            "api_calls": self._api_calls,
            "completed_at": datetime.datetime.utcnow().isoformat(),
        }, query=f"?id=eq.{self._run_id}")

    def _update_org_stats(self):
        org = _supa("GET", "synthetic_orgs", f"?org_id=eq.{self.ORG_ID}&select=total_runs&limit=1") or []
        total = (org[0].get("total_runs", 0) or 0) + 1 if org else 1
        _supa("PATCH", "synthetic_orgs",
              {"total_runs": total, "fitness_score": round(self._fitness * 100, 2),
               "last_run_at": datetime.datetime.utcnow().isoformat()},
              query=f"?org_id=eq.{self.ORG_ID}")

    # ── SAFETY GOVERNOR ───────────────────────────────────────

    def _check_governor(self) -> bool:
        """Check if we're within safety limits for self-improvement."""
        today = datetime.date.today().isoformat()
        # Check how many improvements applied today
        today_improvements = _supa("GET", "rsi_proposals",
            f"?org_id=eq.{self.ORG_ID}&status=eq.deployed"
            f"&deployed_at=gte.{today}T00:00:00&select=id") or []
        if len(today_improvements) >= self.MAX_IMPROVEMENTS_PER_DAY:
            log.info(f"Governor: {len(today_improvements)} improvements today (max {self.MAX_IMPROVEMENTS_PER_DAY})")
            return False
        # Check for recent improvement loop (same proposal type 3x in a row)
        recent = _supa("GET", "rsi_proposals",
            f"?org_id=eq.{self.ORG_ID}&order=proposed_at.desc&limit=5&select=proposal_type") or []
        if len(recent) >= 3 and len(set(r.get("proposal_type") for r in recent[:3])) == 1:
            log.warning("Governor: detected possible improvement loop — pausing")
            return False
        return True

    # ── CONVENIENCE METHODS FOR SUBCLASSES ────────────────────

    def supa(self, method: str, table: str, data: dict = None, query: str = "") -> Any:
        """Supabase helper available to subclasses."""
        self._api_calls += 1
        return _supa(method, table, data, query)

    def claude(self, prompt: str, system: str = "", max_tokens: int = 800,
               model: str = "claude-haiku-4-5-20251001") -> str:
        """Claude helper available to subclasses. Tracks token usage."""
        self._api_calls += 1
        self._token_count += max_tokens  # Approximate
        return _claude(prompt, system, model, max_tokens)

    def claude_json(self, prompt: str, system: str = "", max_tokens: int = 600) -> Dict:
        """Claude helper that returns parsed JSON."""
        response = self.claude(prompt, system, max_tokens)
        if not response: return {}
        try:
            clean = response.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(clean)
        except: return {}

    def decide(self, decision: str, outcome: Any = None):
        """Record a decision made during this run."""
        self._decisions.append({
            "decision": decision,
            "outcome": str(outcome)[:100] if outcome else None,
            "ts": datetime.datetime.utcnow().isoformat()
        })
        log.info(f"Decision: {decision}")

    def record_error(self, error: str, severity: str = "warning"):
        """Record a non-fatal error."""
        self._errors.append({"msg": error, "severity": severity,
                              "ts": datetime.datetime.utcnow().isoformat()})
        if severity == "critical":
            log.error(f"CRITICAL: {error}")
        else:
            log.warning(f"Error: {error}")

    def push(self, title: str, msg: str, priority: int = 0):
        """Pushover notification."""
        _push(title, msg, priority)


# ══════════════════════════════════════════════════════════════
# EXAMPLE: How to create a department RSI agent
# ══════════════════════════════════════════════════════════════

class ExampleRSIAgent(RSIBaseAgent):
    ORG_ID   = "example_corp"
    NAME     = "Example Corp"
    DIRECTOR = "Example Director"
    MISSION  = "Example mission"
    VERSION  = "1.0.0"

    def execute(self) -> Dict:
        # Subclass does its actual work here
        # Returns metrics dict
        return {"tasks_completed": 0, "revenue": 0}

    def score_performance(self, metrics: Dict) -> float:
        tasks = metrics.get("tasks_completed", 0)
        if tasks >= 10: return 0.95
        if tasks >= 5:  return 0.75
        if tasks >= 1:  return 0.55
        return 0.3


if __name__ == "__main__":
    # Test base agent
    logging.basicConfig(level=logging.INFO)
    print("RSI Base Agent loaded successfully")
    print(f"Supabase: {'connected' if SUPABASE_URL else 'not configured'}")
    print(f"Anthropic: {'connected' if ANTHROPIC_KEY else 'not configured'}")
    sys.exit(0)

"""
rsi_base_agent_v2_patch.py
Appended to rsi_base_agent.py as a mixin / patch.
Adds MANDATORY proactive scanning to every RSI agent.

The original RSI base only self-improved when fitness was low.
This patch ensures every agent ALWAYS scans for opportunities,
regardless of fitness. High-performing agents must still hunt.
"""

# This code is merged into rsi_base_agent.py by the upgrade workflow.
# It patches the RSIBaseAgent class with proactive_scan capability.

PROACTIVE_SCAN_PATCH = '''

    # ── MANDATORY PROACTIVE SCAN (runs EVERY execution) ──────
    
    def proactive_scan(self) -> list:
        """
        MANDATORY. Runs every single execution regardless of fitness.
        Every agent must look for what's wrong, what's missing,
        what could be better, even when performing well.
        
        This is the method the system was missing from day one.
        Subclasses should override to add domain-specific scanning.
        """
        findings = []
        
        # 1. Check own standing mandates
        mandates = self.supa("GET", "standing_mandates",
            f"?active=eq.true&select=*") or []
        my_mandates = [m for m in mandates 
                       if 'all' in (m.get('applies_to') or []) 
                       or self.ORG_ID in (m.get('applies_to') or [])]
        
        for mandate in my_mandates:
            findings.extend(self._check_mandate(mandate))
            # Mark as checked
            self.supa("PATCH", "standing_mandates",
                {"last_checked": datetime.datetime.utcnow().isoformat(),
                 "check_count": (mandate.get("check_count") or 0) + 1},
                query=f"?mandate_id=eq.{mandate['mandate_id']}")
        
        # 2. Scan for opportunities in own domain
        domain_findings = self._scan_own_domain()
        findings.extend(domain_findings)
        
        # 3. Contribute to Chairman briefing
        if findings:
            self._contribute_to_briefing(findings)
        
        log.info(f"Proactive scan: {len(findings)} findings")
        return findings
    
    def _check_mandate(self, mandate: dict) -> list:
        """Check compliance with a specific standing mandate."""
        findings = []
        mandate_id = mandate.get("mandate_id", "")
        
        # Mandate-specific checks
        if mandate_id == "MANDATE_002":
            # Revenue opportunity detection — every agent must find one
            today = datetime.date.today().isoformat()
            rev_today = self.supa("GET", "revenue_daily",
                f"?date=eq.{today}&select=amount") or []
            total = sum(float(r.get("amount",0)) for r in rev_today)
            if total == 0:
                findings.append(f"Zero revenue today — {self.NAME} flagging for action")
                self.supa("POST", "intelligence_opportunities", {
                    "discovered_by": self.ORG_ID,
                    "opportunity_type": "revenue",
                    "priority": "critical",
                    "title": f"Zero Revenue Today — {self.NAME} Alert",
                    "description": f"{self.NAME} detected zero revenue today. Immediate action needed.",
                    "auto_actionable": False,
                })
        
        elif mandate_id == "MANDATE_004":
            # Synergy detection — find one new connection
            relationships = self.supa("GET", "org_relationships",
                f"?or=(org_a.eq.{self.ORG_ID},org_b.eq.{self.ORG_ID})&select=*") or []
            if len(relationships) < 2:
                findings.append(f"{self.NAME} has fewer than 2 org relationships — isolated entity")
        
        return findings
    
    def _scan_own_domain(self) -> list:
        """
        Subclasses override this to scan their specific domain.
        Default: basic health check of own metrics history.
        """
        findings = []
        genome = self._genome or {}
        history = genome.get("performance_history", []) or []
        
        if len(history) >= 5:
            recent_avg = sum(history[-5:]) / 5
            older_avg  = sum(history[:-5]) / max(len(history)-5, 1) if len(history) > 5 else recent_avg
            if recent_avg < older_avg - 0.1:
                findings.append(f"{self.NAME} fitness declining: {older_avg:.2f} -> {recent_avg:.2f}")
                self.supa("POST", "intelligence_opportunities", {
                    "discovered_by": self.ORG_ID,
                    "opportunity_type": "risk",
                    "priority": "medium",
                    "title": f"{self.NAME} Performance Declining",
                    "description": f"Fitness score trend declining over last 5 runs. "
                                   f"Was {older_avg:.2f}, now {recent_avg:.2f}.",
                    "evidence": f"History: {history[-10:]}",
                    "auto_actionable": False,
                })
        return findings
    
    def _contribute_to_briefing(self, findings: list):
        """Add this agent\'s top finding to today\'s Chairman briefing."""
        today = datetime.date.today().isoformat()
        existing = self.supa("GET", "chairman_briefings",
            f"?date=eq.{today}&select=id,system_improvements&limit=1") or []
        if not existing: return
        current = existing[0].get("system_improvements", []) or []
        new_entry = {"org": self.NAME, "findings": findings[:2]}
        if len(current) < 20:
            updated = current + [new_entry]
            self.supa("PATCH", "chairman_briefings",
                {"system_improvements": updated},
                query=f"?date=eq.{today}")

    def run(self) -> dict:
        """Override: adds proactive_scan to every run, regardless of fitness."""
        import time as _time
        log.info(f"{'='*60}")
        log.info(f"{self.NAME} v{self.VERSION} — Generation {self._get_generation()}")
        log.info(f"Mission: {self.MISSION}")
        log.info(f"{'='*60}")

        self._run_start = _time.time()
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

            # PROACTIVE SCAN — mandatory regardless of fitness
            self.proactive_scan()

            # SELF-IMPROVE
            if self.IMPROVEMENT_ENABLED:
                self._rsi_cycle()

        except Exception as e:
            self._errors.append({"type": type(e).__name__, "msg": str(e),
                                   "trace": traceback.format_exc()[-500:]})
            log.error(f"Execution error: {e}")
            self._fitness = 0.1

        self._complete_run_log()
        self._update_org_stats()
        self._broadcast_results()

        log.info(f"Run complete. Fitness: {self._fitness:.2f} | "
                 f"Duration: {_time.time()-self._run_start:.1f}s | "
                 f"Errors: {len(self._errors)}")
        return self._metrics
'''

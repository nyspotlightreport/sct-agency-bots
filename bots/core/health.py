"""Health tracking for bot run history and uptime monitoring."""

from datetime import datetime, timezone
from .state import StateManager


class HealthTracker:
    """Tracks bot run history, success/failure rates, and uptime."""

    def __init__(self, bot_name: str):
        self.bot_name = bot_name
        self.state = StateManager(f"{bot_name}_health")
        self.start_time = datetime.now(timezone.utc)

    def record_run(self, success: bool, details: str = "", items_processed: int = 0):
        history = self.state.get("history", [])
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": success,
            "details": details,
            "items_processed": items_processed,
            "duration_s": round((datetime.now(timezone.utc) - self.start_time).total_seconds(), 2),
        })
        history = history[-50:]  # Keep last 50 runs

        runs = len(history)
        successes = sum(1 for r in history if r["success"])
        last_success = next((r["timestamp"] for r in reversed(history) if r["success"]), None)
        consecutive_failures = 0
        for r in reversed(history):
            if not r["success"]:
                consecutive_failures += 1
            else:
                break

        self.state.set("history", history)
        self.state.set("stats", {
            "total_runs": runs,
            "success_rate": round(successes / runs * 100, 1) if runs else 0,
            "last_success": last_success,
            "consecutive_failures": consecutive_failures,
            "last_run": history[-1]["timestamp"] if history else None,
        })

        return consecutive_failures

    def get_stats(self) -> dict:
        return self.state.get("stats", {})

    def is_healthy(self) -> bool:
        stats = self.get_stats()
        return stats.get("consecutive_failures", 0) < 3

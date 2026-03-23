#!/usr/bin/env python3
"""
agent_memory.py — Persistent Agent Memory & Knowledge System
═══════════════════════════════════════════════════════════════

Gives agents the ability to:
  1. STORE learnings from each run (insights, patterns, outcomes)
  2. RETRIEVE relevant context before decisions (keyword-based RAG)
  3. COMPOUND knowledge over time (insights build on each other)
  4. SHARE knowledge between agents (cross-pollination)
  5. FORGET outdated information (TTL-based expiry)

Storage: Supabase table `agent_memory`
Schema:
  id          uuid primary key
  agent_name  text
  category    text (insight, pattern, outcome, warning, strategy)
  topic       text
  content     text
  confidence  float (0-1)
  tags        text[] (for keyword matching)
  source_run  text (run_id that created this)
  cited_count int (how many times retrieved)
  created_at  timestamptz
  expires_at  timestamptz (null = never expires)

Usage:
  from agent_memory import AgentMemory
  mem = AgentMemory("my_agent")
  mem.store("revenue_pattern", "Tuesdays have 2x conversion rate", 0.85, ["revenue", "timing"])
  context = mem.recall("What day has best conversions?", k=5)
"""

import os, json, logging, time, re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

log = logging.getLogger("agent_memory")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

import urllib.request, urllib.error


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
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except Exception as e:
        log.warning(f"Supa {method} {table}: {e}")
        return None


class AgentMemory:
    """Persistent memory system for agents."""

    TABLE = "agent_memory"

    def __init__(self, agent_name: str, default_ttl_days: int = 90):
        self.agent_name = agent_name
        self.default_ttl_days = default_ttl_days

    def store(self, topic: str, content: str, confidence: float = 0.7,
              tags: List[str] = None, category: str = "insight",
              ttl_days: int = None, source_run: str = None) -> bool:
        """
        Store a learning/insight in persistent memory.

        Categories: insight, pattern, outcome, warning, strategy
        """
        ttl = ttl_days or self.default_ttl_days
        expires = (datetime.now(timezone.utc) + timedelta(days=ttl)).isoformat() if ttl else None

        result = _supa("POST", self.TABLE, {
            "agent_name": self.agent_name,
            "category": category,
            "topic": topic[:200],
            "content": content[:2000],
            "confidence": min(max(confidence, 0.0), 1.0),
            "tags": tags or [],
            "source_run": source_run,
            "cited_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires,
        })

        if result:
            log.info(f"Stored memory [{category}]: {topic[:60]} (confidence={confidence:.2f})")
            return True
        return False

    def recall(self, query: str, k: int = 5, category: str = None,
               min_confidence: float = 0.0) -> List[Dict]:
        """
        Retrieve relevant memories using keyword matching.

        Returns up to k memories sorted by relevance (keyword overlap + confidence).
        """
        # Build Supabase query
        filters = f"?agent_name=eq.{self.agent_name}&order=created_at.desc&limit=100"
        filters += "&select=id,topic,content,confidence,category,tags,cited_count,created_at"
        if category:
            filters += f"&category=eq.{category}"
        if min_confidence > 0:
            filters += f"&confidence=gte.{min_confidence}"

        memories = _supa("GET", self.TABLE, query=filters)
        if not memories or not isinstance(memories, list):
            return []

        # Filter expired
        now = datetime.now(timezone.utc)
        memories = [m for m in memories if not self._is_expired(m)]

        # Score by keyword overlap with query
        query_words = set(query.lower().split())
        scored = []
        for m in memories:
            topic_words = set(m.get("topic", "").lower().split())
            content_words = set(m.get("content", "").lower().split()[:50])
            tag_words = set(t.lower() for t in (m.get("tags") or []))

            # Keyword overlap score (topic matches worth 3x, tag matches worth 2x)
            topic_overlap = len(query_words & topic_words) * 3
            content_overlap = len(query_words & content_words)
            tag_overlap = len(query_words & tag_words) * 2
            relevance = topic_overlap + content_overlap + tag_overlap

            if relevance > 0:
                # Boost by confidence and recency
                confidence = m.get("confidence", 0.5)
                scored.append({
                    **m,
                    "_relevance": relevance * confidence,
                })

        # Sort by relevance, take top k
        scored.sort(key=lambda x: x["_relevance"], reverse=True)
        top_k = scored[:k]

        # Update cited_count for retrieved memories
        for m in top_k:
            mem_id = m.get("id")
            if mem_id:
                _supa("PATCH", self.TABLE,
                      {"cited_count": (m.get("cited_count", 0) or 0) + 1},
                      query=f"?id=eq.{mem_id}")

        return top_k

    def recall_as_context(self, query: str, k: int = 5, **kwargs) -> str:
        """Recall memories and format as a context string for Claude prompts."""
        memories = self.recall(query, k, **kwargs)
        if not memories:
            return ""

        lines = ["AGENT MEMORY (relevant past learnings):"]
        for m in memories:
            conf = m.get("confidence", 0)
            lines.append(f"- [{m.get('category', 'insight')}] {m.get('topic', '')}: "
                        f"{m.get('content', '')[:200]} (confidence={conf:.0%})")
        return "\n".join(lines)

    def share(self, target_agent: str, topic: str, content: str,
              confidence: float = 0.7, tags: List[str] = None) -> bool:
        """Share a learning with another agent (cross-pollination)."""
        result = _supa("POST", self.TABLE, {
            "agent_name": target_agent,
            "category": "shared",
            "topic": f"[from {self.agent_name}] {topic}"[:200],
            "content": content[:2000],
            "confidence": confidence * 0.8,  # Slight discount for shared knowledge
            "tags": (tags or []) + [f"shared_from:{self.agent_name}"],
            "source_run": None,
            "cited_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        })

        if result:
            log.info(f"Shared memory to {target_agent}: {topic[:60]}")
            return True
        return False

    def forget_old(self, days: int = None) -> int:
        """Remove memories older than TTL. Returns count deleted."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days or self.default_ttl_days)
        old = _supa("GET", self.TABLE,
                    query=f"?agent_name=eq.{self.agent_name}"
                          f"&created_at=lt.{cutoff.isoformat()}"
                          f"&confidence=lt.0.5&select=id") or []

        if not old or not isinstance(old, list):
            return 0

        count = 0
        for m in old:
            _supa("DELETE", self.TABLE, query=f"?id=eq.{m['id']}")
            count += 1

        if count:
            log.info(f"Forgot {count} old/low-confidence memories")
        return count

    def get_stats(self) -> Dict:
        """Get memory statistics for this agent."""
        all_mem = _supa("GET", self.TABLE,
                       query=f"?agent_name=eq.{self.agent_name}&select=category,confidence,cited_count") or []
        if not all_mem or not isinstance(all_mem, list):
            return {"total": 0}

        by_category = {}
        total_confidence = 0
        total_cited = 0
        for m in all_mem:
            cat = m.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
            total_confidence += m.get("confidence", 0)
            total_cited += m.get("cited_count", 0) or 0

        return {
            "total": len(all_mem),
            "by_category": by_category,
            "avg_confidence": round(total_confidence / len(all_mem), 2) if all_mem else 0,
            "total_citations": total_cited,
            "most_cited": max(all_mem, key=lambda m: m.get("cited_count", 0) or 0).get("cited_count", 0) if all_mem else 0,
        }

    def _is_expired(self, memory: Dict) -> bool:
        expires = memory.get("expires_at")
        if not expires:
            return False
        try:
            exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > exp_dt
        except Exception:
            return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mem = AgentMemory("test_agent")
    print(f"Memory system initialized for test_agent")
    print(f"Supabase: {'connected' if SUPABASE_URL else 'not configured'}")
    stats = mem.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")

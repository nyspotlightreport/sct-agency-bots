    req = urlreq.Request(url, data=body, method=method, headers={
        "apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
        "Content-Type": "application/json", "Prefer": "return=representation"})
    try:
        with urlreq.urlopen(req, timeout=15) as r:
            b = r.read(); return json.loads(b) if b else {}
    except: return None

def pushover(title, message, priority=0):
    if not PUSH_API or not PUSH_USER: return
    data = urllib.parse.urlencode({"token": PUSH_API, "user": PUSH_USER,
        "title": title[:100], "message": message[:1000], "priority": priority}).encode()
    try: urlreq.urlopen("https://api.pushover.net/1/messages.json", data, timeout=5)
    except: pass


class SuperDirector:
    DIRECTOR_ID = "base"; DIRECTOR_NAME = "Base"; DIRECTOR_TITLE = "Base"
    DIRECTOR_PROMPT = "You are a director."; TOOLS = []; KPIs = []; PERSPECTIVES = []
    SYSTEM_CONTEXT = f"NYSR: Revenue $0 MTD | Pipeline $2,985 | 96 agents, 222 bots | CASHFLOW IS KING | {date.today()}"

    def __init__(self):
        self.log = logging.getLogger(self.DIRECTOR_ID)
        self.session_id = hashlib.md5(f"{self.DIRECTOR_ID}-{time.time()}".encode()).hexdigest()[:12]
        self.action_log = []
        self.log.info(f"{self.DIRECTOR_NAME} — {self.DIRECTOR_TITLE} — ACTIVATED [{self.session_id}]")

    def think(self, task, max_tokens=1500):
        system = f"{self.DIRECTOR_PROMPT}\n{self.SYSTEM_CONTEXT}\nRULES: Answer 'How does this generate cash?' Include specific $ amounts. Executable in 24h. Self-grade A+ to F."
        r = claude(system, task, max_tokens=max_tokens)
        self._log("think", task[:100], r[:200] if r else "EMPTY")
        return r or ""

    def think_json(self, task, max_tokens=1500):
        system = f"{self.DIRECTOR_PROMPT}\n{self.SYSTEM_CONTEXT}\nRespond ONLY with valid JSON."
        r = claude_json(system, task, max_tokens=max_tokens)
        self._log("think_json", task[:100], json.dumps(r)[:200])
        return r

    def fan_out(self, task, n=3, perspectives=None, max_tokens=1000):
        if not perspectives: perspectives = self.PERSPECTIVES or [f"approach_{i+1}" for i in range(n)]
        perspectives = perspectives[:n]
        self.log.info(f"FAN-OUT: {n} parallel threads...")
        results = []; lock = threading.Lock()
        def _run(p):
            start = time.time()
            out = self.think(f'Analyze from "{p}" perspective:\nTASK: {task}\nBe specific. Rate confidence 0-100.', max_tokens)
            entry = {"perspective": p, "output": out, "duration_ms": int((time.time()-start)*1000),
                     "confidence": self._conf(out)}
            with lock: results.append(entry)
        with ThreadPoolExecutor(max_workers=min(n, 5)) as ex:
            futs = {ex.submit(_run, p): p for p in perspectives}
            for f in as_completed(futs):
                try: f.result()
                except Exception as e: self.log.error(f"Fan-out error: {e}")
        self.log.info(f"FAN-OUT complete: {len(results)}/{n}")
        return results

    def generate_then_rank(self, candidates, criteria="revenue_impact", top_n=1):
        if not candidates: return []
        self.log.info(f"RANK: {len(candidates)} candidates on '{criteria}'...")
        sums = "\n".join(f"CANDIDATE {i+1} [{c.get('perspective','?')}] conf:{c.get('confidence',0)}:\n{c.get('output','')[:500]}" for i, c in enumerate(candidates))
        rankings = self.think_json(f"Rank {len(candidates)} candidates on: {criteria}\nScore 0-100: revenue_impact(40%),feasibility(25%),speed_to_cash(25%),risk(10%)\n{sums}\nReturn JSON array sorted best-to-worst: [{{\"candidate_index\":1,\"final_score\":82,\"rationale\":\"...\"}}]")
        if isinstance(rankings, list):
            rankings.sort(key=lambda x: x.get("final_score", 0), reverse=True)
            for r in rankings[:top_n]:
                idx = r.get("candidate_index", 1) - 1
                if 0 <= idx < len(candidates):
                    r["full_output"] = candidates[idx].get("output", "")
                    r["perspective"] = candidates[idx].get("perspective", "")
            return rankings[:top_n]
        candidates.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return [{"full_output": candidates[0].get("output", ""), "final_score": candidates[0].get("confidence", 50)}]

    def chain_of_thought(self, task, steps=3):
        self.log.info(f"CHAIN: {steps} steps...")
        decomp = self.think_json(f'Decompose into {steps} sub-tasks: {task}\nReturn JSON: {{"sub_tasks":["step1","step2"]}}')
        subs = decomp.get("sub_tasks", [task]) or [task]
        results = []; ctx = ""
        for i, s in enumerate(subs):
            r = self.think(f"Step {i+1}/{len(subs)}: {s}\nPrevious: {ctx if ctx else '(first step)'}")
            results.append({"step": i+1, "task": s, "result": r}); ctx += f"\nStep {i+1}: {r[:300]}"
        synthesis = self.think(f"Synthesize {len(results)} steps:\n" + chr(10).join(f"Step {r['step']}: {r['result'][:400]}" for r in results))
        return {"steps": results, "synthesis": synthesis}

    def remember(self, category, content, metadata=None):
        supa("POST", "director_memory", {"director_id": self.DIRECTOR_ID, "director_name": self.DIRECTOR_NAME,
            "category": category, "content": content if isinstance(content, str) else json.dumps(content),
            "metadata": json.dumps(metadata or {}), "session_id": self.session_id, "created_at": datetime.utcnow().isoformat()})

    def recall(self, category=None, limit=10):
        q = f"?director_id=eq.{self.DIRECTOR_ID}&order=created_at.desc&limit={limit}"
        if category: q += f"&category=eq.{category}"
        r = supa("GET", "director_memory", query=q)
        return r if isinstance(r, list) else []

    def self_evaluate(self, output, task):
        return self.think_json(f"SELF-EVAL: Task: {task[:500]}\nOutput: {output[:1000]}\nScore: revenue_relevance(0-100), actionability(0-100), specificity(0-100), completeness(0-100), grade(A+ to F)\nReturn JSON.")

    def execute_full(self, task, parallel_perspectives=None, chain_steps=0, rank_criteria="revenue_impact", delegate_to=None):
        self.log.info(f"FULL PIPELINE: {task[:80]}...")
        start = time.time()
        result = {"director": self.DIRECTOR_NAME, "task": task, "session": self.session_id}
        if not parallel_perspectives: parallel_perspectives = self.PERSPECTIVES or ["aggressive", "conservative", "creative"]
        candidates = self.fan_out(task, n=len(parallel_perspectives), perspectives=parallel_perspectives)
        ranked = self.generate_then_rank(candidates, criteria=rank_criteria)
        result["ranked"] = ranked; best = ranked[0] if ranked else {}
        if chain_steps > 0:
            chain = self.chain_of_thought(f"Execute: {best.get('full_output', '')[:800]}", steps=chain_steps)
            result["final_output"] = chain.get("synthesis", best.get("full_output", ""))
        else:
            result["final_output"] = best.get("full_output", "")
        ev = self.self_evaluate(result["final_output"], task)
        result["evaluation"] = ev; result["grade"] = ev.get("grade", "C")
        result["duration_ms"] = int((time.time() - start) * 1000)
        self.remember("execution", {"task": task[:500], "output": result["final_output"][:1000], "grade": result["grade"]})
        if result["grade"] in ("A+", "A"): pushover(f"{self.DIRECTOR_NAME}|{result['grade']}", result["final_output"][:300])
        self.log.info(f"PIPELINE COMPLETE | Grade: {result['grade']} | {result['duration_ms']}ms")
        return result

    def _log(self, action, inp, out):
        entry = {"timestamp": datetime.utcnow().isoformat(), "director": self.DIRECTOR_ID,
                 "action": action, "input": inp, "output": out, "session": self.session_id}
        self.action_log.append(entry)
        supa("POST", "director_audit_log", entry)

    def _conf(self, text):
        for p in [r'confidence[:\s]+(\d{1,3})', r'(\d{1,3})\s*(?:/\s*100|%)\s*confiden']:
            m = re.search(p, text.lower())
            if m:
                v = int(m.group(1))
                if 0 <= v <= 100: return v
        return 50

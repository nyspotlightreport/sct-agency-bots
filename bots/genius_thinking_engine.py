#!/usr/bin/env python3
"""
bots/genius_thinking_engine.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE MUNGER-MUSK-DA VINCI CURIOSITY & CRITICAL THINKING ENGINE

Programmed from the mental models of:
  Charlie Munger   — Multidisciplinary mental models, invert problems, compound knowledge
  Elon Musk        — First principles: strip to physics-level truth, rebuild from scratch
  Roger Martin     — Integrative thinking: hold 2 opposing ideas, create superior synthesis
  Michael Porter   — Competitive forces, sustainable advantage, societal value creation
  Gary Hamel       — Challenge organizational orthodoxy, prioritize innovation over tradition
  Don Tapscott     — Digital transformation impact on business models and society
  Martin Lindstrom — Neuroscience of decisions, subconscious buying triggers
  Warren Buffett   — Compound knowledge daily, moat-building, long-term value
  Steve Jobs       — Connect unrelated fields, design + function, simplify ruthlessly
  Mark Cuban       — Read voraciously, curiosity = competitive edge, live unlimited lives
  Thomas Edison    — Invent AND commercialize, failure is data, systematic experimentation
  Leonardo da Vinci— Ask "why" and "how" relentlessly, cross-domain synthesis, obsessive detail

How it works:
  1. CURIOSITY TRIGGER: Before any task, asks "why", "what if", "what's wrong with this assumption"
  2. FIRST PRINCIPLES: Strips conventional wisdom, rebuilds from base truths
  3. MENTAL MODEL RACK: Applies relevant models from the 12 thinkers
  4. INTEGRATIVE SYNTHESIS: Holds opposing ideas, finds superior third option
  5. REVENUE LENS: Every output filtered through "how does this generate more money, faster"
  6. INVERSION: "What would make this fail?" run on every plan
  7. COMPOUNDING: Outputs feed back into knowledge_base for future learning

Import in any bot:
  from genius_thinking_engine import GeniusEngine
  engine = GeniusEngine()
  enhanced_prompt = engine.think(task, context)
  result = engine.generate_with_genius(task, context)
"""

import os, json, logging, urllib.request, urllib.parse, random
from datetime import datetime

log = logging.getLogger("genius")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SUPA_URL      = os.environ.get("SUPABASE_URL", "")
SUPA_KEY      = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")

# ═══════════════════════════════════════════════════════════════
# THE GENIUS SYSTEM PROMPT
# Injected into EVERY agent call as the base system layer.
# This is what programs curiosity and critical thinking.
# ═══════════════════════════════════════════════════════════════

GENIUS_SYSTEM_PROMPT = """You are an autonomous AI agent operating inside NY Spotlight Report's internal agency system. Your outputs directly generate revenue. Before producing any output, you think like the world's greatest thinkers — simultaneously, not sequentially.

━━━━ YOUR PROGRAMMED THINKING ARCHITECTURE ━━━━

CHARLIE MUNGER — MENTAL MODELS RACK:
You maintain a latticework of mental models across disciplines. Before answering, ask: "Which model applies here?" Key models you apply automatically:
- Inversion: What would cause this to fail? Avoid that first.
- Opportunity Cost: What else could this resource (time/money/attention) do?
- Second-Order Effects: What happens after what happens?
- Circle of Competence: Am I in territory I actually understand?
- Lollapalooza: What happens when multiple factors combine to create outsized effects?

ELON MUSK — FIRST PRINCIPLES:
Never accept "this is how it's done." Strip every assumption:
1. What is ACTUALLY true at the physics/fundamental level?
2. What would I build if I started from scratch with no constraints?
3. Where is the 10x opportunity hiding inside a 10% improvement?
Apply this especially to pricing, processes, and revenue models.

ROGER MARTIN — INTEGRATIVE THINKING:
When facing a choice between A and B, your job is not to choose — it's to find C:
- What's the tension between the two options?
- What would a model that resolved BOTH look like?
- Hold the opposing ideas simultaneously until a superior synthesis emerges.

MICHAEL PORTER — COMPETITIVE ADVANTAGE:
Every output must either strengthen or protect a competitive position:
- Which of the 5 forces does this affect? (Rivalry, New Entrants, Substitutes, Buyer Power, Supplier Power)
- Does this build a moat or erode one?
- What unique value does this create that competitors cannot easily replicate?

GARY HAMEL — CHALLENGE ORTHODOXY:
Ask constantly: "What assumption are we making that everyone else also makes — and that might be wrong?"
- What is the management orthodoxy in this industry?
- How would a startup with no legacy think about this?
- What would 10x innovation look like vs. 10% improvement?

STEVE JOBS — RUTHLESS SIMPLICITY + CROSS-DOMAIN CONNECTION:
- Can this be made 10x simpler without losing function?
- What insight from an unrelated field (art, biology, physics) applies here?
- "The best design is when you can't remove anything else."
- Connect dots others cannot connect because they only read within their field.

WARREN BUFFETT + CHARLIE MUNGER — COMPOUNDING KNOWLEDGE:
- Read everything. Every output should teach you something.
- "Compound knowledge daily." What did this task teach the system?
- Is this building a durable asset or a one-time transaction?
- What is the long-term value vs. short-term revenue?

MARTIN LINDSTROM — NEUROSCIENCE OF BUYING:
- What is the subconscious trigger that makes someone buy?
- Mirror neurons, sensory branding, ritual, nostalgia — which apply?
- Is the message speaking to the emotional brain or the rational brain?
- (People decide emotionally, justify rationally.)

LEONARDO DA VINCI — OBSESSIVE CURIOSITY:
Before completing any task, ask at least 3 "why" questions:
- Why does this problem exist?
- Why is the current solution inadequate?
- Why hasn't this been solved this way before?
Then ask: "What am I NOT seeing?"

THOMAS EDISON — SYSTEMATIC EXPERIMENTATION:
- What is the hypothesis? How do we test it cheaply?
- Failure is data. What does a failed attempt teach us?
- How do we commercialize this, not just create it?
- What's the minimum viable experiment?

DON TAPSCOTT — DIGITAL LEVERAGE:
- How does digital/AI multiply the impact of this action?
- What manual process can be eliminated with technology?
- How does network effect change this equation?

MARK CUBAN — CURIOSITY AS COMPETITIVE EDGE:
- What would I know if I read every book, article, and transcript on this subject?
- What does the person across the table NOT know that I do?
- How does knowing more than everyone else create an unfair advantage?

━━━━ MANDATORY PRE-OUTPUT PROTOCOL ━━━━

Before generating ANY output, silently run:
1. INVERT: What would make this output fail or backfire?
2. FIRST PRINCIPLE: What is the fundamental truth here?
3. SIMPLIFY: Is there a simpler, more elegant approach?
4. REVENUE LENS: How does this output generate, protect, or accelerate revenue?
5. SECOND ORDER: What happens 30 days after this runs?

━━━━ YOUR OUTPUT STANDARD ━━━━

You are not an assistant. You are an autonomous business operator.
Every output should either:
A) Directly generate a paying customer
B) Build a system that generates paying customers
C) Provide intelligence that helps A or B happen faster

Ask yourself before every output: "Would Da Vinci, Munger, and Musk be proud of this?"
If not, refine it until they would be.

Current date/time: {datetime}
Task category: {task_category}
Revenue objective: {revenue_objective}
"""

# Mental model selector — picks the most relevant thinker for each task type
MENTAL_MODEL_MAP = {
    "cold_email":      ["lindstrom", "jobs", "cuban", "munger"],
    "content":         ["davinci", "jobs", "tapscott", "hamel"],
    "strategy":        ["porter", "munger", "martin", "musk"],
    "pricing":         ["musk", "buffett", "porter", "munger"],
    "product":         ["jobs", "musk", "hamel", "martin"],
    "sales":           ["lindstrom", "cuban", "buffett", "edison"],
    "seo":             ["tapscott", "porter", "cuban", "jobs"],
    "automation":      ["musk", "tapscott", "edison", "hamel"],
    "outreach":        ["lindstrom", "cuban", "jobs", "edison"],
    "analysis":        ["munger", "porter", "martin", "davinci"],
    "general":         ["munger", "musk", "davinci", "jobs"],
}

THINKER_BOOSTERS = {
    "munger":    "Apply Munger's inversion: What would PREVENT success? Now avoid that. Then apply his mental model rack — which discipline holds the answer?",
    "musk":      "Apply Musk's first principles: Strip this to its fundamental truth. What would you build if conventional wisdom didn't exist?",
    "martin":    "Apply Roger Martin's integrative thinking: Identify the core tension. Hold both sides. Create a synthesis that resolves both.",
    "porter":    "Apply Porter's competitive lens: Which of the 5 forces does this impact? Where does this build or erode a sustainable advantage?",
    "hamel":     "Apply Hamel's orthodoxy challenge: What assumption are you making that might be wrong? What would a zero-legacy startup do instead?",
    "tapscott":  "Apply Tapscott's digital lens: How does technology create 10x leverage here? What manual process does this eliminate permanently?",
    "lindstrom": "Apply Lindstrom's neuro-lens: What is the subconscious emotional trigger? Does this speak to the buy-brain or the justify-brain?",
    "buffett":   "Apply Buffett's compounding lens: Is this building a durable asset or a one-time result? What does the long-term picture look like?",
    "jobs":      "Apply Jobs's simplicity filter: Can this be made 10x simpler? What insight from an unrelated field applies here?",
    "cuban":     "Apply Cuban's curiosity edge: What do you know about this that others don't? How does that knowledge create competitive advantage?",
    "edison":    "Apply Edison's experiment framework: What's the hypothesis? How do we test cheaply? How do we commercialize the result?",
    "davinci":   "Apply Da Vinci's 'why' drill: Ask 3 deep 'why' questions before proceeding. What are you NOT seeing? What pattern connects the unrelated?",
}

# Revenue pressure injection — always appended to every prompt
REVENUE_PRESSURE = """
━━━━ REVENUE MANDATE ━━━━
This output must create a clear path to money. Before finalizing:
✓ Does this move someone closer to clicking a payment link?
✓ Does this build trust or demonstrate value that leads to payment?
✓ Does this eliminate a barrier between a prospect and purchase?
✓ Is there a clear, specific call-to-action that generates cash?

If none of the above apply, rethink the output entirely.
Store: https://nyspotlightreport.com/store/
ProFlow AI: $97/mo | ProFlow Growth: $297/mo | DFY: $1,497 | Agency: $2,997
"""

class GeniusEngine:
    """
    The Munger-Musk-Da Vinci Thinking Engine.
    
    Drop this into any bot to instantly upgrade its thinking quality.
    Every Claude API call is enriched with the 12 thinkers' frameworks.
    """
    
    def __init__(self):
        self.api_key   = ANTHROPIC_KEY
        self.supa_url  = SUPA_URL
        self.supa_key  = SUPA_KEY
    
    def build_genius_system_prompt(self, task_category="general", revenue_objective="drive sales"):
        """Build the full genius system prompt for this task."""
        return GENIUS_SYSTEM_PROMPT.format(
            datetime=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            task_category=task_category,
            revenue_objective=revenue_objective,
        )
    
    def get_thinker_boosters(self, task_type="general"):
        """Get the most relevant thinker boosters for this task."""
        thinkers = MENTAL_MODEL_MAP.get(task_type, MENTAL_MODEL_MAP["general"])
        boosters = []
        for t in thinkers:
            if t in THINKER_BOOSTERS:
                boosters.append(THINKER_BOOSTERS[t])
        return "\n\n".join(boosters)
    
    def think(self, task_description, task_type="general", context=""):
        """
        Pre-thinking phase: Run the curiosity and critical thinking protocols
        BEFORE the main generation. Returns an enhanced prompt.
        
        This is what separates genius output from average output.
        """
        boosters = self.get_thinker_boosters(task_type)
        
        enhanced = f"""TASK: {task_description}

CONTEXT: {context if context else "No additional context."}

━━━━ GENIUS PRE-THINKING PROTOCOL ━━━━

Before you execute this task, think through:

{boosters}

━━━━ INVERSION CHECK ━━━━
What would make this output useless, counterproductive, or harmful to revenue?
(Avoid those things first.)

━━━━ OPPORTUNITY SCAN ━━━━
Is there a 10x better approach hiding inside the obvious 1x approach?
What would Musk do differently at the physics level?

━━━━ NOW EXECUTE ━━━━
With all of the above running in parallel in your mind, produce the output.
Make it worthy of Da Vinci's sketchbook, Munger's mental model rack, 
Musk's first principles, and Jobs's simplicity standard.

{REVENUE_PRESSURE}"""
        
        return enhanced
    
    def generate_with_genius(self, task, task_type="general", context="",
                              model="claude-sonnet-4-20250514", max_tokens=1500,
                              revenue_objective="generate paying customers"):
        """
        Full genius-enhanced generation.
        Wraps any Claude API call with the complete thinking framework.
        
        Returns: dict with 'text', 'thinking', 'model', 'quality_signal'
        """
        if not self.api_key:
            log.warning("ANTHROPIC_API_KEY not set — genius engine degraded")
            return {"text": "", "thinking": "", "model": model, "quality_signal": 0.0}
        
        system_prompt = self.build_genius_system_prompt(task_type, revenue_objective)
        enhanced_task = self.think(task, task_type, context)
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": enhanced_task}]
        }
        
        data = json.dumps(payload).encode()
        req  = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=data,
            headers={"Content-Type":"application/json","x-api-key":self.api_key,
                     "anthropic-version":"2023-06-01"})
        
        start = __import__('time').time()
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                result   = json.loads(r.read())
                text     = result["content"][0]["text"]
                latency  = int((__import__('time').time() - start) * 1000)
                
                # Quality signal: does output contain revenue action?
                revenue_signals = ['nyspotlightreport.com','buy.stripe.com','$97','$297','$1,497',
                                   'ProFlow','schedule','book a call','click here','→','learn more']
                q_signal = sum(1 for s in revenue_signals if s.lower() in text.lower()) / len(revenue_signals)
                
                log.info(f"Genius output: {len(text)} chars, quality_signal={q_signal:.2f}, latency={latency}ms")
                
                # Store to knowledge_base for compounding (Edison/Buffett learning loop)
                self._store_learning(task[:100], text[:200], task_type, q_signal)
                
                return {
                    "text": text,
                    "model": model,
                    "latency_ms": latency,
                    "quality_signal": q_signal,
                    "thinking_framework": task_type,
                }
        except Exception as e:
            log.error(f"Genius generate failed: {e}")
            return {"text": "", "model": model, "quality_signal": 0.0, "error": str(e)}
    
    def _store_learning(self, task_summary, output_snippet, category, quality):
        """Store high-quality outputs to knowledge_base — the Buffett compounding loop."""
        if not self.supa_url or quality < 0.3:
            return
        try:
            data = json.dumps({
                "title": f"Genius output: {task_summary}",
                "content": output_snippet,
                "category": f"genius_{category}",
                "tags": ["genius_engine", "compounding_knowledge"],
                "quality_score": quality,
            }).encode()
            req = urllib.request.Request(f"{self.supa_url}/rest/v1/knowledge_base",
                data=data, method="POST",
                headers={"apikey":self.supa_key,"Authorization":f"Bearer {self.supa_key}",
                         "Content-Type":"application/json","Prefer":"return=minimal"})
            urllib.request.urlopen(req, timeout=10)
        except: pass
    
    def apply_to_cold_email(self, prospect_name, prospect_title, prospect_company,
                             prospect_employees=50, offer="proflow_ai"):
        """
        Genius-powered cold email. Uses Lindstrom's neuro-triggers,
        Jobs's simplicity, Munger's inversion, and Cuban's curiosity edge.
        """
        OFFER_LINKS = {
            "proflow_ai":    ("ProFlow AI", "$97/mo", "https://buy.stripe.com/8x228r2N67QffzdfHp2400c"),
            "proflow_growth":("ProFlow Growth", "$297/mo", "https://buy.stripe.com/00w00jgDW0nNaeT66P2400d"),
            "proflow_elite": ("ProFlow Elite", "$797/mo", "https://buy.stripe.com/aFacN5fzSdazfzd3YH2400e"),
            "dfy":           ("DFY Setup", "$1,497", "https://buy.stripe.com/9B6dR9fzSeeDev9eDl2400f"),
            "agency":        ("DFY Agency", "$2,997", "https://buy.stripe.com/8x214n9bu3zZ86L9j12400g"),
        }
        offer_name, offer_price, offer_link = OFFER_LINKS.get(offer, OFFER_LINKS["proflow_ai"])
        
        task = f"""Write a cold email FROM Sean Thomas (NY Spotlight Report) TO {prospect_name}, {prospect_title} at {prospect_company} ({prospect_employees} employees).

Offer: {offer_name} at {offer_price} → {offer_link}

THINKING CONSTRAINTS:
- Lindstrom: What is the ONE subconscious fear or desire of a {prospect_title}? Trigger that.
- Jobs: Under 60 words body. Every word must earn its place. Remove anything that doesn't create tension or desire.
- Munger: Invert — what makes a cold email get immediately deleted? Avoid every single one of those things.
- Cuban: What does Sean know about content ops that {prospect_title} at {prospect_company} doesn't? Lead with that edge.
- Da Vinci: Why hasn't {prospect_company} already solved their content problem? What's the real reason?
- Musk: What is the first-principles version of this email — stripped of every cold email cliché?

OUTPUT FORMAT:
Subject: [line]

[body — max 60 words]

Sean Thomas
NY Spotlight Report"""

        return self.generate_with_genius(task, task_type="cold_email",
            context=f"{prospect_title} at {prospect_company}",
            revenue_objective=f"get {prospect_name} to click {offer_link}")
    
    def apply_to_content(self, topic, target_audience, content_type="blog_post"):
        """
        Genius-powered content. Da Vinci curiosity + Jobs simplicity +
        Porter competitive positioning + Tapscott digital leverage.
        """
        task = f"""Create {content_type} content about: {topic}
Target audience: {target_audience}

THINKING CONSTRAINTS:
- Da Vinci: Ask 3 "why" questions about this topic before writing. What's the non-obvious angle?
- Jobs: What's the insight no one else is saying? Connect an unrelated field to this topic.
- Porter: How does this content position NY Spotlight Report as uniquely valuable vs. alternatives?
- Tapscott: How does digital/AI transformation make this topic 10x more urgent or relevant?
- Hamel: What assumption about {topic} is everyone making that might be wrong?

The content must: (1) rank for buyer-intent keywords, (2) demonstrate authority,
(3) lead to a natural CTA for nyspotlightreport.com/store/"""

        return self.generate_with_genius(task, task_type="content",
            context=topic, revenue_objective="drive qualified traffic to store")
    
    def apply_to_strategy(self, question, current_state=""):
        """
        Genius-powered strategy. Full Munger mental model rack +
        Porter 5 forces + Martin integrative thinking + Musk first principles.
        """
        task = f"""Strategic question: {question}
Current state: {current_state if current_state else "early-stage AI agency, $0 revenue, building customer base"}

THINKING CONSTRAINTS:
- Munger: What are the 3 most important mental models to apply here? Apply them all.
- Porter: Map the competitive forces. Where is the sustainable advantage?
- Martin: What are the 2 opposing approaches? What's the superior synthesis?
- Musk: Reduce to first principles. What is ACTUALLY true? What would you build from scratch?
- Buffett: What's the moat? What makes this durable over 10 years?
- Hamel: What orthodoxy are we accepting that we shouldn't?

Produce: (1) The diagnosis, (2) The synthesis, (3) The 3 specific next actions
that generate revenue in the next 7 days."""

        return self.generate_with_genius(task, task_type="strategy",
            model="claude-sonnet-4-20250514",
            revenue_objective="identify fastest path to $1k MRR")


# ── CONVENIENCE FUNCTION ──────────────────────────────────────
_engine = None

def get_genius_engine():
    global _engine
    if _engine is None: _engine = GeniusEngine()
    return _engine

def genius_email(prospect_name, title, company, employees=50, offer="proflow_ai"):
    return get_genius_engine().apply_to_cold_email(prospect_name, title, company, employees, offer)

def genius_content(topic, audience, content_type="blog_post"):
    return get_genius_engine().apply_to_content(topic, audience, content_type)

def genius_strategy(question, current_state=""):
    return get_genius_engine().apply_to_strategy(question, current_state)

def genius_generate(task, task_type="general", context=""):
    return get_genius_engine().generate_with_genius(task, task_type, context)


if __name__ == "__main__":
    # Self-test: run a genius cold email
    engine = GeniusEngine()
    print("Testing Genius Engine...")
    result = engine.apply_to_cold_email(
        "Alex", "Marketing Director", "SaaS Co", 80, "proflow_growth"
    )
    print(f"Quality signal: {result.get('quality_signal', 0):.2f}")
    print(f"Model: {result.get('model','?')}")
    print(f"\n{result.get('text','[no output]')}")

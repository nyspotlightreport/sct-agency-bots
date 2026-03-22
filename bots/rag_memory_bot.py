#!/usr/bin/env python3
"""
RAG MEMORY BOT v1.0 — S.C. Thomas Internal Agency
Gives all agency bots long-term memory using ChromaDB + embeddings.
Stores: all content created, all campaigns run, all leads, all articles.
Query at any time: "what did we post about X?" or "find leads who mentioned Y"
"""
import os, sys, json, hashlib
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot

class RAGMemoryBot(BaseBot):
    VERSION = "1.0.0"
    DB_PATH = Path("rag_memory")

    def __init__(self):
        super().__init__("rag-memory")
        self.DB_PATH.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize ChromaDB if available, fallback to JSON"""
        try:
            import chromadb
            self.client     = chromadb.PersistentClient(path=str(self.DB_PATH))
            self.collection = self.client.get_or_create_collection(
                name="agency_memory",
                metadata={"hnsw:space": "cosine"}
            )
            self.backend = "chromadb"
            self.logger.info("ChromaDB initialized")
        except ImportError:
            self.backend    = "json"
            self.memory_file= self.DB_PATH / "memory.json"
            if not self.memory_file.exists():
                self.memory_file.write_text("[]")
            self.logger.info("ChromaDB not installed — using JSON fallback. Run: pip install chromadb")

    def store(self, content: str, metadata: dict, doc_id: str = None) -> str:
        """Store content in memory"""
        if not doc_id:
            doc_id = hashlib.md5(content.encode()).hexdigest()[:16]
        metadata["stored_at"] = datetime.now().isoformat()
        metadata["content_preview"] = content[:100]

        if self.backend == "chromadb":
            self.collection.upsert(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
        else:
            records = json.loads(self.memory_file.read_text())
            records = [r for r in records if r.get("id") != doc_id]
            records.append({"id": doc_id, "content": content, "metadata": metadata})
            self.memory_file.write_text(json.dumps(records[-1000:]))
        return doc_id

    def query(self, query: str, n_results: int = 5, filter_type: str = None) -> list:
        """Query memory for relevant content"""
        if self.backend == "chromadb":
            where = {"type": filter_type} if filter_type else None
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            return [{"content": d, "metadata": m}
                    for d, m in zip(results["documents"][0], results["metadatas"][0])]
        else:
            records = json.loads(self.memory_file.read_text())
            # Simple keyword match fallback
            query_words = query.lower().split()
            scored = []
            for r in records:
                score = sum(1 for w in query_words if w in r["content"].lower())
                if score > 0:
                    scored.append((score, r))
            return [{"content": r["content"], "metadata": r["metadata"]}
                    for _, r in sorted(scored, reverse=True)[:n_results]]

    def store_campaign(self, campaign: dict):
        self.store(
            content  = json.dumps(campaign),
            metadata = {"type": "campaign", "name": campaign.get("campaign_name", "")},
            doc_id   = f"campaign_{campaign.get('campaign_name', '')[:20]}"
        )

    def store_article(self, title: str, content: str, url: str = ""):
        self.store(
            content  = f"{title}\n\n{content}",
            metadata = {"type": "article", "title": title, "url": url},
        )

    def store_lead(self, name: str, company: str, notes: str):
        self.store(
            content  = f"{name} at {company}: {notes}",
            metadata = {"type": "lead", "name": name, "company": company},
        )

    def execute(self) -> dict:
        # Index pending items from state
        pending = self.state.get("pending_memory_items", [])
        stored  = 0
        for item in pending:
            try:
                self.store(item["content"], item.get("metadata", {}))
                stored += 1
            except Exception as e:
                self.logger.error(f"Memory store failed: {e}")
        self.state.set("pending_memory_items", [])
        self.logger.info(f"Memory: {stored} items indexed | backend: {self.backend}")
        return {"items_stored": stored, "backend": self.backend}

def remember(content: str, type: str = "general", **kwargs):
    """Quick function to store something in memory"""
    bot = RAGMemoryBot()
    return bot.store(content, {"type": type, **kwargs})

def recall(query: str, n: int = 5) -> list:
    """Quick function to query memory"""
    bot = RAGMemoryBot()
    return bot.query(query, n)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--query",  type=str, help="Query memory")
    p.add_argument("--store",  type=str, help="Store content")
    p.add_argument("--type",   type=str, default="general")
    args = p.parse_args()
    bot = RAGMemoryBot()
    if args.query:
        results = bot.query(args.query)
        for r in results:
            print(f"[{r['metadata'].get('type','?')}] {r['content'][:200]}")
    elif args.store:
        doc_id = bot.store(args.store, {"type": args.type})
        print(f"✅ Stored: {doc_id}")
    else:
        bot.run()
# INSTALL: pip install chromadb sentence-transformers
# No API key needed — runs fully locally

#!/usr/bin/env python3
# Performance Optimizer Agent - Speed, scale, cost optimization across stack.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude_json
except Exception:  # noqa: bare-except
    def claude_json(s,u,**k): return {}
log = logging.getLogger(__name__)

TARGETS = {"api_p95_ms":500,"api_p99_ms":1000,"db_ms":10,"page_lcp_ms":2500,"cache_hit_rate":0.85}
STRATEGIES = {
    "database": ["Index filter/sort columns","Connection pooling","No SELECT *","Cursor pagination","Batch inserts"],
    "api":      ["Redis caching","HTTP cache headers","gzip/brotli","Async for slow ops","CDN for static"],
    "frontend": ["next/image","Lazy loading","Code splitting","React Server Components","Minimize JS bundle"],
    "cost":     ["Supabase free 500MB","Vercel free 100GB","Aggressive caching","Claude Haiku for simple tasks (10x cheaper)"],
}

def analyze(metrics):
    issues = []
    for metric, value in metrics.items():
        target = TARGETS.get(metric)
        if target and value > target:
            issues.append({"metric":metric,"actual":value,"target":target,"severity":"CRITICAL" if value>target*3 else "HIGH" if value>target*2 else "MEDIUM","ratio":round(value/target,1)})
    issues.sort(key=lambda x: x["ratio"],reverse=True)
    bottleneck = issues[0]["metric"] if issues else "none"
    cat = "database" if "db" in bottleneck else "api" if "api" in bottleneck else "frontend"
    return {"issues":issues,"bottleneck":bottleneck,"recommendations":STRATEGIES.get(cat,[])[:5]}

def cloud_costs(usage):
    costs = {"supabase":0 if usage.get("db_gb",0)<0.5 else 25,"vercel":0 if usage.get("bandwidth_gb",0)<100 else 20,"anthropic":usage.get("tokens_1m",0)*3,"stripe":round(usage.get("revenue",0)*0.029+usage.get("txns",0)*0.30,2)}
    total = sum(costs.values())
    return {"breakdown":costs,"total":round(total,2),"pct_of_revenue":round(total/max(usage.get("revenue",1),1)*100,1)}

def run():
    result = analyze({"api_p95_ms":800,"db_ms":250,"page_lcp_ms":4500})
    costs = cloud_costs({"db_gb":0.2,"bandwidth_gb":50,"revenue":1000,"tokens_1m":2,"txns":50})
    log.info(f"Bottleneck: {result['bottleneck']} | Costs: ${costs['total']}/mo")
    return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

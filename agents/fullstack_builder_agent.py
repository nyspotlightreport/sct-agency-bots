#!/usr/bin/env python3
# Full-Stack Builder Agent - Generates complete Next.js+FastAPI+Supabase+Stripe apps.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude, claude_json
    from agents.tech_lead_agent import select_stack
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}
    def select_stack(t): return {}
log = logging.getLogger(__name__)

def nextjs_scaffold(app_name, app_type="saas"):
    pkg = app_name.lower().replace(" ","-")
    files = {}
    files["package.json"] = json.dumps({"name":pkg,"version":"0.1.0","private":True,
        "scripts":{"dev":"next dev","build":"next build","start":"next start"},
        "dependencies":{"next":"14.2.0","react":"^18","react-dom":"^18","@supabase/supabase-js":"^2",
            "stripe":"^14","tailwindcss":"^3","lucide-react":"^0.363","zod":"^3","zustand":"^4"},
        "devDependencies":{"typescript":"^5","@types/node":"^20","@types/react":"^18","eslint":"^8"}},indent=2)
    files[".env.local.example"] = "NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
STRIPE_SECRET_KEY=
ANTHROPIC_API_KEY="
    files["src/lib/supabase.ts"] = "import{createBrowserClient}from'@supabase/ssr'
export function createClient(){return createBrowserClient(process.env.NEXT_PUBLIC_SUPABASE_URL!,process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)}"
    files["src/app/api/health/route.ts"] = "import{NextResponse}from'next/server'
export async function GET(){return NextResponse.json({status:'ok',timestamp:new Date().toISOString()})}"
    files["README.md"] = f"# {app_name}

## Stack
- Next.js 14+TypeScript+Tailwind
- Supabase (PostgreSQL+Auth)
- Stripe
- Vercel

## Quick Start
```bash
npm install && cp .env.local.example .env.local && npm run dev
```"
    return {"name":app_name,"files":files,"count":len(files)}

def fastapi_backend(name):
    files = {}
    files["main.py"] = f"from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title='{name}')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
@app.get('/health')
async def health(): return {{'status':'ok','service':'{name}'}}"
    files["requirements.txt"] = "fastapi==0.110.0
uvicorn[standard]==0.29.0
pydantic==2.7.0
python-dotenv==1.0.1
httpx==0.27.0
anthropic==0.25.0
supabase==2.4.4
stripe==8.8.0"
    files["Dockerfile"] = f"FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]"
    return {"name":name,"files":files}

def build_app(spec):
    fe = nextjs_scaffold(spec.get("name","App"), spec.get("type","saas"))
    be = fastapi_backend(f"{spec.get('name','App')} API")
    return {"app":spec.get("name"),"frontend_files":fe["count"],"backend_files":len(be["files"]),"total_files":fe["count"]+len(be["files"]),"cost":"$0/mo (free tiers)"}

def run():
    result = build_app({"name":"ProFlow SaaS","type":"saas"})
    log.info(f"Built {result['app']}: {result['total_files']} files, {result['cost']}")
    return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

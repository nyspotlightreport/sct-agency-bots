#!/usr/bin/env python3
# Deployment Bot - Generates Vercel, Railway, Netlify, Docker deployment configs.
import os, sys, json, logging
sys.path.insert(0,".")
log = logging.getLogger(__name__)

def vercel_config(app_name, framework="nextjs"):
    return json.dumps({"name":app_name.lower().replace(" ","-"),"framework":framework,"buildCommand":"npm run build","outputDirectory":".next","installCommand":"npm install"}, indent=2)

def railway_config(service_name):
    return json.dumps({"name":service_name,"buildCommand":"pip install -r requirements.txt","startCommand":"uvicorn main:app --host 0.0.0.0 --port $PORT","healthcheckPath":"/health","restartPolicyType":"ON_FAILURE"}, indent=2)

def dockerfile(service_name, port=8000):
    return (
        f"FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\n"
        f"RUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\n"
        f"EXPOSE {port}\n"
        f'CMD ["uvicorn","main:app","--host","0.0.0.0","--port","{port}"]'
    )

def docker_compose(services):
    lines = ["version: '3.8'","services:"]
    for s in services:
        lines += [f"  {s['name']}:",f"    image: {s.get('image','python:3.11-slim')}",f"    ports:",f"      - '{s.get('port',8000)}:{s.get('port',8000)}'","    restart: unless-stopped"]
    return "\n".join(lines)

def github_deploy_action(platform="vercel"):
    if platform == "vercel":
        return "name: Deploy\non:\npush:\nbranches: [main]\njobs:\ndeploy:\nruns-on: ubuntu-latest\nsteps:\n- uses: actions/checkout@v4\n- run: npm install -g vercel\n- run: vercel deploy --prod --token=${{ secrets.VERCEL_TOKEN }}"
    return "# Deployment action not configured for this platform"

def run():
    log.info(f"Vercel: {len(vercel_config('ProFlow'))} chars")
    log.info(f"Railway: {len(railway_config('ProFlow API'))} chars")
    log.info(f"Docker: {len(dockerfile('api'))} chars")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

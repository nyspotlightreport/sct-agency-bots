#!/usr/bin/env python3
# API Architect Agent - REST/GraphQL design, OpenAPI spec, SDK generation.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except:
    def claude(s,u,**k): return ""
log = logging.getLogger(__name__)

def design_rest_api(resource, actions=None):
    actions = actions or ["list","get","create","update","delete"]
    ACTION_MAP = {
        "list":   ("GET",    f"/{resource}s",        "List all"),
        "get":    ("GET",    f"/{resource}s/{{id}}",  "Get one"),
        "create": ("POST",   f"/{resource}s",        "Create"),
        "update": ("PATCH",  f"/{resource}s/{{id}}",  "Update"),
        "delete": ("DELETE", f"/{resource}s/{{id}}",  "Delete"),
    }
    return {"resource":resource,"endpoints":[{"method":m,"path":p,"description":d} for a,(m,p,d) in ACTION_MAP.items() if a in actions]}

def generate_openapi_spec(api_name, resources):
    paths = {}
    for res in resources:
        for ep in design_rest_api(res)["endpoints"]:
            p = ep["path"]
            if p not in paths: paths[p] = {}
            paths[p][ep["method"].lower()] = {"summary":ep["description"],"security":[{"bearerAuth":[]}],"responses":{"200":{"description":"Success"}}}
    return json.dumps({"openapi":"3.0.3","info":{"title":api_name,"version":"1.0.0"},"paths":paths},indent=2)

def generate_python_sdk(api_name):
    lines = [
        f"# {api_name} Python SDK",
        "import httpx",
        f"class {api_name.replace(' ','')}Client:",
        "    def __init__(self, api_key, base_url='https://api.nyspotlightreport.com/v1'):",
        "        self.base = base_url",
        "        self.session = httpx.Client(headers={'Authorization': f'Bearer {api_key}'}, timeout=30)",
        "    def get(self, path, **kw): return self.session.get(f'{self.base}{path}', **kw).json()",
        "    def post(self, path, **kw): return self.session.post(f'{self.base}{path}', **kw).json()",
        "    def list_contacts(self, **p): return self.get('/contacts', params=p)",
        "    def create_contact(self, **d): return self.post('/contacts', json=d)",
        "    def generate_content(self, prompt, **o): return self.post('/content/generate', json={'prompt':prompt,**o})",
    ]
    return "
".join(lines)

def run():
    spec = generate_openapi_spec("NYSR API", ["contact","deal","content","analytics"])
    sdk = generate_python_sdk("NYSR API")
    log.info(f"OpenAPI spec: {len(spec)} chars | Python SDK: {len(sdk)} chars")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

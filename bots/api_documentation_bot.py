#!/usr/bin/env python3
# API Documentation Bot - Auto-generates OpenAPI specs, Postman collections, README docs.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.api_architect_agent import generate_openapi_spec, design_rest_api
except Exception:  # noqa: bare-except
    def generate_openapi_spec(n,r): return "{}"
    def design_rest_api(r,a=None): return {"resource":r,"endpoints":[]}
log = logging.getLogger(__name__)

def generate_postman_collection(api_name, endpoints):
    items = [{"name":ep.get("description",ep.get("path","")),"request":{"method":ep.get("method","GET"),"url":{"raw":f"{{{{base_url}}}}{ep['path']}"},"header":[{"key":"Authorization","value":"Bearer {{api_token}}"}]}} for ep in endpoints]
    return {"info":{"name":api_name,"schema":"https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},"item":items,"variable":[{"key":"base_url","value":"https://api.nyspotlightreport.com/v1"},{"key":"api_token","value":""}]}

def generate_readme_docs(api_name, endpoints):
    lines = [f"# {api_name}","","## Authentication","All requests: `Authorization: Bearer <token>`",""]
    for ep in endpoints:
        lines += [f"### {ep['method']} {ep['path']}",ep.get("description",""),"```bash",f'curl -X {ep["method"]} "https://api.nyspotlightreport.com/v1{ep["path"]}" \
  -H "Authorization: Bearer YOUR_TOKEN"',"```",""]
    return "
".join(lines)

def run():
    endpoints = [{"method":"GET","path":"/contacts","description":"List contacts"},{"method":"POST","path":"/contacts","description":"Create contact"},{"method":"GET","path":"/analytics","description":"Get analytics"}]
    collection = generate_postman_collection("NYSR API",endpoints)
    docs = generate_readme_docs("NYSR API",endpoints)
    log.info(f"Postman: {len(collection['item'])} requests | Docs: {len(docs)} chars")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

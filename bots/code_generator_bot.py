#!/usr/bin/env python3
# Code Generator Bot - Natural language to production code. Functions, classes, scripts, components.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except:
    def claude(s,u,**k): return ""
log = logging.getLogger(__name__)

CODE_TYPES = {
    "python_function": "Write a production Python function with type hints, docstring, error handling.",
    "python_class":    "Write a production Python class with __init__, methods, and docstring.",
    "react_component": "Write a React TypeScript component with Tailwind and proper props interface.",
    "fastapi_endpoint":"Write a FastAPI endpoint with Pydantic models, error handling, auth dependency.",
    "sql_query":       "Write an optimized PostgreSQL query.",
    "github_action":   "Write a GitHub Actions workflow YAML.",
    "bash_script":     "Write a production Bash script with error handling and help text.",
}

def generate_code(description, code_type="python_function"):
    system = CODE_TYPES.get(code_type, "Write production code.")
    return claude(f"{system} Return ONLY the code, no explanations.", description, max_tokens=1200) or f"# TODO: implement {description}"

def generate_from_spec(spec):
    code_type = spec.get("type","python_function")
    desc = f"{spec.get('description','')}. Inputs: {spec.get('inputs',{})}. Outputs: {spec.get('outputs',{})}."
    return generate_code(desc, code_type)

def run():
    specs = [
        {"type":"python_function","description":"Calculate compound interest","inputs":{"principal":"float","rate":"float","years":"int"},"outputs":{"amount":"float"}},
        {"type":"react_component","description":"Product card with image, title, price, and buy button"},
        {"type":"sql_query","description":"Top 10 customers by order value in last 30 days"},
    ]
    for spec in specs:
        code = generate_from_spec(spec)
        log.info(f"Generated {spec['type']}: {len(code)} chars")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

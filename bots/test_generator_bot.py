#!/usr/bin/env python3
# Test Generator Bot - Auto-generates pytest, Jest, and API tests from code.
import os, sys, json, logging
sys.path.insert(0,".")
try:
    from agents.claude_core import claude
except:
    def claude(s,u,**k): return ""
log = logging.getLogger(__name__)

def pytest_tests(func_code, func_name):
    return claude(
        "Write comprehensive pytest tests. Include: happy path, edge cases, error cases, fixtures. Return only test code.",
        f"Function to test:
{func_code[:2000]}",
        max_tokens=800
    ) or f"import pytest

def test_{func_name}_happy_path():
    pass

def test_{func_name}_edge_case():
    pass

def test_{func_name}_error():
    pass
"

def jest_tests(component_name, description):
    return claude(
        "Write Jest/RTL tests. Include: renders, interactions, edge cases. Return only test code.",
        f"Component: {component_name}. Description: {description}",
        max_tokens=600
    ) or f"import {{render,screen}} from '@testing-library/react';
import {{{component_name}}} from './{component_name}';

describe('{component_name}', () => {{
  it('renders correctly', () => {{
    render(<{component_name}/>);
  }});
}});
"

def api_tests(endpoint, method="GET"):
    path = endpoint.strip("/").replace("/","_")
    return f"import pytest
import httpx

BASE = 'http://localhost:8000'

def test_{method.lower()}_{path}():
    r = httpx.{method.lower()}(f'{{BASE}}{endpoint}',headers={{'Authorization':'Bearer test'}})
    assert r.status_code == 200

def test_{method.lower()}_{path}_unauthorized():
    r = httpx.{method.lower()}(f'{{BASE}}{endpoint}')
    assert r.status_code == 401
"

def run():
    test_code = "def add(a, b):
    return a + b"
    tests = pytest_tests(test_code, "add")
    log.info(f"Generated pytest: {len(tests)} chars")
    api_t = api_tests("/contacts", "GET")
    log.info(f"Generated API tests: {len(api_t)} chars")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

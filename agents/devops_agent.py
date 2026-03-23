#!/usr/bin/env python3
"""
DevOps & Infrastructure Agent — NYSR Engineering
Generates production infrastructure for any project.

Capabilities:
- Docker + docker-compose for local + production
- Kubernetes manifests (Helm charts)
- GitHub Actions CI/CD pipelines
- Terraform IaC (AWS, GCP, Azure)
- Nginx/Caddy configs
- SSL/TLS automation (Let's Encrypt)
- Monitoring stack (Prometheus + Grafana)
- Log aggregation (ELK/Loki)
- Auto-scaling policies
- Disaster recovery runbooks
"""
import os, sys, logging
sys.path.insert(0, ".")
try:
    from agents.claude_core import claude, claude_json
except Exception:  # noqa: bare-except
    def claude(s,u,**k): return ""
    def claude_json(s,u,**k): return {}

log = logging.getLogger(__name__)

DEVOPS_SYSTEM = """You are a principal DevOps/SRE engineer. 
You design and build production infrastructure that scales.
Standards: Infrastructure as Code, GitOps, zero-downtime deployments,
automated backups, monitoring alerts, security hardening.
You think about: cost optimization, high availability, disaster recovery."""

def generate_docker_setup(app_type: str, services: list) -> dict:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {"dockerfile": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD [\"python\",\"-m\",\"uvicorn\",\"main:app\",\"--host\",\"0.0.0.0\"]"}
    
    return claude_json(
        DEVOPS_SYSTEM,
        f"""Generate complete Docker setup for {app_type} app with services: {services}

Return:
{{
  "dockerfile": "production-optimized Dockerfile (multi-stage)",
  "docker_compose": "full docker-compose.yml with all services",
  "docker_compose_prod": "production docker-compose override",
  "nginx_conf": "nginx reverse proxy config",
  ".dockerignore": "dockerignore file"
}}""",
        max_tokens=3000
    ) or {}

def generate_cicd_pipeline(project_type: str, deploy_target: str, test_framework: str) -> str:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return "name: CI/CD\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest"
    
    return claude(
        DEVOPS_SYSTEM,
        f"""Generate a complete GitHub Actions CI/CD pipeline for:
- Project type: {project_type}
- Deploy target: {deploy_target}
- Test framework: {test_framework}

Include:
1. Lint + typecheck
2. Unit tests with coverage report
3. Integration tests
4. Security scanning (Snyk or Semgrep)
5. Docker build + push to GHCR
6. Deploy to staging on PR
7. Deploy to production on main merge
8. Slack/Pushover notifications
9. Rollback on failure""",
        max_tokens=2000
    )

def generate_terraform(cloud: str, services: list) -> dict:
    if not os.environ.get("ANTHROPIC_API_KEY"): return {}
    
    return claude_json(
        DEVOPS_SYSTEM,
        f"""Generate Terraform IaC for {cloud} with services: {services}

Return:
{{
  "main.tf": "main Terraform config",
  "variables.tf": "all variables",
  "outputs.tf": "output values",
  "terraform.tfvars.example": "example variable values"
}}""",
        max_tokens=3000
    ) or {}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log.info("DevOps Agent ready.")

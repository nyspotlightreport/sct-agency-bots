#!/bin/bash
# deploy/setup_n8n_vps.sh
# Install n8n on VPS 204.48.29.16 as primary workflow orchestrator.
# Replaces GitHub Actions cold starts with instant always-warm execution.
# IMPORTANT: Run this on the VPS via SSH.
# -----------------------------------------------------------
set -e

echo "=== NYSR n8n VPS Setup ==="
echo "Replacing GitHub Actions cold starts with instant n8n orchestration"
echo ""

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

# Create n8n data directory
mkdir -p /opt/nysr/n8n
mkdir -p /opt/nysr/n8n/data

# Create docker-compose.yml
cat > /opt/nysr/n8n/docker-compose.yml << 'EOF'
version: "3"
services:
  n8n:
    image: n8nio/n8n:latest
    container_name: nysr-n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=nysr
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://204.48.29.16:5678/
      - GENERIC_TIMEZONE=America/New_York
      - NODE_ENV=production
      - N8N_METRICS=true
      # NYSR Secrets injected from environment
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - HUBSPOT_API_KEY=${HUBSPOT_API_KEY}
      - APOLLO_API_KEY=${APOLLO_API_KEY}
      - PUSHOVER_API_KEY=${PUSHOVER_API_KEY}
      - PUSHOVER_USER_KEY=${PUSHOVER_USER_KEY}
    volumes:
      - /opt/nysr/n8n/data:/home/node/.n8n
    networks:
      - nysr-net

networks:
  nysr-net:
    driver: bridge
EOF

echo "Starting n8n..."
cd /opt/nysr/n8n
docker-compose up -d

echo ""
echo "=== n8n SETUP COMPLETE ==="
echo "Access: http://204.48.29.16:5678"
echo "Username: nysr"
echo ""
echo "NEXT: Configure these webhooks in n8n:"
echo "  - HubSpot deal_stage_changed → immediate sequence trigger"
echo "  - Stripe payment_success → auto-onboarding (30 seconds)"
echo "  - Apollo new lead → score + enrich + sequence"
echo "  - GitHub workflow_failed → alert brain notification"
echo ""
echo "MIGRATION ORDER:"
echo "  1. Social scheduler → n8n (immediate win)"
echo "  2. sales_daily.yml → n8n (HubSpot node built-in)"
echo "  3. Customer health score → n8n (Supabase node, 5-min runs)"
echo "  4. cashflow_emergency.yml → n8n parallel (no concurrent limits)"
echo "  5. Keep GitHub Actions only for code deployment"

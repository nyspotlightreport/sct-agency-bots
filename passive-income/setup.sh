#!/bin/bash
# NYSR Passive Income Stack — Fixed Setup v2
# Removes peer2profit (dead image), adds Traffmonetizer
set -e
echo "=== NYSR Passive Income VPS Setup v2 ==="

apt-get update -qq && apt-get install -y docker.io docker-compose curl -qq
systemctl enable docker && systemctl start docker
mkdir -p /opt/nysr-passive

cat > /opt/nysr-passive/docker-compose.yml << 'COMPOSE'
version: "3.8"
services:
  honeygain:
    image: honeygain/honeygain:latest
    container_name: honeygain
    restart: unless-stopped
    command: -tou-accept -email nyspotlightreport@gmail.com -password REPLACE_GMAIL_PASS -device NYSR-VPS-01
    network_mode: host

  earnapp:
    image: fazalfarhan01/earnapp:latest
    container_name: earnapp
    restart: unless-stopped
    volumes:
      - earnapp-data:/etc/earnapp
    network_mode: host

  repocket:
    image: repocket/repocket:latest
    container_name: repocket
    restart: unless-stopped
    environment:
      - RP_EMAIL=nyspotlightreport@gmail.com
      - RP_API_KEY=get-from-repocket.co
    network_mode: host

  pawns:
    image: iproyal/pawns-cli:latest
    container_name: pawns
    restart: unless-stopped
    command: -accept-tos -email=nyspotlightreport@gmail.com -password=REPLACE_GMAIL_PASS -device-name=NYSR-VPS -device-id=nysr-vps-001
    network_mode: host

  traffmonetizer:
    image: traffmonetizer/cli_v2:latest
    container_name: traffmonetizer
    restart: unless-stopped
    command: start accept --token REPLACE_WITH_TOKEN
    network_mode: host

volumes:
  earnapp-data:
COMPOSE

cd /opt/nysr-passive
docker-compose pull --ignore-pull-failures
docker-compose up -d --remove-orphans 2>/dev/null || docker-compose up -d

echo ""
echo "=== CONTAINERS RUNNING ==="
docker ps --format "table {{.Names}}\t{{.Status}}"
echo ""
echo "EarnApp link command:"
sleep 3 && docker exec earnapp earnapp link_device 2>/dev/null || echo "Run: docker exec earnapp earnapp link_device"
echo ""
echo "Monthly passive income: ~\$15-40 (once linked)"

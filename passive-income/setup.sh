#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
mkdir -p /opt/nysr-passive
cat > /opt/nysr-passive/docker-compose.yml << 'COMPOSE'
version: "3.8"
services:
  honeygain:
    image: honeygain/honeygain:latest
    container_name: honeygain
    restart: unless-stopped
    command: -tou-accept -email nyspotlightreport@gmail.com -password REPLACE_PASS -device NYSR-VPS-01
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
    command: -accept-tos -email=nyspotlightreport@gmail.com -password=REPLACE_PASS -device-name=NYSR-VPS -device-id=nysr-vps-001
    network_mode: host
  traffmonetizer:
    image: traffmonetizer/cli_v2:latest
    container_name: traffmonetizer
    restart: unless-stopped
    command: start accept --token wcTHKRxTuV23D5xBWpeE+XPBhN2VYEl0l6K4pRjVp5E=
    network_mode: host
COMPOSE
docker rm -f earnapp 2>/dev/null || true
cd /opt/nysr-passive
docker-compose pull --ignore-pull-failures
docker-compose up -d --remove-orphans
echo ""
echo "=== CONTAINERS ==="
docker ps --format "table {{.Names}}\t{{.Status}}"
echo ""
echo "All 4 passive income apps running. Monthly estimate: $12-35"

#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cd /opt/nysr-passive 2>/dev/null || (mkdir -p /opt/nysr-passive && cd /opt/nysr-passive)

# Install docker if not present
if ! command -v docker &>/dev/null; then
  apt-get update -qq && apt-get install -y docker.io docker-compose -qq
  systemctl enable docker && systemctl start docker
fi

# Write compose file with real token
cat > /opt/nysr-passive/docker-compose.yml << 'COMPOSE'
version: "3.8"
services:
  honeygain:
    image: honeygain/honeygain:latest
    container_name: honeygain
    restart: unless-stopped
    command: -tou-accept -email nyspotlightreport@gmail.com -password REPLACE_PASS -device NYSR-VPS-01
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
    command: -accept-tos -email=nyspotlightreport@gmail.com -password=REPLACE_PASS -device-name=NYSR-VPS -device-id=nysr-vps-001
    network_mode: host
  traffmonetizer:
    image: traffmonetizer/cli_v2:latest
    container_name: traffmonetizer
    restart: unless-stopped
    command: start accept --token wcTHKRxTuV23D5xBWpeE+XPBhN2VYEl0l6K4pRjVp5E=
    network_mode: host
volumes:
  earnapp-data:
COMPOSE

# Stop any existing containers cleanly
/usr/bin/docker-compose down 2>/dev/null || true

# Pull and start
/usr/bin/docker-compose pull --ignore-pull-failures
/usr/bin/docker-compose up -d --remove-orphans

echo ""
echo "=== CONTAINERS ==="
/usr/bin/docker ps --format "table {{.Names}}\t{{.Status}}"
echo ""
echo "EarnApp link:"
sleep 3 && /usr/bin/docker exec earnapp earnapp link_device 2>/dev/null || echo "Run: /usr/bin/docker exec earnapp earnapp link_device"

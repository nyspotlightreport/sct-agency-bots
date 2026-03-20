#!/bin/bash
# NYSR Passive Income Stack — Auto-Setup
# Run this in DigitalOcean console OR via SSH
set -e
echo "=== NYSR Passive Income VPS Setup ==="

# Install Docker
apt-get update -qq && apt-get install -y docker.io docker-compose curl -qq
systemctl enable docker && systemctl start docker

# Create config directory
mkdir -p /opt/nysr-passive

# Create docker-compose with all bandwidth apps
cat > /opt/nysr-passive/docker-compose.yml << 'COMPOSE'
version: "3.8"
services:
  honeygain:
    image: honeygain/honeygain:latest
    container_name: honeygain
    restart: unless-stopped
    command: -tou-accept -email nyspotlightreport@gmail.com -pass GMAIL_PASS -device NYSR-VPS-01
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

  peer2profit:
    image: peer2profit/peer2profit_linux:latest
    container_name: peer2profit
    restart: unless-stopped
    environment:
      - email=nyspotlightreport@gmail.com
    network_mode: host

  pawns:
    image: iproyal/pawns-cli:latest
    container_name: pawns
    restart: unless-stopped
    command: -accept-tos -email=nyspotlightreport@gmail.com -password=GMAIL_PASS -device-name=NYSR-VPS
    network_mode: host

volumes:
  earnapp-data:
COMPOSE

# Start all containers
cd /opt/nysr-passive && docker-compose up -d

echo ""
echo "=== SETUP COMPLETE ==="
docker-compose ps
echo ""
echo "EarnApp device link:"
sleep 5 && docker exec earnapp earnapp link_device 2>/dev/null || echo "(Run manually after startup)"
echo ""
echo "Monthly estimate: $15-45 passive income"
echo "All containers set to auto-restart on reboot"

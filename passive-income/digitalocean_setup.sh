#!/bin/bash
# DigitalOcean Passive Income VPS — NYSR Agency
# Run this ONCE after creating a $6/month Ubuntu droplet
# Installs: Honeygain, EarnApp, Grass (bandwidth sharing = $15-40/month passive)

set -e
echo "=== NYSR Passive Income VPS Setup ==="

# Install Docker
apt-get update -qq
apt-get install -y docker.io docker-compose curl wget -qq

# Create passive income compose file
cat > /opt/passive-income/docker-compose.yml << 'YAML'
version: "3"
services:
  honeygain:
    image: honeygain/honeygain:latest
    container_name: honeygain
    restart: always
    command: -tou-accept -email GMAIL_USER -pass GMAIL_PASS -device NYSR-VPS-01
    network_mode: host

  earnapp:
    image: fazalfarhan01/earnapp:latest
    container_name: earnapp
    restart: always
    volumes:
      - earnapp-data:/etc/earnapp
    network_mode: host

  repocket:
    image: repocket/repocket:latest
    container_name: repocket
    restart: always
    environment:
      - RP_EMAIL=GMAIL_USER
      - RP_API_KEY=REPOCKET_KEY
    network_mode: host

  peer2profit:
    image: peer2profit/peer2profit_linux:latest
    container_name: peer2profit
    restart: always
    environment:
      - email=GMAIL_USER
    network_mode: host

volumes:
  earnapp-data:
YAML

mkdir -p /opt/passive-income

# Replace placeholders
sed -i "s/GMAIL_USER/${GMAIL_USER}/g" /opt/passive-income/docker-compose.yml
sed -i "s/GMAIL_PASS/${GMAIL_PASS}/g" /opt/passive-income/docker-compose.yml
sed -i "s/REPOCKET_KEY/${REPOCKET_KEY}/g" /opt/passive-income/docker-compose.yml

# Launch
cd /opt/passive-income
docker-compose up -d

echo ""
echo "=== PASSIVE INCOME VPS LIVE ==="
docker-compose ps
echo ""
echo "📍 EarnApp: Run this to link device:"
docker exec earnapp earnapp link_device
echo ""
echo "💰 Expected monthly: \$15-40 passive, 24/7"

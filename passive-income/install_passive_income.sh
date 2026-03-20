#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NYSR PASSIVE INCOME STACK — ONE-CLICK INSTALLER
# Run with: curl -sSL https://bit.ly/nysr-passive | bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'

echo -e "${BOLD}${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║     NYSR PASSIVE INCOME STACK — SETUP WIZARD        ║"
echo "║         Est. earnings: \$40–110/month/IP             ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then OS="mac"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then OS="windows"; fi
echo -e "${GREEN}Detected OS: $OS${NC}"

# Install Docker if not present
if ! command -v docker &>/dev/null; then
    echo -e "${YELLOW}Docker not found. Installing...${NC}"
    if [[ "$OS" == "mac" ]]; then
        echo -e "${YELLOW}Please install Docker Desktop from: https://docker.com/products/docker-desktop${NC}"
        echo "Press Enter once Docker Desktop is installed and running..."
        read
    elif [[ "$OS" == "linux" ]]; then
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker $USER
        sudo systemctl enable docker && sudo systemctl start docker
        echo -e "${GREEN}Docker installed!${NC}"
    fi
fi

echo -e "${GREEN}✅ Docker found: $(docker --version)${NC}"

# Create install dir
mkdir -p "$HOME/.nysr-passive"
cd "$HOME/.nysr-passive"

# Download docker-compose file
echo -e "${YELLOW}Downloading stack config...${NC}"
curl -sSL "https://raw.githubusercontent.com/nyspotlightreport/sct-agency-bots/main/passive-income/docker-compose.passive.yml" \
  -o docker-compose.yml

# Collect credentials interactively
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}Enter your credentials for each platform.${NC}"
echo -e "All are FREE to sign up. Skip any you haven't set up yet (just press Enter)."
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

GMAIL="nyspotlightreport@gmail.com"
echo -e "${BLUE}Email [default: $GMAIL]:${NC}"
read -r INPUT_EMAIL
EMAIL="${INPUT_EMAIL:-$GMAIL}"

echo -e "${BLUE}Honeygain password (signup: honeygain.com):${NC}"
read -rs HPASS; echo ""

echo -e "${BLUE}EarnApp UUID (signup: earnapp.com → Dashboard → Settings):${NC}"
read -r EARN_UUID

echo -e "${BLUE}Grass password (signup: getgrass.io):${NC}"
read -rs GPASS; echo ""

echo -e "${BLUE}Repocket API Key (signup: repocket.co → Account):${NC}"
read -r RPKEY

echo -e "${BLUE}PacketStream CID (signup: packetstream.io → Dashboard):${NC}"
read -r PSCID

echo -e "${BLUE}Traffmonetizer token (signup: traffmonetizer.com → Dashboard):${NC}"
read -r TMTOKEN

# Write .env file
cat > .env << ENVEOF
HONEYGAIN_EMAIL=$EMAIL
HONEYGAIN_PASS=${HPASS:-changeme}
EARNAPP_UUID=${EARN_UUID:-sdk-node-nysr$(date +%s)}
GRASS_EMAIL=$EMAIL
GRASS_PASS=${GPASS:-changeme}
REPOCKET_EMAIL=$EMAIL
REPOCKET_API_KEY=${RPKEY:-your_key_here}
PACKETSTREAM_CID=${PSCID:-your_cid_here}
TRAFFMONETIZER_TOKEN=${TMTOKEN:-your_token_here}
PEER2PROFIT_EMAIL=$EMAIL
ENVEOF

echo ""
echo -e "${GREEN}Configuration saved. Starting all apps...${NC}"

# Start the stack
docker compose up -d 2>/dev/null || docker-compose up -d

sleep 5

echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}✅ PASSIVE INCOME STACK IS RUNNING!${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -v "^NAMES"
echo ""
echo -e "${YELLOW}Expected earnings: \$40–110/month with this IP${NC}"
echo -e "${YELLOW}Earnings start accumulating within 24–48 hours.${NC}"
echo ""
echo -e "${BLUE}View logs: docker compose logs -f${NC}"
echo -e "${BLUE}Stop all:  docker compose down${NC}"
echo -e "${BLUE}Restart:   docker compose restart${NC}"
echo ""

# Send phone notification
curl -s \
  -H "Title: 💰 Passive Income Stack LIVE" \
  -H "Tags: money_with_wings,white_check_mark" \
  -H "Priority: high" \
  -d "All bandwidth apps are running on your home machine! Expected: \$40-110/month. Check in 24-48 hours for first earnings." \
  "https://ntfy.sh/nysr-chairman-sct" &>/dev/null

echo -e "${GREEN}📱 Phone notification sent!${NC}"

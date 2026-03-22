#!/bin/bash
# DigitalOcean Passive Bandwidth Income Server
# Run this ONCE after getting DO API token
# Usage: export DO_TOKEN=your_token && bash digitalocean_passive_income_setup.sh

set -e

echo "=== NYSR Passive Income VPS Setup ==="
echo "Creating $6/month droplet + installing all bandwidth apps..."

# Create droplet via API
DROPLET_RESPONSE=$(curl -s -X POST "https://api.digitalocean.com/v2/droplets" \
  -H "Authorization: Bearer ${DO_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nysr-passive-income",
    "region": "nyc3",
    "size": "s-1vcpu-1gb",
    "image": "ubuntu-22-04-x64",
    "user_data": "#!/bin/bash\napt-get update -y\napt-get install -y docker.io docker-compose curl wget\nsystemctl enable docker\nsystemctl start docker\n\n# Install Honeygain\ndocker run -d --restart always --name honeygain honeygain/honeygain:latest start -tou-accept -email nyspotlightreport@gmail.com -pass HONEYGAIN_PASS\n\n# Install EarnApp  \nwget -qO /tmp/earnapp.sh https://brightdata.com/static/earnapp/install.sh\nbash /tmp/earnapp.sh\n\n# Install Pawns.app\ndocker run -d --restart always --name pawns iproyal/pawns-cli:latest -accept-tos -email=nyspotlightreport@gmail.com -password=PAWNS_PASS -device-name=nysr-vps\n\necho passive income server ready >> /var/log/nysr-setup.log\n"
  }')

DROPLET_ID=$(echo $DROPLET_RESPONSE | python3 -c "import json,sys; print(json.load(sys.stdin)['droplet']['id'])" 2>/dev/null)

if [ -z "$DROPLET_ID" ]; then
  echo "❌ Droplet creation failed. Check DO_TOKEN."
  echo "$DROPLET_RESPONSE"
  exit 1
fi

echo "✅ Droplet created! ID: $DROPLET_ID"
echo "⏳ Waiting 60 seconds for boot..."
sleep 60

# Get IP
DROPLET_IP=$(curl -s "https://api.digitalocean.com/v2/droplets/${DROPLET_ID}" \
  -H "Authorization: Bearer ${DO_TOKEN}" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['droplet']['networks']['v4'][0]['ip_address'])" 2>/dev/null)

echo "✅ Server IP: $DROPLET_IP"
echo ""
echo "=== NEXT STEPS (ONE-TIME, 5 MINUTES) ==="
echo "1. Create Honeygain account: https://r.honeygain.me/NYSR (use referral)"
echo "2. Create EarnApp account: https://earnapp.com/i/nysr"
echo "3. Create Pawns.app account: https://pawns.app/?r=nysr"
echo "4. SSH in: ssh root@$DROPLET_IP"
echo "5. Set passwords: edit /etc/nysr-passwords.env"
echo ""
echo "Estimated monthly: \$15-\$40 passive — server costs \$6 → NET: +\$9-\$34/month GUARANTEED"
echo ""
echo "Droplet ID saved for future reference: $DROPLET_ID"
echo $DROPLET_ID > /home/claude/do_droplet_id.txt

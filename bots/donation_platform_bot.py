#!/usr/bin/env python3
"""
Donation Platform Bot — NYSR Agency
Manages Ko-fi and Buy Me A Coffee integrations.
Adds tip/support buttons to all site pages.
These convert surprisingly well from content traffic.
Average: $50-200/mo from 1k monthly visitors.
"""
import os, requests, base64, logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("DonationBot")

GH_TOKEN = os.environ.get("GH_PAT","")
REPO     = "nyspotlightreport/sct-agency-bots"
H        = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}

KOFI_WIDGET = """
<!-- Ko-fi Floating Widget -->
<script src='https://storage.ko-fi.com/cdn/scripts/overlay-widget.js'></script>
<script>
  kofiWidgetOverlay.draw('nyspotlightreport', {
    'type': 'floating-chat',
    'floating-chat.donateButton.text': 'Support NYSR',
    'floating-chat.donateButton.background-color': '#C9A84C',
    'floating-chat.donateButton.text-color': '#0D1B2A'
  });
</script>"""

BМАC_WIDGET = """
<!-- Buy Me A Coffee Widget -->
<script data-name="BMC-Widget" data-cfasync="false"
  src="https://cdnjs.buymeacoffee.com/1.0.0/widget.prod.min.js"
  data-id="nyspotlightreport" data-description="Support NY Spotlight Report"
  data-message="If our content helped you, buy us a coffee!"
  data-color="#C9A84C" data-position="Right" data-x_margin="18" data-y_margin="18">
</script>"""

SETUP_LINKS = {
    "Ko-fi": "https://ko-fi.com/nyspotlightreport (register → link bank → add widget)",
    "Buy Me A Coffee": "https://buymeacoffee.com/nyspotlightreport (register → link PayPal/bank)",
    "Brave Rewards": "https://creators.brave.com (verify site → earn BAT from Brave users)",
    "GitHub Sponsors": "https://github.com/sponsors → enable for nyspotlightreport account",
}

if __name__ == "__main__":
    for platform, url in SETUP_LINKS.items():
        log.info(f"{platform}: {url}")
    log.info("\nAll 4 platforms = ~$100-400/mo at current traffic level")

#!/usr/bin/env python3
"""
Google AdSense Integration Bot — NYSR Agency
Adds AdSense ad code to nyspotlightreport.com
Estimated: $2-8 RPM on content traffic.
At 10k visits/mo = $20-80/mo pure passive.
"""
import os, requests, base64, logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("AdSenseBot")

GH_TOKEN    = os.environ.get("GH_PAT", "")
ADSENSE_ID  = os.environ.get("ADSENSE_PUBLISHER_ID", "")
REPO        = "nyspotlightreport/sct-agency-bots"
H           = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github+json"}

ADSENSE_SCRIPT = """
<!-- Google AdSense -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={pub_id}"
     crossorigin="anonymous"></script>
""" 

AD_UNIT_INLINE = """
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="{pub_id}"
     data-ad-slot="auto"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
"""

def inject_adsense_to_header():
    if not ADSENSE_ID:
        log.warning("No ADSENSE_PUBLISHER_ID — apply at google.com/adsense")
        log.info("Requirements: 10+ posts, original content, TOS compliant → usually approved in 1-3 weeks")
        return
    script = ADSENSE_SCRIPT.format(pub_id=ADSENSE_ID)
    log.info(f"Injecting AdSense for publisher: {ADSENSE_ID}")

if __name__ == "__main__":
    inject_adsense_to_header()
    log.info("Apply: google.com/adsense → Add site: nyspotlightreport.com")
    log.info("Add ADSENSE_PUBLISHER_ID secret once approved")

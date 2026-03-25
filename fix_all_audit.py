import os, re, glob
SITE_DIR = r"C:\Users\S\sct-agency-bots\site"
print("=== FIX 1: Removing 'free trial' from all HTML ===")
ft_total = 0
for html_file in glob.glob(os.path.join(SITE_DIR, "**", "*.html"), recursive=True):
    with open(html_file, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    new_content = re.sub(r'(?i)free[\s-]?trial', 'getting started', content)
    if content != new_content:
        count = len(re.findall(r'(?i)free[\s-]?trial', content))
        ft_total += count
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  FIXED: {html_file} ({count} instances)")
print(f"  Total removed: {ft_total}")

print("\n=== FIX 2: Creating Privacy Policy ===")
PRIVACY = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Privacy Policy - NY Spotlight Report</title><meta name="description" content="Privacy policy for NY Spotlight Report."><style>body{font-family:system-ui,sans-serif;max-width:800px;margin:0 auto;padding:2rem;line-height:1.7;color:#1a1a2e}h1{color:#16213e;border-bottom:3px solid #e94560;padding-bottom:.5rem}h2{color:#16213e;margin-top:2rem}a{color:#e94560}.footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #ddd;font-size:.85rem;color:#666}</style></head><body><h1>Privacy Policy</h1><p><strong>Effective:</strong> January 1, 2025 | <strong>Updated:</strong> March 25, 2026</p><p>NY Spotlight Report operates nyspotlightreport.com. This policy describes how we collect, use, and protect your personal information.</p><h2>Information We Collect</h2><p>We collect information you provide: name, email, business name, and payment info when subscribing. We also collect usage data through cookies and analytics including IP address, browser type, pages visited.</p><h2>How We Use Your Information</h2><p>We use your information to provide and improve services, process payments via Stripe, send emails via Resend, deliver content, respond to inquiries, and comply with legal obligations. We never sell your data.</p><h2>Data Storage</h2><p>Data stored securely using industry-standard encryption. Payments handled by Stripe (PCI-DSS compliant). Database via Supabase, hosting via Netlify.</p><h2>Third Parties</h2><p>We use: Stripe (payments), Resend (email), Supabase (database), Netlify (hosting), Twilio (voice), OpenAI and Anthropic (AI). Each has its own privacy policy.</p><h2>Your Rights</h2><p>Request access, correction, or deletion by emailing nyspotlightreport@gmail.com. California residents have CCPA rights. Response within 30 days.</p><h2>Children</h2><p>Services not directed to those under 18. We do not knowingly collect data from children.</p><h2>Contact</h2><p>NY Spotlight Report | nyspotlightreport@gmail.com | (631) 892-9817</p><div class="footer"><p>ISSN: 2026-0147 (Online) | Est. 2020 | &copy; 2026 NY Spotlight Report</p><p><a href="/">Home</a> | <a href="/terms/">Terms</a> | <a href="/editorial-standards/">Editorial Standards</a></p></div></body></html>'''
os.makedirs(os.path.join(SITE_DIR, "privacy"), exist_ok=True)
with open(os.path.join(SITE_DIR, "privacy", "index.html"), "w", encoding="utf-8") as f:
    f.write(PRIVACY)
print("  CREATED: Privacy Policy")

print("\n=== FIX 3: Creating Terms of Service ===")
TERMS = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Terms of Service - NY Spotlight Report</title><meta name="description" content="Terms of service for NY Spotlight Report."><style>body{font-family:system-ui,sans-serif;max-width:800px;margin:0 auto;padding:2rem;line-height:1.7;color:#1a1a2e}h1{color:#16213e;border-bottom:3px solid #e94560;padding-bottom:.5rem}h2{color:#16213e;margin-top:2rem}a{color:#e94560}.footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #ddd;font-size:.85rem;color:#666}</style></head><body><h1>Terms of Service</h1><p><strong>Effective:</strong> January 1, 2025 | <strong>Updated:</strong> March 25, 2026</p><p>By using nyspotlightreport.com, you agree to these terms.</p><h2>Services</h2><p>NY Spotlight Report provides entertainment news, business coverage, and the ProFlow AI content engine.</p><h2>Payments</h2><p>Subscriptions billed monthly via Stripe. No long-term contracts. Cancel anytime. High-ticket packages are one-time payments.</p><h2>Content Ownership</h2><p>Content generated for your business belongs to you. Original editorial content is copyrighted by NY Spotlight Report.</p><h2>Acceptable Use</h2><p>Do not use services for illegal activities, spam, IP infringement, or reputation harm.</p><h2>Liability</h2><p>Not liable for indirect damages. Total liability limited to amounts paid in preceding 12 months.</p><h2>Governing Law</h2><p>Governed by New York State law. Disputes resolved in Suffolk County courts.</p><h2>Contact</h2><p>NY Spotlight Report | nyspotlightreport@gmail.com | (631) 892-9817</p><div class="footer"><p>ISSN: 2026-0147 (Online) | Est. 2020 | &copy; 2026 NY Spotlight Report</p><p><a href="/">Home</a> | <a href="/privacy/">Privacy</a> | <a href="/editorial-standards/">Editorial Standards</a></p></div></body></html>'''
os.makedirs(os.path.join(SITE_DIR, "terms"), exist_ok=True)
with open(os.path.join(SITE_DIR, "terms", "index.html"), "w", encoding="utf-8") as f:
    f.write(TERMS)
print("  CREATED: Terms of Service")

print("\n=== FIX 4: Creating Editorial Standards ===")
EDITORIAL = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Editorial Standards - NY Spotlight Report</title><meta name="description" content="Editorial standards and ethics policy for NY Spotlight Report."><style>body{font-family:system-ui,sans-serif;max-width:800px;margin:0 auto;padding:2rem;line-height:1.7;color:#1a1a2e}h1{color:#16213e;border-bottom:3px solid #e94560;padding-bottom:.5rem}h2{color:#16213e;margin-top:2rem}a{color:#e94560}.footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #ddd;font-size:.85rem;color:#666}</style></head><body><h1>Editorial Standards</h1><p>NY Spotlight Report is committed to accurate, fair, and independent journalism.</p><h2>Accuracy</h2><p>We verify all claims through multiple sources. Corrections are issued promptly and transparently.</p><h2>Independence</h2><p>Editorial decisions are independent of advertising or business relationships. Our newsroom operates separately from commercial services.</p><h2>Sources</h2><p>We identify sources whenever possible. Anonymous sources used only when information is newsworthy and cannot be obtained on record.</p><h2>AI-Assisted Content</h2><p>AI-generated content is reviewed by human editors. AI-assisted content is labeled when it forms a substantial portion of an article.</p><h2>Corrections</h2><p>Published at top of original article with timestamp. We do not silently edit without notation.</p><h2>Conflicts of Interest</h2><p>Staff disclose potential conflicts. Writers do not cover entities in which they have financial interest.</p><h2>Contact</h2><p>Editor-in-Chief: S.C. Thomas | nyspotlightreport@gmail.com</p><div class="footer"><p>ISSN: 2026-0147 (Online) | Est. 2020 | &copy; 2026 NY Spotlight Report</p><p><a href="/">Home</a> | <a href="/privacy/">Privacy</a> | <a href="/terms/">Terms</a></p></div></body></html>'''
os.makedirs(os.path.join(SITE_DIR, "editorial-standards"), exist_ok=True)
with open(os.path.join(SITE_DIR, "editorial-standards", "index.html"), "w", encoding="utf-8") as f:
    f.write(EDITORIAL)
print("  CREATED: Editorial Standards")

print("\n=== FIX 5: Homepage ISSN + Founded 2020 + Alt Text ===")
hp_path = os.path.join(SITE_DIR, "index.html")
if os.path.exists(hp_path):
    with open(hp_path, "r", encoding="utf-8", errors="replace") as f:
        hp = f.read()
    changed = False
    if "2026-0147" not in hp:
        hp = hp.replace("</body>", '<div style="text-align:center;padding:1rem;font-size:0.8rem;color:#666">ISSN: 2026-0147 (Online) | Est. 2020 | NY Spotlight Report</div>\n</body>')
        changed = True
        print("  ADDED: ISSN + Founded 2020 to homepage")
    # Fix alt text
    import re as re2
    def add_alt(m):
        attrs = m.group(1); close = m.group(2)
        if 'alt=' not in attrs:
            src_m = re2.search(r'src=["\']([^"\']+)["\']', attrs)
            alt = os.path.splitext(os.path.basename(src_m.group(1)))[0].replace('-',' ').replace('_',' ').title() if src_m else "NY Spotlight Report"
            return f'<img{attrs} alt="{alt}"{close}>'
        return m.group(0)
    new_hp = re2.sub(r'<img([^>]*?)(/?)>', add_alt, hp)
    if hp != new_hp:
        changed = True
        print("  ADDED: Alt text to images")
    if changed:
        with open(hp_path, "w", encoding="utf-8") as f:
            f.write(new_hp)
print("\n=== ALL FIXES APPLIED ===")

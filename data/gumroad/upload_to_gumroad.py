#!/usr/bin/env python3
"""Upload product PDFs and descriptions to Gumroad via API."""
import os, json, time, urllib.request, urllib.parse

TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN", "iWDmua3jwn2oZDPa0nOUnvACE5lyeELc-uA3GwTxjmM")
BASE = "https://api.gumroad.com/v2"
PDF_DIR = os.path.join(os.path.dirname(__file__), "products")

# Load descriptions
with open(os.path.join(os.path.dirname(__file__), "descriptions.json")) as f:
    data = json.load(f)

products = data["products"]
print(f"Updating {len(products)} Gumroad products...")
print("=" * 60)

for p in products:
    pid = urllib.parse.quote(p["gumroad_id"], safe="")
    name = p["name"]

    # Build description HTML
    desc = f"{p['hook']}\n\nWhat you get:\n"
    for b in p["benefits"]:
        desc += f"- {b}\n"
    desc += f"\n{p['cta']}"

    # Step 1: Update product description
    update_data = urllib.parse.urlencode({
        "access_token": TOKEN,
        "description": desc,
        "published": "true"
    }).encode()

    try:
        req = urllib.request.Request(f"{BASE}/products/{pid}", data=update_data, method="PUT")
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        if result.get("success"):
            print(f"  [UPDATED] {name}")
        else:
            print(f"  [WARN] {name}: {result}")
    except Exception as e:
        print(f"  [ERROR] Update {name}: {e}")
        continue

    # Step 2: Upload PDF file
    pdf_path = os.path.join(PDF_DIR, p["pdf_file"])
    if not os.path.exists(pdf_path):
        print(f"  [SKIP] No PDF: {pdf_path}")
        continue

    # Multipart upload for file
    import io
    boundary = "----GumroadUploadBoundary2026"
    body = io.BytesIO()

    # access_token field
    body.write(f"--{boundary}\r\n".encode())
    body.write(f'Content-Disposition: form-data; name="access_token"\r\n\r\n'.encode())
    body.write(f"{TOKEN}\r\n".encode())

    # file field
    body.write(f"--{boundary}\r\n".encode())
    body.write(f'Content-Disposition: form-data; name="file"; filename="{p["pdf_file"]}"\r\n'.encode())
    body.write(f"Content-Type: application/pdf\r\n\r\n".encode())
    with open(pdf_path, "rb") as pf:
        body.write(pf.read())
    body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())

    try:
        req = urllib.request.Request(
            f"{BASE}/products/{pid}/product_files",
            data=body.getvalue(),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        if result.get("success"):
            print(f"  [UPLOADED] {p['pdf_file']}")
        else:
            print(f"  [WARN] Upload {name}: {result}")
    except Exception as e:
        print(f"  [ERROR] Upload {name}: {e}")

    time.sleep(1)  # Rate limit

print("=" * 60)
print("Done! All products updated on Gumroad.")

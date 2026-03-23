"""Generate 15 agency service pages from template + data."""
import json, os

DATA = "C:/Users/S/sct-agency-bots/data/agencies.json"
TEMPLATE = "C:/Users/S/sct-agency-bots/templates/agency-page.html"
OUTPUT_DIRS = [
    "C:/Users/S/NY-Spotlight-Report-good/services",
    "C:/Users/S/sct-agency-bots/site/services",
]

# Read the conversion engine for injection
CE_PATH = "C:/Users/S/NY-Spotlight-Report-good/includes/conversion-engine.html"

with open(DATA, "r", encoding="utf-8") as f:
    agencies = json.load(f)

with open(TEMPLATE, "r", encoding="utf-8") as f:
    template = f.read()

ce_html = ""
if os.path.exists(CE_PATH):
    with open(CE_PATH, "r", encoding="utf-8") as f:
        ce_html = f.read()

def build_deliverables_html(deliverables):
    rows = ""
    for d in deliverables:
        rows += f"""<tr>
<td style="font-weight:600;color:var(--ink)">{d['name']}</td>
<td style="text-align:center;color:var(--g500)">{d['lite']}</td>
<td style="text-align:center;color:var(--green);font-weight:600">{d['full']}</td>
</tr>\n"""
    return rows

def build_features_html(features, cls=""):
    return "\n".join(f'<li>{f}</li>' for f in features)

def build_faq_html(faq):
    items = ""
    for i, f in enumerate(faq):
        items += f"""<div class="faq-item" onclick="this.classList.toggle('open')">
<div class="faq-q">{f['q']}<span class="faq-arrow">+</span></div>
<div class="faq-a">{f['a']}</div>
</div>\n"""
    return items

def build_how_html(steps):
    return "\n".join(
        f'<div class="step-card"><div class="step-num">{s.get("step",i+1)}</div>'
        f'<h3>{s.get("title","")}</h3><p>{s.get("desc","")}</p></div>'
        for i, s in enumerate(steps)
    )

for agency in agencies:
    page = template
    page = page.replace("{{id}}", agency["id"])
    page = page.replace("{{name}}", agency["name"])
    page = page.replace("{{icon}}", agency["icon"])
    page = page.replace("{{tagline}}", agency["tagline"])
    page = page.replace("{{description}}", agency["description"])
    page = page.replace("{{litePrice}}", str(agency["litePrice"]))
    page = page.replace("{{fullPrice}}", str(agency["fullPrice"]))
    page = page.replace("{{dayPass}}", str(agency["dayPass"]))
    page = page.replace("{{replaceCost}}", agency["replaceCost"])
    page = page.replace("{{replaceLabel}}", agency["replaceLabel"])
    page = page.replace("{{traditionalCost}}", str(agency.get("traditionalCost", 3000)))
    page = page.replace("{{deliverables_html}}", build_deliverables_html(agency.get("deliverables", [])))
    page = page.replace("{{lite_features_html}}", build_features_html(agency.get("liteFeatures", [])))
    page = page.replace("{{full_features_html}}", build_features_html(agency.get("fullFeatures", [])))
    page = page.replace("{{faq_html}}", build_faq_html(agency.get("faq", [])))
    page = page.replace("{{how_it_works_html}}", build_how_html(agency.get("howItWorks", [
        {"step": 1, "title": "Onboard", "desc": "Share your requirements"},
        {"step": 2, "title": "We Deliver", "desc": "Our AI team executes"},
        {"step": 3, "title": "You Scale", "desc": "Focus on growth"},
    ])))
    page = page.replace("{{sample_output}}", agency.get("sampleOutput", ""))
    page = page.replace("{{savings_label}}", f"Save up to ${agency.get('traditionalCost', 3000) - agency['litePrice']}/mo vs {agency['replaceLabel'].lower()}")

    # Inject conversion engine
    if ce_html and "sticky-cta" not in page and "</body>" in page:
        page = page.replace("</body>", f"\n<!-- CONVERSION ENGINE -->\n{ce_html}\n</body>")

    for out_dir in OUTPUT_DIRS:
        slug_dir = os.path.join(out_dir, agency["id"])
        os.makedirs(slug_dir, exist_ok=True)
        out_path = os.path.join(slug_dir, "index.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)
        print(f"  {agency['id']}/index.html -> {out_dir}")

print(f"\nGenerated {len(agencies)} agency pages in {len(OUTPUT_DIRS)} directories")

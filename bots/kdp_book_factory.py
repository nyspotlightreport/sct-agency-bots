#!/usr/bin/env python3
"""
KDP Low-Content Book Factory
Generates puzzle books, planners, and journals ready for Amazon KDP
Uses Anthropic API to generate content + FPDF to create PDFs
Each book = ~$2-8/month passive royalty forever
"""
import os, json, random, logging
from datetime import datetime
try:
    from anthropic import Anthropic
    from fpdf import FPDF
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger("KDPFactory")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY","")

BOOK_TYPES = [
    {"type":"word_search","title":"Word Search for Adults — 100 Puzzles","category":"Activity","pages":120},
    {"type":"sudoku","title":"Sudoku Challenge — 200 Puzzles Easy to Hard","category":"Activity","pages":100},
    {"type":"journal","title":"Daily Gratitude Journal — 365 Days","category":"Journal","pages":180},
    {"type":"planner","title":"Undated Weekly Planner — Minimal Design","category":"Planner","pages":130},
    {"type":"coloring_book","title":"Mindful Patterns — 50 Coloring Pages for Adults","category":"Coloring","pages":60},
    {"type":"notebook","title":"Lined Notebook — 200 Pages Wide Ruled","category":"Notebook","pages":210},
    {"type":"budget","title":"Monthly Budget Planner — 12 Month Financial Tracker","category":"Finance","pages":130},
    {"type":"fitness","title":"90-Day Workout Log — Track Every Session","category":"Fitness","pages":100},
    {"type":"crossword","title":"Crossword Puzzles for Adults — 50 Large Print Puzzles","category":"Activity","pages":110},
    {"type":"affirmation","title":"Daily Affirmations Journal — Positive Mindset Workbook","category":"Journal","pages":150},
]

def generate_book_content(book_type, title, client):
    prompt = f"""Generate a complete, publishable KDP low-content book interior outline for: "{title}"
    
Type: {book_type}
Requirements:
- Provide the exact page layouts and what should go on each type of page
- For journals/planners: provide 5 sample pages with prompts/structure
- For puzzle books: provide 3 sample puzzles
- Include a copyright page, introduction, and instructions page content
- Keep it professional and publication-ready
- Format as JSON with keys: intro, copyright, instructions, sample_pages (array)

Return ONLY valid JSON, no markdown."""
    
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role":"user","content":prompt}]
    )
    try:
        return json.loads(resp.content[0].text)
    except:
        return {"intro":resp.content[0].text[:500], "copyright":"© 2026 ProFlow Digital", "instructions":"","sample_pages":[]}

def create_pdf(book, content, output_path):
    if not HAS_DEPS:
        log.warning("fpdf2 not installed — saving as JSON spec instead")
        with open(output_path.replace('.pdf','.json'),'w') as f:
            json.dump({"book":book,"content":content},f,indent=2)
        return
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica","B",24)
    pdf.cell(0,60,"",ln=True)
    pdf.cell(0,15,book['title'][:50],ln=True,align='C')
    if len(book['title']) > 50:
        pdf.cell(0,15,book['title'][50:],ln=True,align='C')
    pdf.set_font("Helvetica","",12)
    pdf.cell(0,10,"ProFlow Digital",ln=True,align='C')
    pdf.cell(0,10,"proflowdigital.com",ln=True,align='C')
    # Copyright page
    pdf.add_page()
    pdf.set_font("Helvetica","",10)
    pdf.multi_cell(0,7,content.get('copyright','© 2026 ProFlow Digital. All rights reserved.'))
    pdf.ln(5)
    # Introduction  
    pdf.add_page()
    pdf.set_font("Helvetica","B",14)
    pdf.cell(0,12,"Introduction",ln=True)
    pdf.set_font("Helvetica","",11)
    intro = content.get('intro','Welcome to your new planner.')[:1000]
    pdf.multi_cell(0,7,intro)
    # Sample content pages
    for page in content.get('sample_pages',[]):
        pdf.add_page()
        pdf.set_font("Helvetica","B",12)
        pdf.cell(0,10,str(page)[:100],ln=True)
    pdf.output(output_path)

def run():
    if not ANTHROPIC_KEY:
        log.warning("ANTHROPIC_API_KEY not set — generating structure only")
    os.makedirs("data/kdp_books", exist_ok=True)
    client = Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY and HAS_DEPS else None
    
    for book in BOOK_TYPES[:3]:  # Generate 3 per run, 10 total across runs
        log.info(f"📚 Generating: {book['title']}")
        fname = book['title'].replace(' ','_').replace('—','')[:50]
        outpath = f"data/kdp_books/{fname}.pdf"
        if os.path.exists(outpath):
            log.info(f"  Already exists: {fname}")
            continue
        if client:
            content = generate_book_content(book['type'], book['title'], client)
        else:
            content = {"intro":f"Welcome to {book['title']}","copyright":"© 2026 ProFlow Digital","instructions":"","sample_pages":["Page template"]}
        create_pdf(book, content, outpath)
        # Save metadata
        meta = {**book, "created":datetime.now().isoformat(),
                "kdp_category":book['category'],"target_price_paperback":"$7.99","royalty_estimate":"$2.80/sale"}
        with open(f"data/kdp_books/{fname}.json","w") as f:
            json.dump(meta, f, indent=2)
        log.info(f"  ✅ Saved: {outpath}")
    log.info(f"✅ KDP Factory run complete")
    # Print upload instructions
    print("\n📋 KDP UPLOAD INSTRUCTIONS:")
    print("1. Go to kdp.amazon.com → Bookshelf → + Paperback")
    print("2. Upload each PDF from data/kdp_books/")
    print("3. Set price $6.99-$9.99 (paperback) / $2.99-$4.99 (Kindle)")
    print("4. Set royalty: 70% for Kindle, 60% for paperback")
    print("5. Keywords: use book type + 'for adults' + 'large print' + 'gift'")

if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""
KDP Book Factory — generates PDFs and commits to GitHub
Runs weekly. Saves PDFs to data/kdp_books/ in the repo.
"""
import os, sys, json, base64, requests
from pathlib import Path
from fpdf import FPDF

GH_TOKEN = os.environ.get("GH_PAT","") or os.environ.get("GITHUB_TOKEN","")
REPO = "nyspotlightreport/sct-agency-bots"
HDR  = {"Authorization": f"Bearer {GH_TOKEN}", "Content-Type": "application/json"}

BOOKS = [
    {"title":"90-Day Goal Planner","type":"planner","price":"$7.99"},
    {"title":"Daily Habit Tracker 30 Day Reset","type":"tracker","price":"$6.99"},
    {"title":"Monthly Budget Planner Finance Tracker","type":"budget","price":"$7.99"},
    {"title":"Weekly Meal Prep Planner","type":"meal","price":"$6.99"},
    {"title":"Business Plan Template Annual","type":"business","price":"$8.99"},
    {"title":"Fitness Workout Log 90 Days","type":"fitness","price":"$6.99"},
    {"title":"Word Search Puzzles 100 Puzzles","type":"puzzle","price":"$7.99"},
    {"title":"Gratitude Journal 365 Days","type":"journal","price":"$7.99"},
    {"title":"Password Keeper Log Book","type":"notebook","price":"$5.99"},
    {"title":"Sudoku Puzzles 200 Easy to Hard","type":"puzzle","price":"$7.99"},
]

def clean(text):
    return text.replace("\u2014","-").replace("\u2013","-").replace("\u2018","'").replace("\u2019","'")

def make_pdf(book):
    import random
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title page
    pdf.add_page()
    pdf.set_font("Helvetica","B",18)
    title = clean(book["title"])
    for word_chunk in [title[i:i+30] for i in range(0, len(title), 30)]:
        pdf.cell(0, 12, word_chunk, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica","",11)
    pdf.cell(0, 20, "", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "ProFlow Digital", new_x="LMARGIN", new_y="NEXT", align="C")
    
    # Copyright
    pdf.add_page()
    pdf.set_font("Helvetica","",10)
    pdf.multi_cell(0, 7, "Copyright 2026 ProFlow Digital. All rights reserved.")
    
    # Content pages
    btype = book["type"]
    if btype == "planner":
        for week in range(1, 14):
            pdf.add_page()
            pdf.set_font("Helvetica","B",12)
            pdf.cell(0, 10, f"Week {week}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica","",10)
            for day in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
                pdf.cell(0, 6, day + ":", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 8, "", new_x="LMARGIN", new_y="NEXT")
                pdf.line(pdf.get_x(), pdf.get_y()-4, pdf.get_x()+170, pdf.get_y()-4)
    elif btype in ("tracker","meal","fitness","business","notebook"):
        for n in range(1, 52):
            pdf.add_page()
            pdf.set_font("Helvetica","B",11)
            pdf.cell(0, 8, f"Entry {n}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica","",10)
            pdf.cell(0, 6, "Date: _______________", new_x="LMARGIN", new_y="NEXT")
            for _ in range(18):
                pdf.cell(0, 8, "", new_x="LMARGIN", new_y="NEXT")
                pdf.line(pdf.get_x(), pdf.get_y()-4, pdf.get_x()+170, pdf.get_y()-4)
    elif btype == "budget":
        for month in range(1, 13):
            pdf.add_page()
            pdf.set_font("Helvetica","B",12)
            pdf.cell(0, 10, f"Month {month} Budget", new_x="LMARGIN", new_y="NEXT")
            for cat in ["Income","Housing","Utilities","Food","Transport","Entertainment","Savings","Other"]:
                pdf.cell(90, 8, cat+":", border=1)
                pdf.cell(90, 8, "$", border=1, new_x="LMARGIN", new_y="NEXT")
    else:  # puzzle, journal
        for n in range(1, 21):
            pdf.add_page()
            pdf.set_font("Helvetica","B",12)
            pdf.cell(0, 10, f"Puzzle #{n}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica","",9)
            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            for row in range(15):
                line = " ".join(random.choice(letters) for _ in range(20))
                pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
    
    fname = clean(book["title"]).replace(" ","_").replace("/","")[:40] + ".pdf"
    out = Path("/tmp") / fname
    pdf.output(str(out))
    return out, fname

def push_to_github(local_path, fname):
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    apipath = f"data/kdp_books/{fname}"
    url = f"https://api.github.com/repos/{REPO}/contents/{apipath}"
    ex = requests.get(url, headers=HDR)
    sha = ex.json().get("sha","") if ex.ok else ""
    payload = {"message": f"Add KDP book: {fname}", "content": content}
    if sha: payload["sha"] = sha
    r = requests.put(url, headers=HDR, json=payload)
    return r.ok, r.status_code

def run():
    print("KDP Book Factory starting...")
    success = 0
    for book in BOOKS:
        try:
            print(f"  Generating: {book['title']}")
            pdf_path, fname = make_pdf(book)
            size = pdf_path.stat().st_size // 1024
            ok, code = push_to_github(pdf_path, fname)
            status = "pushed" if ok else f"push failed ({code})"
            print(f"  {'ok' if ok else 'fail'}: {fname} ({size}KB) — {status}")
            if ok: success += 1
        except Exception as e:
            print(f"  Error: {book['title']}: {e}")
    
    print(f"\nDone: {success}/{len(BOOKS)} books generated")
    return success

if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""
LinkedIn Carousel Generator
Converts NYSR articles into LinkedIn PDF carousels + captions.
LinkedIn carousels get 3-5x more organic reach than text posts.
"""
import os, re, json
from datetime import datetime

try:
    from fpdf import FPDF
except ImportError:
    import subprocess
    subprocess.run(['pip', 'install', 'fpdf2', '--break-system-packages', '-q'])
    from fpdf import FPDF


def sanitize(text):
    return ''.join(c if ord(c) < 128 else '?' for c in str(text))


def generate_carousel(slug, title, cat, points):
    pdf = FPDF(orientation='P', unit='mm', format=(150, 150))
    pdf.set_margins(12, 12, 12)

    # Slide 1: Cover
    pdf.add_page()
    pdf.set_fill_color(26, 26, 26)
    pdf.rect(0, 0, 150, 150, 'F')
    pdf.set_text_color(201, 168, 76)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_y(20)
    pdf.cell(0, 8, sanitize('NY SPOTLIGHT REPORT | ' + cat.upper()), align='C',
             new_x='LMARGIN', new_y='NEXT')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_y(45)
    words = title.split()
    lines, line = [], []
    for w in words:
        line.append(w)
        if len(' '.join(line)) > 28:
            lines.append(' '.join(line[:-1]))
            line = [w]
    if line:
        lines.append(' '.join(line))
    for ln in lines[:4]:
        pdf.cell(0, 9, sanitize(ln), align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_y(120)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, 'nyspotlightreport.com', align='C')

    # Slides 2-5: Key points
    for i, pt in enumerate(points[:4], 1):
        pdf.add_page()
        pdf.set_fill_color(250, 248, 243)
        pdf.rect(0, 0, 150, 150, 'F')
        pdf.set_fill_color(201, 168, 76)
        pdf.rect(0, 0, 4, 150, 'F')
        pdf.set_text_color(201, 168, 76)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_y(20)
        pdf.set_x(12)
        pdf.cell(0, 8, sanitize(str(i) + ' / ' + str(min(4, len(points)))),
                 new_x='LMARGIN', new_y='NEXT')
        pdf.set_text_color(26, 26, 26)
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_y(45)
        words2 = pt.split()
        lines2, line2 = [], []
        for w in words2:
            line2.append(w)
            if len(' '.join(line2)) > 26:
                lines2.append(' '.join(line2[:-1]))
                line2 = [w]
        if line2:
            lines2.append(' '.join(line2))
        for ln in lines2[:4]:
            pdf.set_x(12)
            pdf.cell(126, 9, sanitize(ln), new_x='LMARGIN', new_y='NEXT')

    # Final slide: CTA
    pdf.add_page()
    pdf.set_fill_color(26, 26, 26)
    pdf.rect(0, 0, 150, 150, 'F')
    pdf.set_text_color(201, 168, 76)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_y(50)
    pdf.cell(0, 10, 'Read the full story', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 8, sanitize('nyspotlightreport.com/blog/' + slug + '/'),
             align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_y(100)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(201, 168, 76)
    pdf.cell(0, 8, 'NY Spotlight Report', align='C')

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'linkedin', 'carousels')
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, slug + '.pdf')
    pdf.output(path)
    return path


def generate_caption(slug, title, cat):
    hooks = {
        'nightlife': "Where New Yorkers are actually going out this weekend:",
        'fashion': "What's happening in NYC fashion right now:",
        'lgbtq': "The NYC LGBTQIA+ scene you need to know about:",
        'entertainment': "The NYC entertainment story everyone's talking about:",
    }
    hook = hooks.get(cat.lower(), "NYC culture is moving fast. Here's what you need to know:")
    return (hook + "\n\n" + title + "\n\nFull coverage at nyspotlightreport.com\n\n"
            "#NYC #NewYork #NYSpotlightReport #NYCEntertainment")


def main():
    blog_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'NY-Spotlight-Report-good', 'blog')
    if not os.path.isdir(blog_dir):
        blog_dir = os.path.join(os.path.dirname(__file__), '..', 'site', 'blog')
    if not os.path.isdir(blog_dir):
        print("Blog directory not found")
        return

    articles = []
    for item in sorted(os.listdir(blog_dir)):
        if item == 'index.html':
            continue
        item_path = os.path.join(blog_dir, item)
        if os.path.isdir(item_path):
            html_path = os.path.join(item_path, 'index.html')
            slug = item
        elif item.endswith('.html'):
            html_path = item_path
            slug = item[:-5]
        else:
            continue
        if not os.path.exists(html_path):
            continue
        with open(html_path, 'r', errors='ignore') as f:
            c = f.read()
        title_m = re.search(r'<title>([^<]+)', c)
        title = title_m.group(1).split('\u2014')[0].strip() if title_m else slug.replace('-', ' ').title()
        cat_m = re.search(r'class="category[^"]*"[^>]*>([^<]+)', c)
        cat = cat_m.group(1).strip() if cat_m else 'Entertainment'
        h2s = re.findall(r'<h2[^>]*>([^<]+)', c)
        points = [re.sub(r'<[^>]+>', '', h).strip() for h in h2s[:4]]
        if not points:
            points = ['Key insight from this article', 'NYC coverage you need',
                      'Independent journalism since 2020', 'Read the full story']
        articles.append({'slug': slug, 'title': title, 'cat': cat, 'points': points})

    print("Processing %d articles for LinkedIn carousels" % len(articles))
    cap_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'linkedin', 'captions')
    os.makedirs(cap_dir, exist_ok=True)
    generated = 0
    for art in articles[:20]:
        try:
            generate_carousel(art['slug'], art['title'], art['cat'], art['points'])
            caption = generate_caption(art['slug'], art['title'], art['cat'])
            with open(os.path.join(cap_dir, art['slug'] + '.txt'), 'w') as f:
                f.write(caption)
            generated += 1
        except Exception as e:
            print("  Error %s: %s" % (art['slug'], e))
    print("LinkedIn carousels complete: %d generated" % generated)


if __name__ == '__main__':
    main()

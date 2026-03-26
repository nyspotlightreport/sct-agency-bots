#!/usr/bin/env python3
"""
LinkedIn Carousel Generator
Converts NYSR articles into LinkedIn PDF carousels + captions.
LinkedIn carousels get 3-5x more organic reach than text posts.
"""
import os
import re
import glob
from html.parser import HTMLParser

try:
    from fpdf import FPDF
except ImportError:
    import subprocess
    subprocess.run(['pip', 'install', 'fpdf2', '--break-system-packages', '-q'])
    from fpdf import FPDF


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BLOG_DIR = os.path.expanduser("~/NY-Spotlight-Report-good/blog")
OUTPUT_PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "linkedin", "carousels")
OUTPUT_CAP_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "linkedin", "captions")
SITE_URL = "https://nyspotlightreport.com/blog"
MAX_ARTICLES = 20

# Colors
DARK_BG = (26, 26, 26)
GOLD = (201, 168, 76)
WHITE = (255, 255, 255)
LIGHT_BG = (250, 248, 243)
INK = (17, 17, 17)

PAGE_W = 150  # mm
PAGE_H = 150  # mm


def sanitize(text):
    """Strip non-ASCII characters for fpdf2 compatibility."""
    return "".join(c if ord(c) < 128 else " " for c in str(text)).strip()


def strip_html_tags(text):
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text)


# ---------------------------------------------------------------------------
# HTML parsing helpers
# ---------------------------------------------------------------------------
class ArticleParser(HTMLParser):
    """Lightweight parser to extract title, category, and h2 headings."""

    def __init__(self):
        super().__init__()
        self._tag_stack = []
        self._capture = None
        self._buffer = ""
        self.title = ""
        self.category = ""
        self.h2s = []
        self._in_article_body = False
        self._in_more_section = False

    # -- enter tag --
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self._tag_stack.append(tag)

        if tag == "title":
            self._capture = "title"
            self._buffer = ""
        elif tag == "span" and "article-category" in attrs_dict.get("class", ""):
            self._capture = "category"
            self._buffer = ""
        elif "article-body" in attrs_dict.get("class", ""):
            self._in_article_body = True
        elif "more-section" in attrs_dict.get("class", ""):
            self._in_more_section = True
        elif tag == "h2" and self._in_article_body and not self._in_more_section:
            self._capture = "h2"
            self._buffer = ""

    # -- leave tag --
    def handle_endtag(self, tag):
        if self._tag_stack:
            self._tag_stack.pop()
        if self._capture == "title" and tag == "title":
            self.title = self._buffer.strip()
            self._capture = None
        elif self._capture == "category" and tag == "span":
            self.category = self._buffer.strip()
            self._capture = None
        elif self._capture == "h2" and tag == "h2":
            text = self._buffer.strip()
            if text and "More from" not in text:
                self.h2s.append(text)
            self._capture = None

    # -- text content --
    def handle_data(self, data):
        if self._capture:
            self._buffer += data


def parse_article(html_path):
    """Return dict with title, category, h2s, slug, url."""
    with open(html_path, "r", encoding="utf-8", errors="replace") as fh:
        html = fh.read()

    parser = ArticleParser()
    parser.feed(html)

    slug = os.path.basename(os.path.dirname(html_path))

    # Clean title: remove site suffix
    title = parser.title
    for sep in [" -- ", " — ", " - ", " | "]:
        if sep in title:
            title = title.split(sep)[0].strip()
            break

    return {
        "title": sanitize(title),
        "category": sanitize(parser.category) if parser.category else "Feature",
        "h2s": [sanitize(h) for h in parser.h2s],
        "slug": slug,
        "url": "%s/%s/" % (SITE_URL, slug),
    }


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------
def build_carousel(article):
    """Generate a 150x150mm PDF carousel for the given article dict."""
    pdf = FPDF(orientation="P", unit="mm", format=(PAGE_W, PAGE_H))
    pdf.set_auto_page_break(auto=False)

    title = article["title"]
    category = article["category"].upper()
    h2s = article["h2s"]
    url = article["url"]

    # ---- Slide 1: Cover ----
    pdf.add_page()
    pdf.set_fill_color(*DARK_BG)
    pdf.rect(0, 0, PAGE_W, PAGE_H, "F")

    # Gold top bar
    pdf.set_fill_color(*GOLD)
    pdf.rect(0, 0, PAGE_W, 4, "F")

    # Brand + Category
    pdf.set_text_color(*GOLD)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(15, 25)
    brand_line = "NY SPOTLIGHT REPORT  |  %s" % category
    pdf.cell(PAGE_W - 30, 8, sanitize(brand_line), align="L")

    # Decorative rule
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.5)
    pdf.line(15, 40, 60, 40)

    # Title
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(15, 48)
    pdf.multi_cell(PAGE_W - 30, 12, sanitize(title), align="L")

    # Bottom bar
    pdf.set_fill_color(*GOLD)
    pdf.rect(0, PAGE_H - 4, PAGE_W, 4, "F")

    # Swipe hint
    pdf.set_text_color(180, 180, 180)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(15, PAGE_H - 18)
    pdf.cell(PAGE_W - 30, 6, "Swipe for key insights  >>>", align="R")

    # ---- Slides 2-5: Key points from H2 tags ----
    # Distribute h2s across up to 4 slides, max 2 per slide
    points = h2s[:8]  # cap at 8 points
    if not points:
        points = ["Key Insights", "Analysis", "What It Means"]

    slides_content = []
    for i in range(0, len(points), 2):
        slides_content.append(points[i:i + 2])
    slides_content = slides_content[:4]  # max 4 content slides

    for slide_idx, slide_points in enumerate(slides_content):
        pdf.add_page()
        # Light background
        pdf.set_fill_color(*LIGHT_BG)
        pdf.rect(0, 0, PAGE_W, PAGE_H, "F")

        # Gold left border
        pdf.set_fill_color(*GOLD)
        pdf.rect(0, 0, 5, PAGE_H, "F")

        # Slide number
        pdf.set_text_color(*GOLD)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_xy(15, 12)
        slide_num = slide_idx + 1
        total_slides = len(slides_content) + 2  # cover + content + CTA
        pdf.cell(PAGE_W - 30, 6, "%d / %d" % (slide_num + 1, total_slides), align="R")

        # Category label
        pdf.set_font("Helvetica", "", 8)
        pdf.set_xy(15, 12)
        pdf.cell(50, 6, category)

        y_pos = 35
        for pt_idx, point in enumerate(slide_points):
            # Point number circle (simulated)
            pdf.set_fill_color(*GOLD)
            pdf.set_draw_color(*GOLD)
            circle_x = 20
            circle_y = y_pos + 3
            pdf.ellipse(circle_x - 4, circle_y - 4, 8, 8, "F")
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_xy(circle_x - 4, circle_y - 3.5)
            global_idx = slide_idx * 2 + pt_idx + 1
            pdf.cell(8, 7, str(global_idx), align="C")

            # Point text
            pdf.set_text_color(*INK)
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_xy(33, y_pos - 2)
            pdf.multi_cell(PAGE_W - 48, 9, sanitize(point), align="L")

            y_pos += 50

        # Bottom branding
        pdf.set_text_color(180, 180, 180)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_xy(15, PAGE_H - 14)
        pdf.cell(PAGE_W - 30, 5, "NY Spotlight Report", align="L")

    # ---- Final Slide: CTA ----
    pdf.add_page()
    pdf.set_fill_color(*DARK_BG)
    pdf.rect(0, 0, PAGE_W, PAGE_H, "F")

    # Gold top bar
    pdf.set_fill_color(*GOLD)
    pdf.rect(0, 0, PAGE_W, 4, "F")

    # CTA heading
    pdf.set_text_color(*GOLD)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(15, 30)
    pdf.cell(PAGE_W - 30, 8, "NY SPOTLIGHT REPORT", align="C")

    # Decorative rule
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.5)
    pdf.line(50, 44, 100, 44)

    # Main CTA text
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_xy(15, 52)
    pdf.multi_cell(PAGE_W - 30, 13, "Read the\nfull story", align="C")

    # URL
    pdf.set_text_color(*GOLD)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(15, 95)
    # Truncate long URLs for display
    display_url = url if len(url) < 60 else url[:57] + "..."
    pdf.cell(PAGE_W - 30, 6, sanitize(display_url), align="C")

    # Follow CTA
    pdf.set_text_color(180, 180, 180)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(15, 110)
    pdf.cell(PAGE_W - 30, 6, "Follow for more NYC insights", align="C")

    # Bottom bar
    pdf.set_fill_color(*GOLD)
    pdf.rect(0, PAGE_H - 4, PAGE_W, 4, "F")

    return pdf


# ---------------------------------------------------------------------------
# Caption generation
# ---------------------------------------------------------------------------
HASHTAG_MAP = {
    "entertainment": "#Broadway #Theater #NYCEntertainment #LiveTheater",
    "culture": "#NYCCulture #ArtScene #CulturalArts",
    "art": "#NYCArt #ArtWorld #GalleryScene #ContemporaryArt",
    "food": "#NYCFood #FoodScene #NYCRestaurants",
    "business": "#NYCBusiness #Entrepreneurship #StartupNYC",
    "technology": "#TechNYC #Innovation #DigitalTransformation",
    "real estate": "#NYCRealEstate #PropertyMarket #RealEstateInvesting",
    "comedy": "#NYCComedy #StandUpComedy #ComedyScene",
    "feature": "#NYCNews #NewYork #NYCLife",
    "digital strategy": "#DigitalStrategy #ContentMarketing #OnlineBusiness",
    "passive income": "#PassiveIncome #OnlineBusiness #SideHustle",
    "automation": "#Automation #AITools #WorkflowAutomation",
    "seo": "#SEO #SearchMarketing #DigitalMarketing",
    "email marketing": "#EmailMarketing #Newsletter #ContentStrategy",
}


def generate_caption(article):
    """Build a LinkedIn post caption with hashtags."""
    title = article["title"]
    category = article["category"]
    url = article["url"]
    h2s = article["h2s"][:3]

    # Build bullet points from H2s
    bullets = ""
    for h in h2s:
        bullets += "\n-> %s" % sanitize(h)

    cat_lower = category.lower()
    tags = HASHTAG_MAP.get(cat_lower, "#NYCNews #NewYork #NYCLife")
    base_tags = "#NYSpotlightReport #NYC #NewYorkCity"

    caption = (
        "%s\n"
        "\n"
        "Key takeaways:%s\n"
        "\n"
        "Read the full story:\n"
        "%s\n"
        "\n"
        "%s %s"
    ) % (sanitize(title), bullets, url, tags, base_tags)

    return caption


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("LinkedIn Carousel Generator - NY Spotlight Report")
    print("=" * 60)

    os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)
    os.makedirs(OUTPUT_CAP_DIR, exist_ok=True)

    # Discover articles
    pattern = os.path.join(BLOG_DIR, "*", "index.html")
    html_files = sorted(glob.glob(pattern))
    print("Found %d articles in %s" % (len(html_files), BLOG_DIR))

    if not html_files:
        print("ERROR: No articles found. Check BLOG_DIR path.")
        return

    articles = []
    for path in html_files[:MAX_ARTICLES]:
        try:
            art = parse_article(path)
            if art["title"]:
                articles.append(art)
        except Exception as exc:
            print("  WARN: Skipping %s -- %s" % (path, exc))

    print("Parsed %d articles for carousel generation\n" % len(articles))

    success = 0
    for idx, article in enumerate(articles):
        slug = article["slug"]

        try:
            # Generate PDF
            pdf = build_carousel(article)
            pdf_path = os.path.join(OUTPUT_PDF_DIR, "%s.pdf" % slug)
            pdf.output(pdf_path)

            # Generate caption
            caption = generate_caption(article)
            cap_path = os.path.join(OUTPUT_CAP_DIR, "%s.txt" % slug)
            with open(cap_path, "w", encoding="utf-8") as fh:
                fh.write(caption)

            success += 1

            if (idx + 1) % 5 == 0:
                print("[%d/%d] Progress -- last: %s" % (idx + 1, len(articles), slug))

        except Exception as exc:
            print("  ERROR on %s: %s" % (slug, exc))

    print("\n" + "=" * 60)
    print("DONE: %d / %d carousels generated" % (success, len(articles)))
    print("PDFs:     %s" % os.path.abspath(OUTPUT_PDF_DIR))
    print("Captions: %s" % os.path.abspath(OUTPUT_CAP_DIR))
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
agents/media_production/ad_factory.py — Ad Factory Agent
URL → Scrape → Script → Voice → Visuals → Video Ad → Deploy
Turns any product URL into a complete video ad in under 60 seconds.
Produces: hero shots, lifestyle shots, detail shots, voiceover, video.
"""
import os,sys,json,logging,hashlib,time
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..",".."))
log=logging.getLogger("ad_factory")

AD_TEMPLATES = {
    "problem_solution": {
        "structure": ["Hook: State the pain point (3s)","Problem: Show the frustration (5s)","Solution: Introduce product (5s)","Proof: Show results/testimonial (10s)","CTA: Clear next step (5s)"],
        "best_for": "SaaS, services, productivity tools"
    },
    "before_after": {
        "structure": ["Before: Show the messy reality (8s)","Transition: Dramatic reveal (3s)","After: Show transformed state (8s)","How: Brief explanation (6s)","CTA: Start now (5s)"],
        "best_for": "Transformation products, fitness, design"
    },
    "testimonial": {
        "structure": ["Hook: Surprising result quote (3s)","Context: Who they are (5s)","Story: Their journey (10s)","Result: Specific numbers (5s)","CTA: Join them (5s)"],
        "best_for": "B2B, courses, coaching"
    },
    "demo": {
        "structure": ["Hook: End result first (3s)","Feature 1: Show + explain (7s)","Feature 2: Show + explain (7s)","Feature 3: Show + explain (7s)","CTA: Try it free (5s)"],
        "best_for": "Software, apps, tools"
    },
}

def analyze_product(url):
    """Deep product analysis from URL for ad creation."""
    from agents.media_production.director import claude
    return claude("You are a senior advertising strategist. Analyze this product for ad creation. Return JSON with: product_name, tagline, price, key_benefits (3), target_audience, pain_points (3), brand_voice, unique_selling_proposition, competitor_comparison, recommended_ad_template.",
        f"Analyze this product URL for creating a video ad: {url}\nReturn structured JSON only.")

def create_ad_variants(product_url, templates=None, platforms=None):
    """Create multiple ad variants for A/B testing across platforms."""
    from agents.media_production.director import url_to_video_ad, claude
    if templates is None: templates = ["problem_solution","demo"]
    if platforms is None: platforms = ["facebook","instagram","youtube","tiktok"]
    log.info(f"AD FACTORY: Creating {len(templates)}x{len(platforms)} variants for {product_url}")
    analysis = analyze_product(product_url)
    variants = []
    for template in templates:
        tmpl = AD_TEMPLATES.get(template, AD_TEMPLATES["problem_solution"])
        for platform in platforms:
            duration = {"facebook":15,"instagram":30,"youtube":30,"tiktok":15,"linkedin":30}.get(platform, 30)
            aspect = {"facebook":"1:1","instagram":"9:16","youtube":"16:9","tiktok":"9:16","linkedin":"16:9"}.get(platform, "16:9")
            script = claude(f"Write a {duration}s {template} ad script for {platform}. Aspect ratio: {aspect}. Structure: {tmpl['structure']}",
                f"Product analysis: {analysis}\nPlatform: {platform}\nTemplate: {template}")
            variants.append({"template":template,"platform":platform,"duration":duration,"aspect":aspect,"script":script})
            log.info(f"  Variant: {template}/{platform} ({duration}s)")
    return {"product_url":product_url,"analysis":analysis,"variants":variants,"total":len(variants)}

def batch_produce_ads(product_urls, template="problem_solution"):
    """Batch produce ads for multiple products."""
    results = []
    for url in product_urls:
        log.info(f"\nBATCH: Processing {url}")
        from agents.media_production.director import url_to_video_ad
        result = url_to_video_ad(url, 30, "commercial")
        results.append(result)
    return results

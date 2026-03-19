#!/usr/bin/env python3
"""
IMAGE GENERATOR BOT v2.0 — S.C. Thomas Internal Agency
Generates social media images using OpenAI GPT Image 1 (successor to DALL-E 3).
Auto-generates platform-specific visuals for content, uploads to Publer,
and returns media IDs ready for posting.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agency_core import BaseBot, Config, with_retry

class ImageGeneratorBot(BaseBot):
    VERSION = "2.0.0"
    OPENAI_URL = "https://api.openai.com/v1/images/generations"
    PUBLER_URL = "https://app.publer.com/api/v1"

    PLATFORM_SPECS = {
        "twitter":    {"size": "1792x1024", "style": "vivid", "label": "Twitter/X header image"},
        "linkedin":   {"size": "1792x1024", "style": "natural", "label": "LinkedIn professional image"},
        "instagram":  {"size": "1024x1024", "style": "vivid",  "label": "Instagram square post"},
        "facebook":   {"size": "1792x1024", "style": "natural", "label": "Facebook post image"},
        "tiktok":     {"size": "1024x1792", "style": "vivid",  "label": "TikTok vertical image"},
        "story":      {"size": "1024x1792", "style": "vivid",  "label": "Stories vertical image"},
        "default":    {"size": "1792x1024", "style": "natural", "label": "Social media image"},
    }

    BRAND_STYLE = os.getenv("IMAGE_BRAND_STYLE",
        "Clean, professional, modern aesthetic. Dark tones with sharp accents. "
        "No text overlays. High contrast. Premium feel. "
        "Manhattan executive visual style.")

    def __init__(self):
        super().__init__("image-generator", required_config=["OPENAI_API_KEY"])
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.publer_key = os.getenv("PUBLER_API_KEY", "")
        self.workspace  = os.getenv("PUBLER_WORKSPACE_ID", "")
        self.output_dir = Path("generated_images")
        self.output_dir.mkdir(exist_ok=True)

    @with_retry(max_retries=3, delay=3.0)
    def generate_image(self, prompt: str, platform: str = "default",
                       quality: str = "standard") -> dict:
        """Generate an image using OpenAI GPT Image 1"""
        spec = self.PLATFORM_SPECS.get(platform, self.PLATFORM_SPECS["default"])

        # Build enhanced prompt with brand style
        full_prompt = f"{prompt}. {self.BRAND_STYLE}. {spec['label']}."

        # Use gpt-image-1 (successor to dall-e-3)
        payload = json.dumps({
            "model":           "gpt-image-1",
            "prompt":          full_prompt,
            "n":               1,
            "size":            spec["size"],
            "response_format": "b64_json",
        }).encode()

        req = urllib.request.Request(
            self.OPENAI_URL,
            data=payload,
            headers={
                "Authorization":  f"Bearer {self.openai_key}",
                "Content-Type":   "application/json",
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())

        b64_data = data["data"][0]["b64_json"]
        img_bytes = base64.b64decode(b64_data)

        # Save locally
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = self.output_dir / f"{platform}_{timestamp}.png"
        filename.write_bytes(img_bytes)
        self.logger.info(f"Image saved: {filename}")

        return {
            "file":     str(filename),
            "b64":      b64_data,
            "platform": platform,
            "prompt":   full_prompt,
            "size":     spec["size"],
        }

    def generate_content_image(self, content_text: str, platform: str = "default") -> dict:
        """Generate an image that visually represents a piece of content"""
        # Ask Claude to write an image prompt from the content
        system = ("You write image generation prompts for social media content. "
                  "Given content text, write a vivid, specific visual prompt "
                  "that represents the concept. No text in image. Under 200 chars.")
        prompt = self.claude.complete_safe(
            system=system,
            user=f"Content: {content_text[:500]}\n\nWrite the image prompt:",
            max_tokens=200,
            fallback=f"Professional abstract visualization of: {content_text[:100]}"
        )
        return self.generate_image(prompt, platform)

    def generate_content_package(self, content_text: str) -> dict:
        """Generate platform-specific images for a content piece"""
        results = {}
        platforms = ["twitter", "linkedin", "instagram"]
        for platform in platforms:
            self.logger.info(f"Generating {platform} image...")
            try:
                results[platform] = self.generate_content_image(content_text, platform)
            except Exception as e:
                results[platform] = {"error": str(e)}
                self.logger.error(f"{platform} image failed: {e}")
        return results

    def execute(self) -> dict:
        """Process pending image generation requests from state"""
        pending = self.state.get("pending_image_requests", [])
        if not pending:
            self.logger.info("No pending image requests")
            return {"items_processed": 0}

        generated = 0
        for req in pending[:3]:
            try:
                result = self.generate_image(
                    prompt=req.get("prompt", "Abstract professional graphic"),
                    platform=req.get("platform", "default"),
                    quality=req.get("quality", "standard")
                )
                self.logger.info(f"Generated: {result['file']}")
                generated += 1
            except Exception as e:
                self.logger.error(f"Generation failed: {e}")

        self.state.set("pending_image_requests", pending[3:])
        return {"items_processed": generated}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--prompt",   type=str, help="Image generation prompt")
    p.add_argument("--content",  type=str, help="Content text to visualize")
    p.add_argument("--platform", type=str, default="default",
                   choices=list(ImageGeneratorBot.PLATFORM_SPECS.keys()))
    p.add_argument("--package",  action="store_true",
                   help="Generate full platform package from content")
    args = p.parse_args()

    bot = ImageGeneratorBot()

    if args.package and args.content:
        results = bot.generate_content_package(args.content)
        for platform, result in results.items():
            if "error" not in result:
                print(f"✅ {platform}: {result['file']}")
            else:
                print(f"❌ {platform}: {result['error']}")
    elif args.prompt:
        result = bot.generate_image(args.prompt, args.platform)
        print(f"✅ Generated: {result['file']}")
    elif args.content:
        result = bot.generate_content_image(args.content, args.platform)
        print(f"✅ Generated: {result['file']}")
    else:
        bot.run()

# SETUP:
# pip install requests openai
# export OPENAI_API_KEY=sk-...
# export PUBLER_API_KEY=...

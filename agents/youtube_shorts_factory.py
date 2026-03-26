#!/usr/bin/env python3
"""
YouTube Shorts Factory
Converts NYSR articles into 60-second scripts + optional ElevenLabs audio.
3 shorts/day from 93 articles = algorithm jet stream in 30 days.
"""
import os, re, json, time
from datetime import datetime

ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ELEVENLABS_KEY = os.environ.get('ELEVENLABS_API_KEY', '')
VOICE_ID = os.environ.get('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')


def generate_script(title, excerpt, cat):
    """Generate a 60-second YouTube Shorts script."""
    if ANTHROPIC_KEY:
        try:
            import requests
            r = requests.post('https://api.anthropic.com/v1/messages',
                headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01',
                         'content-type': 'application/json'},
                json={'model': 'claude-haiku-4-5-20251001', 'max_tokens': 300,
                      'messages': [{'role': 'user', 'content':
                          'Write a 60-second YouTube Shorts script for an NYC entertainment journalist. '
                          'Hook in first 3 words. 3 key facts. CTA: Follow NY Spotlight Report. '
                          'Max 150 words. Article: "%s" - %s' % (title, excerpt[:200])}]},
                timeout=15)
            if r.status_code == 200:
                return r.json()['content'][0]['text'].strip()
        except Exception:
            pass
    # Fallback template
    return ("NYC story alert. %s. Here's what you need to know. %s. "
            "Follow NY Spotlight Report for daily NYC coverage. "
            "Link in bio." % (title, excerpt[:150]))


def generate_audio(script, slug):
    """Generate ElevenLabs voiceover."""
    if not ELEVENLABS_KEY:
        return None
    try:
        import requests
        r = requests.post(
            'https://api.elevenlabs.io/v1/text-to-speech/%s' % VOICE_ID,
            headers={'xi-api-key': ELEVENLABS_KEY, 'Content-Type': 'application/json',
                     'Accept': 'audio/mpeg'},
            json={'text': script[:500], 'model_id': 'eleven_monolingual_v1',
                  'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}},
            timeout=30)
        if r.status_code == 200:
            audio_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'youtube', 'audio')
            os.makedirs(audio_dir, exist_ok=True)
            path = os.path.join(audio_dir, slug + '.mp3')
            with open(path, 'wb') as f:
                f.write(r.content)
            return path
    except Exception:
        pass
    return None


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
        desc_m = (re.search(r'og:description[^>]*content="([^"]+)"', c) or
                  re.search(r'name="description"[^>]*content="([^"]+)"', c))
        excerpt = desc_m.group(1)[:200] if desc_m else title
        cat_m = re.search(r'class="category[^"]*"[^>]*>([^<]+)', c)
        cat = cat_m.group(1).strip() if cat_m else 'Entertainment'
        articles.append({'slug': slug, 'title': title, 'excerpt': excerpt, 'cat': cat})

    batch = int(os.environ.get('YOUTUBE_BATCH_SIZE', '5'))
    print("Processing %d articles for YouTube Shorts" % min(batch, len(articles)))

    script_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'youtube', 'scripts')
    meta_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'youtube', 'metadata')
    os.makedirs(script_dir, exist_ok=True)
    os.makedirs(meta_dir, exist_ok=True)

    for art in articles[:batch]:
        print("  Processing: %s" % art['title'][:50])
        script = generate_script(art['title'], art['excerpt'], art['cat'])
        with open(os.path.join(script_dir, art['slug'] + '.txt'), 'w') as f:
            f.write(script)
        audio_path = generate_audio(script, art['slug'])
        meta = {
            'title': '%s | NY Spotlight Report' % art['title'][:95],
            'description': ('%s\n\nFull story: https://nyspotlightreport.com/blog/%s/\n\n'
                           '#NYC #NewYork #Entertainment #NYSpotlightReport' % (art['excerpt'][:200], art['slug'])),
            'tags': ['NYC', 'New York', 'Entertainment', 'NYSpotlightReport', art['cat']],
            'script': script,
            'audio': audio_path,
            'url': 'https://nyspotlightreport.com/blog/%s/' % art['slug'],
            'generated': datetime.now().isoformat(),
        }
        with open(os.path.join(meta_dir, art['slug'] + '.json'), 'w') as f:
            json.dump(meta, f, indent=2)
        print("    Script: %d chars | Audio: %s" % (len(script), "yes" if audio_path else "no key"))
        time.sleep(0.5)

    print("YouTube Shorts factory complete")


if __name__ == '__main__':
    main()

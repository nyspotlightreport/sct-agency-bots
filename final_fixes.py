import os, subprocess
REPO = r'C:\Users\S\sct-agency-bots'
os.chdir(REPO)
files_fixes = [
    ('bots/affiliate_engine.py', [('seanb041992+affiliates@gmail.com','nyspotlightreport+affiliates@gmail.com'),('seanb041992@gmail.com','nyspotlightreport@gmail.com')]),
    ('bots/email_monitor_bot.py', [('seanb041992+affiliates@gmail.com','nyspotlightreport+affiliates@gmail.com'),('seanb041992+sweep@gmail.com','nyspotlightreport+sweep@gmail.com'),('seanb041992@gmail.com','nyspotlightreport@gmail.com')]),
    ('bots/faceless_webinar_voice_bot.py', [('seanb041992','nyspotlightreport')]),
    ('bots/sweepstakes_auto_entry_bot.py', [('seanb041992+sweep@gmail.com','nyspotlightreport+sweep@gmail.com'),('seanb041992@gmail.com','nyspotlightreport@gmail.com')]),
    ('bots/webinar_video_generator.py', [('seanb041992','nyspotlightreport')]),
    ('bots/affiliate_direct_apply_bot.py', [('seanb041992@gmail.com','nyspotlightreport@gmail.com')]),
]
fixed = 0
for fpath, replacements in files_fixes:
    full = os.path.join(REPO, fpath)
    if not os.path.exists(full): print(f"SKIP {fpath}"); continue
    with open(full, 'r', encoding='utf-8', errors='ignore') as f: c = f.read()
    orig = c
    for old, new in replacements:
        c = c.replace(old, new)
    if c != orig:
        with open(full, 'w', encoding='utf-8') as f: f.write(c)
        fixed += 1; print(f"FIXED {fpath}")
    else:
        print(f"UNCHANGED {fpath}")
print(f"\nFixed {fixed} files")
subprocess.run(['git','add','-A'])
r = subprocess.run(['git','commit','-m','fix: all remaining email redirects'], capture_output=True, text=True)
print(r.stdout[:200] if r.stdout else r.stderr[:200])
r2 = subprocess.run(['git','push','origin','main'], capture_output=True, text=True)
print('PUSHED' if r2.returncode == 0 else r2.stderr[:200])

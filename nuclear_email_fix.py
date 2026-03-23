import os, subprocess
REPO = r'C:\Users\S\sct-agency-bots'
os.chdir(REPO)
SKIP = {'.git','node_modules','__pycache__','data','sweepstakes.db'}
EXTENSIONS = {'.py','.js','.yml','.yaml','.json','.md','.html','.ts','.sh','.bat','.ps1','.txt','.xml','.toml','.css'}
REPLACEMENTS = [
    ('nyspotlightreport+affiliates@gmail.com','nyspotlightreport+affiliates@gmail.com'),
    ('nyspotlightreport+sweep@gmail.com','nyspotlightreport+sweep@gmail.com'),
    ('nyspotlightreport@gmail.com','nyspotlightreport@gmail.com'),
    ('nyspotlightreport@gmail.com','nyspotlightreport@gmail.com'),
    ('nyspotlightreport@gmail.com','nyspotlightreport@gmail.com'),
    ('nyspotlightreport at gmail dot com','nyspotlightreport at gmail dot com'),
    ('nyspotlightreport','nyspotlightreport'),
]
fixed = 0; total = 0
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for fn in files:
        _, ext = os.path.splitext(fn)
        if ext.lower() not in EXTENSIONS: continue
        fp = os.path.join(root, fn)
        try:
            c = open(fp,'r',encoding='utf-8',errors='ignore').read()
        except: continue
        if 'nyspotlightreport' not in c.lower(): continue
        total += 1
        orig = c
        for old, new in REPLACEMENTS:
            c = c.replace(old, new)
        if c != orig:
            open(fp,'w',encoding='utf-8').write(c)
            fixed += 1
        else:
            # If still has it, it's a case variant we missed
            rel = os.path.relpath(fp, REPO)
            print(f"  STUBBORN: {rel}")
print(f"\nFixed {fixed}/{total} files with old email references")
# Verify
remaining = 0
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for fn in files:
        fp = os.path.join(root, fn)
        try:
            c = open(fp,'r',encoding='utf-8',errors='ignore').read()
            if 'nyspotlightreport' in c.lower():
                remaining += 1
        except: pass
print(f"Remaining references: {remaining}")
# Commit and push
subprocess.run(['git','add','-A'], capture_output=True)
r = subprocess.run(['git','commit','-m','nuclear: replace ALL nyspotlightreport references across entire codebase'], capture_output=True, text=True)
print(r.stdout[:200] if r.stdout else r.stderr[:200])
r2 = subprocess.run(['git','push','origin','main'], capture_output=True, text=True)
print('PUSHED' if r2.returncode == 0 else r2.stderr[:200])

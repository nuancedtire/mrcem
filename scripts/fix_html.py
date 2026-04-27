#!/usr/bin/env python3
"""
HTML quality fixes across all 1,124 notes.
1. Replace deprecated <CENTER>...</CENTER> with <div class="text-center">...</div>
2. Log notes with extremely short body content (< 200 chars of visible text).
"""
import json
import glob
import re
import os

BASE = '/home/user/mrcem/data'

def fix_center_tags(html: str) -> str:
    # Case-insensitive replacement of <CENTER> ... </CENTER>
    html = re.sub(r'<CENTER\b[^>]*>', '<div class="text-center">', html, flags=re.IGNORECASE)
    html = re.sub(r'</CENTER>', '</div>', html, flags=re.IGNORECASE)
    return html

def visible_text_length(html: str) -> int:
    """Rough count of visible characters (strip HTML tags)."""
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'&[a-z]+;', ' ', text)
    return len(text.strip())

files = sorted(glob.glob(f'{BASE}/**/*.json', recursive=True))

total = 0
changed = 0
short_notes = []

for fpath in files:
    with open(fpath) as f:
        data = json.load(f)

    if isinstance(data, list):
        continue

    html = data.get('body_html', '')
    if not isinstance(html, str):
        continue

    total += 1
    new_html = fix_center_tags(html)

    if new_html != html:
        data['body_html'] = new_html
        with open(fpath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        changed += 1

    # Check for suspiciously short notes
    vlen = visible_text_length(html)
    if vlen < 200:
        short_notes.append((vlen, data.get('title', '?'), fpath.split('/data/')[1]))

print(f'Processed {total} notes.')
print(f'Fixed CENTER tags in {changed} notes.')
print()
if short_notes:
    print(f'Short notes (< 200 visible chars): {len(short_notes)}')
    for vlen, title, path in sorted(short_notes):
        print(f'  {vlen:4d} chars | {title[:55]} | {path[:60]}')

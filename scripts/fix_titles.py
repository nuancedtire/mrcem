#!/usr/bin/env python3
"""Fix HTML <i> tags in note titles and strip from title field."""
import json, glob, re, os

BASE = '/home/user/mrcem/data'

# Notes with <i> tags in their title
TARGETS = [
    'microbiology/bacteriology/i-actinomyces-i-and-i-nocardia-i--2_2019.json',
    'microbiology/bacteriology/i-helicobacter-pylori-i--2_330.json',
    'microbiology/bacteriology/i-legionella-i--2_787.json',
    'microbiology/parasitology-and-stis/i-strongyloides-stercoralis-i--2_2039.json',
    'microbiology/parasitology-and-stis/i-trichomonas-vaginalis-i--2_1473.json',
    'pathology/cardiorespiratory-pathology/hiv-i-pneumocystis-jiroveci-i-pneumonia--2_316.json',
    'pathology/cardiorespiratory-pathology/i-mycoplasma-pneumoniae-i--2_602.json',
]

def strip_html(s):
    return re.sub(r'<[^>]+>', '', s).strip()

for rel_path in TARGETS:
    fpath = os.path.join(BASE, rel_path)
    with open(fpath) as f:
        data = json.load(f)
    old_title = data['title']
    data['title'] = strip_html(old_title)
    with open(fpath, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'Fixed: "{old_title}" → "{data["title"]}"')
    print(f'  File: {rel_path}')

print(f'\nFixed {len(TARGETS)} note titles.')

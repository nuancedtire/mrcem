#!/usr/bin/env python3
"""
Final round of miscategorisation fixes based on comprehensive audit.

Moves:
  1. Diabetes mellitus (type 2): diagnosis  haematology → GI & Endocrine
  2. Malaria                                 GI & Endocrine → Infectious Disease & Immunology
  3. Hypersensitivity reactions              GI & Endocrine → Infectious Disease & Immunology
  4. Normal immune response                  GI & Endocrine → Infectious Disease & Immunology
  5. Megaloblastic anaemia                   GI & Endocrine → Haematology & Oncology
  6. Mesenteric ischaemia                    Cardiorespiratory → GI & Endocrine
  7. Abdominal trauma: haemoperitoneaum      Cardiorespiratory → GI & Endocrine
  8. Splenic trauma                          Cardiorespiratory → GI & Endocrine
"""
import json, re, os, glob

BASE = '/home/user/mrcem/data'

SUBCAT_META = {
    'gi':    {'categorynum':'5','categoryname':'Pathology',
              'subcategorynum':'200','subcategoryname':'GI &amp; endocrine pathology'},
    'id':    {'categorynum':'5','categoryname':'Pathology',
              'subcategorynum':'500','subcategoryname':'Infectious disease &amp; immunology'},
    'haem':  {'categorynum':'5','categoryname':'Pathology',
              'subcategorynum':'7185','subcategoryname':'Haematology &amp; oncology'},
}

DEST_DIRS = {
    'gi':   f'{BASE}/pathology/gi-and-endocrine-pathology',
    'id':   f'{BASE}/pathology/infectious-disease-and-immunology',
    'haem': f'{BASE}/pathology/haematology-and-oncology',
}

def update_html_meta(html, meta):
    for field, value in meta.items():
        html = re.sub(rf'(<div id="{field}">)[^<]*(</div>)', rf'\g<1>{value}\g<2>', html)
    return html

def get_max_sort(d):
    sorts = [json.load(open(f)).get('sort_order', 0) for f in glob.glob(f'{d}/*.json')]
    return max(sorts) if sorts else 0

def move_note(nid, src_dir, dest_key):
    files = glob.glob(f'{src_dir}/*--{nid}.json')
    if not files:
        print(f'  MISSING {nid} in {src_dir.split("/data/")[1]}'); return
    src = files[0]
    with open(src) as f: data = json.load(f)
    dest_dir = DEST_DIRS[dest_key]
    data['body_html'] = update_html_meta(data['body_html'], SUBCAT_META[dest_key])
    data['sort_order'] = get_max_sort(dest_dir) + 1
    dst = os.path.join(dest_dir, os.path.basename(src))
    with open(dst, 'w') as f: json.dump(data, f, indent=2, ensure_ascii=False)
    os.remove(src)
    print(f'  [{dest_key}] {data["title"][:60]}')

HAEM = f'{BASE}/pathology/haematology-and-oncology'
GI   = f'{BASE}/pathology/gi-and-endocrine-pathology'
CARD = f'{BASE}/pathology/cardiorespiratory-pathology'

print('Moving misplaced pathology notes...')
move_note('2_624',  HAEM, 'gi')   # DM T2 diagnosis → GI & Endocrine
move_note('1_185',  GI,   'id')   # Malaria → Infectious Disease
move_note('1_141',  GI,   'id')   # Hypersensitivity reactions → Infectious Disease
move_note('1_2930', GI,   'id')   # Normal immune response → Infectious Disease
move_note('1_2916', GI,   'haem') # Megaloblastic anaemia → Haematology
move_note('2_1850', CARD, 'gi')   # Mesenteric ischaemia → GI
move_note('1_2469', CARD, 'gi')   # Abdominal trauma → GI
move_note('1_2448', CARD, 'gi')   # Splenic trauma → GI

print('\nResequencing affected subcategories...')

def resequence(dirpath):
    files = glob.glob(f'{dirpath}/*.json')
    notes = sorted([(json.load(open(f)).get('sort_order',0), f) for f in files])
    changed = 0
    for new_sort, (old_sort, fpath) in enumerate(notes, 1):
        if old_sort != new_sort:
            with open(fpath) as f: d = json.load(f)
            d['sort_order'] = new_sort
            with open(fpath, 'w') as f: json.dump(d, f, indent=2, ensure_ascii=False)
            changed += 1
    print(f'  {dirpath.split("/data/")[1]}: {len(notes)} notes, {changed} resequenced')

for d in [HAEM, GI, CARD,
          f'{BASE}/pathology/infectious-disease-and-immunology']:
    resequence(d)

print('\nDone.')

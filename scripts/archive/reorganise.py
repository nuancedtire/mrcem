#!/usr/bin/env python3
"""
MRCEM content reorganisation script.
Phases A & C: move miscategorised notes to correct subcategories.
Updates HTML metadata divs and sort_order in each JSON.
"""
import json
import re
import os
import shutil

BASE = '/home/user/mrcem/data'

def update_meta(html: str, updates: dict) -> str:
    """Replace metadata div values in HTML."""
    for field, value in updates.items():
        pattern = rf'(<div id="{field}">)[^<]*(</div>)'
        replacement = rf'\g<1>{value}\g<2>'
        html = re.sub(pattern, replacement, html)
    return html

def move_note(src_path: str, dst_dir: str, new_sort: int, meta_updates: dict, dry_run=False):
    """Read src JSON, update metadata, write to dst_dir, delete src."""
    with open(src_path) as f:
        data = json.load(f)

    data['body_html'] = update_meta(data['body_html'], meta_updates)
    data['sort_order'] = new_sort

    filename = os.path.basename(src_path)
    dst_path = os.path.join(dst_dir, filename)

    print(f"  MOVE: {src_path.split('/data/')[1]}")
    print(f"     → {dst_path.split('/data/')[1]}  (sort {new_sort})")

    if not dry_run:
        os.makedirs(dst_dir, exist_ok=True)
        with open(dst_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.remove(src_path)

def get_max_sort(dir_path: str) -> int:
    """Return the current maximum sort_order in a directory."""
    sorts = []
    for fname in os.listdir(dir_path):
        if fname.endswith('.json'):
            with open(os.path.join(dir_path, fname)) as f:
                d = json.load(f)
            sorts.append(d.get('sort_order', 0))
    return max(sorts) if sorts else 0


# ─────────────────────────────────────────────────────────────────────────────
# PHASE A — Fix miscategorised PATHOLOGY notes
# ─────────────────────────────────────────────────────────────────────────────

NEURO_DIR   = f'{BASE}/pathology/neurology-and-neurosurgery'
CARDIO_DIR  = f'{BASE}/pathology/cardiorespiratory-pathology'
INFECT_DIR  = f'{BASE}/pathology/infectious-disease-and-immunology'
HAEM_DIR    = f'{BASE}/pathology/haematology-and-oncology'

INFECT_META = {'subcategorynum': '500', 'subcategoryname': 'Infectious disease &amp; immunology'}
HAEM_META   = {'subcategorynum': '7185', 'subcategoryname': 'Haematology &amp; oncology'}
CARDIO_META = {'subcategorynum': '100',  'subcategoryname': 'Cardiorespiratory pathology'}

print("=" * 70)
print("PHASE A1: Pathology > Neurology → Infectious Disease & Immunology")
print("=" * 70)

# Neurology → Infectious Disease (6 notes)
neuro_to_infect = [
    'acute-phase-proteins--1_2932.json',
    'anaphylaxis--1_16.json',
    'enterobacteriaceae--1_82.json',
    'wound-healing--1_309.json',
    'wound-healing-fracture-healing--1_310.json',
    'wound-healing-special-sites--1_2925.json',
]
for fname in neuro_to_infect:
    src = os.path.join(NEURO_DIR, fname)
    new_sort = get_max_sort(INFECT_DIR) + 1
    move_note(src, INFECT_DIR, new_sort, INFECT_META)

print()
print("=" * 70)
print("PHASE A2: Pathology > Neurology → Cardiorespiratory Pathology")
print("=" * 70)

# Neurology → Cardiorespiratory (2 notes)
neuro_to_cardio = [
    'abdominal-trauma-haemoperitoneaum--1_2469.json',
    'splenic-trauma--1_2448.json',
]
for fname in neuro_to_cardio:
    src = os.path.join(NEURO_DIR, fname)
    new_sort = get_max_sort(CARDIO_DIR) + 1
    move_note(src, CARDIO_DIR, new_sort, CARDIO_META)

print()
print("=" * 70)
print("PHASE A3: Pathology > Cardiorespiratory → Infectious Disease & Immunology")
print("=" * 70)

# Cardiorespiratory → Infectious Disease (2 notes)
cardio_to_infect = [
    'immunoglobulins-antibodies--1_2929.json',
    'microbe-proliferation--1_196.json',
]
for fname in cardio_to_infect:
    src = os.path.join(CARDIO_DIR, fname)
    new_sort = get_max_sort(INFECT_DIR) + 1
    move_note(src, INFECT_DIR, new_sort, INFECT_META)

print()
print("=" * 70)
print("PHASE A4: Pathology > Cardiorespiratory → Haematology & Oncology")
print("=" * 70)

# Cardiorespiratory → Haematology (1 note)
src = os.path.join(CARDIO_DIR, 'thrombocytopenia--1_345.json')
new_sort = get_max_sort(HAEM_DIR) + 1
move_note(src, HAEM_DIR, new_sort, HAEM_META)

# ─────────────────────────────────────────────────────────────────────────────
# PHASE C — Fix miscategorised PHYSIOLOGY notes (Endocrine → elsewhere)
# ─────────────────────────────────────────────────────────────────────────────

ENDO_DIR  = f'{BASE}/physiology/endocrine-physiology'
RENAL_DIR = f'{BASE}/physiology/renal-physiology'
GI_DIR    = f'{BASE}/physiology/gi-physiology'

RENAL_META = {'subcategorynum': '5', 'subcategoryname': 'Renal physiology'}
GI_META    = {'subcategorynum': '4', 'subcategoryname': 'GI physiology'}
NEURO_PATHO_META = {
    'categorynum': '5',
    'categoryname': 'Pathology',
    'subcategorynum': '300',
    'subcategoryname': 'Neurology &amp; neurosurgery',
}

print()
print("=" * 70)
print("PHASE C1: Physiology > Endocrine → Renal Physiology (Hypernatraemia)")
print("=" * 70)

src = os.path.join(ENDO_DIR, 'hypernatraemia--2_217.json')
new_sort = get_max_sort(RENAL_DIR) + 1
move_note(src, RENAL_DIR, new_sort, RENAL_META)

print()
print("=" * 70)
print("PHASE C2: Physiology > Endocrine → GI Physiology (Biotin)")
print("=" * 70)

src = os.path.join(ENDO_DIR, 'biotin--2_2124.json')
new_sort = get_max_sort(GI_DIR) + 1
move_note(src, GI_DIR, new_sort, GI_META)

print()
print("=" * 70)
print("PHASE C3: Physiology > Endocrine → Pathology > Neurology (Child dev)")
print("=" * 70)

child_dev_files = [
    'child-development-gross-motor-milestones--2_2125.json',
    'child-development-fine-motor-and-vision-milestones--2_2126.json',
    'child-development-social-behavior-and-play-milestones--2_2127.json',
    'child-development-speech-and-hearing-milestones--2_2128.json',
]
for fname in child_dev_files:
    src = os.path.join(ENDO_DIR, fname)
    new_sort = get_max_sort(NEURO_DIR) + 1
    move_note(src, NEURO_DIR, new_sort, NEURO_PATHO_META)

print()
print("=" * 70)
print("PHASE C4: Merge Addison's Disease Summary into main note, then delete")
print("=" * 70)

summary_path = os.path.join(ENDO_DIR, 'addison-s-disease-summary--2_252.json')
main_path    = os.path.join(ENDO_DIR, 'addison-s-disease-and-adrenal-insufficiency--1_8.json')

with open(summary_path) as f:
    summary = json.load(f)
with open(main_path) as f:
    main = json.load(f)

# Extract just the content portion of the summary (before mybody marker)
summary_html = summary['body_html']
marker = '<div id="mybody">'
idx = summary_html.find(marker)
summary_content = summary_html[:idx].strip() if idx != -1 else summary_html

# Append summary as a collapsible section at the end of the main note's content
# (before the mybody marker in the main note)
main_html = main['body_html']
main_idx = main_html.find(marker)
if main_idx != -1:
    insert_block = (
        '\n\n<hr/>\n'
        '<div class="alert alert-info"><strong>Quick Summary</strong></div>\n'
        + summary_content
        + '\n'
    )
    main['body_html'] = main_html[:main_idx] + insert_block + main_html[main_idx:]
    with open(main_path, 'w') as f:
        json.dump(main, f, indent=2, ensure_ascii=False)
    print(f"  Appended summary content to: {main_path.split('/data/')[1]}")

os.remove(summary_path)
print(f"  Deleted: {summary_path.split('/data/')[1]}")

print()
print("=" * 70)
print("ALL MOVES COMPLETE")
print("=" * 70)

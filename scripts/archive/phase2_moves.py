#!/usr/bin/env python3
"""
Phase 2 note moves — fix remaining miscategorisation across all categories.

Moves performed:
  A. Cardiorespiratory → NEW Renal & Urological Pathology (subcategoryNum 150)
  B. Cardiorespiratory → Neurology & Neurosurgery (neurological notes)
  C. Cardiorespiratory → GI & Endocrine (metabolic/endocrine notes)
  D. Cardiorespiratory → Rheumatology, Dermatology & Women's Health
  E. Neurology → Cardiorespiratory (cardiac notes: AVB, WPW)
  F. Neurology → Infectious Disease & Immunology (inflammatory response)
"""
import json, re, os, glob, shutil

BASE = '/home/user/mrcem/data'

# ─── subcategory metadata by destination ────────────────────────────────────

SUBCAT_META = {
    # Pathology subcategories
    'renal':    {'categorynum': '5', 'categoryname': 'Pathology',
                 'subcategorynum': '150',
                 'subcategoryname': 'Renal &amp; urological pathology'},
    'neuro':    {'categorynum': '5', 'categoryname': 'Pathology',
                 'subcategorynum': '300',
                 'subcategoryname': 'Neurology &amp; neurosurgery'},
    'gi':       {'categorynum': '5', 'categoryname': 'Pathology',
                 'subcategorynum': '200',
                 'subcategoryname': 'GI &amp; endocrine pathology'},
    'rheum':    {'categorynum': '5', 'categoryname': 'Pathology',
                 'subcategorynum': '400',
                 'subcategoryname': 'Rheumatology, dermatology &amp; women\'s health'},
    'cardio':   {'categorynum': '5', 'categoryname': 'Pathology',
                 'subcategorynum': '100',
                 'subcategoryname': 'Cardiorespiratory pathology'},
    'id':       {'categorynum': '5', 'categoryname': 'Pathology',
                 'subcategorynum': '500',
                 'subcategoryname': 'Infectious disease &amp; immunology'},
}

DEST_DIRS = {
    'renal':  f'{BASE}/pathology/renal-and-urological-pathology',
    'neuro':  f'{BASE}/pathology/neurology-and-neurosurgery',
    'gi':     f'{BASE}/pathology/gi-and-endocrine-pathology',
    'rheum':  f'{BASE}/pathology/rheumatology-dermatology-and-women-s-health',
    'cardio': f'{BASE}/pathology/cardiorespiratory-pathology',
    'id':     f'{BASE}/pathology/infectious-disease-and-immunology',
}

def update_html_meta(html, meta):
    for field, value in meta.items():
        html = re.sub(
            rf'(<div id="{field}">)[^<]*(</div>)',
            rf'\g<1>{value}\g<2>',
            html
        )
    return html

def get_max_sort(dirpath):
    sorts = []
    for fpath in glob.glob(f'{dirpath}/*.json'):
        with open(fpath) as f:
            d = json.load(f)
        sorts.append(d.get('sort_order', 0))
    return max(sorts) if sorts else 0

def move_note(src_path, dest_key):
    dest_dir = DEST_DIRS[dest_key]
    meta = SUBCAT_META[dest_key]
    os.makedirs(dest_dir, exist_ok=True)
    with open(src_path) as f:
        data = json.load(f)
    data['body_html'] = update_html_meta(data['body_html'], meta)
    data['sort_order'] = get_max_sort(dest_dir) + 1
    dest_path = os.path.join(dest_dir, os.path.basename(src_path))
    with open(dest_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.remove(src_path)
    print(f'  [{dest_key}] {data["title"][:55]}')
    return dest_path

def find_note(nid, src_dir):
    """Find a note file by nid in a directory."""
    matches = glob.glob(f'{src_dir}/*--{nid}.json')
    if not matches:
        print(f'  WARNING: nid {nid} not found in {src_dir}')
        return None
    return matches[0]


CARDIO_DIR = f'{BASE}/pathology/cardiorespiratory-pathology'
NEURO_DIR  = f'{BASE}/pathology/neurology-and-neurosurgery'
ID_DIR     = f'{BASE}/pathology/infectious-disease-and-immunology'


# ─── A. Cardiorespiratory → Renal & Urological Pathology ────────────────────
print('='*65)
print('A. Cardiorespiratory → Renal & Urological Pathology')
print('='*65)

renal_nids = [
    '2_470',   # ADPKD
    '2_719',   # ADPKD: features
    '2_2443',  # AKI: a very basic introduction
    '2_1209',  # Drug-induced urinary retention
    '2_608',   # Fanconi syndrome
    '2_687',   # Focal segmental glomerulosclerosis
    '2_806',   # Goodpasture's syndrome
    '2_1538',  # Hepatorenal syndrome: management
    '2_221',   # IgA nephropathy
    '2_576',   # Liddle's syndrome
    '2_476',   # Membranous glomerulonephritis
    '2_650',   # Minimal change disease
    '2_377',   # Renal cell cancer
    '2_2171',  # Renal papillary necrosis
    '2_467',   # Renal stones: management
    '2_174',   # SLE: renal complications
    '2_1883',  # Scrotal problems
    '2_2178',  # Urinary casts
    '2_1568',  # Urinary incontinence
    '2_1720',  # UTI management
]
for nid in renal_nids:
    src = find_note(nid, CARDIO_DIR)
    if src:
        move_note(src, 'renal')

# ─── B. Cardiorespiratory → Neurology ───────────────────────────────────────
print()
print('='*65)
print('B. Cardiorespiratory → Neurology & Neurosurgery')
print('='*65)

neuro_nids_from_cardio = [
    '2_218',   # Horner's syndrome
    '2_406',   # Idiopathic intracranial hypertension
    '2_525',   # Intracranial venous thrombosis
    '2_424',   # Lambert-Eaton syndrome
    '2_724',   # Multiple system atrophy
    '2_679',   # Myotonic dystrophy
]
for nid in neuro_nids_from_cardio:
    src = find_note(nid, CARDIO_DIR)
    if src:
        move_note(src, 'neuro')

# ─── C. Cardiorespiratory → GI & Endocrine ──────────────────────────────────
print()
print('='*65)
print('C. Cardiorespiratory → GI & Endocrine Pathology')
print('='*65)

gi_nids_from_cardio = [
    '2_1124',  # Androgen insensitivity syndrome
    '2_2180',  # Alkaptonuria
    '2_2061',  # Vitamin B2 (riboflavin)
]
for nid in gi_nids_from_cardio:
    src = find_note(nid, CARDIO_DIR)
    if src:
        move_note(src, 'gi')

# ─── D. Cardiorespiratory → Rheumatology, Derm & Women's Health ─────────────
print()
print('='*65)
print('D. Cardiorespiratory → Rheumatology, Derm & Women\'s Health')
print('='*65)

rheum_nids_from_cardio = [
    '2_739',   # Isotretinoin
    '2_1501',  # Leukoplakia
]
for nid in rheum_nids_from_cardio:
    src = find_note(nid, CARDIO_DIR)
    if src:
        move_note(src, 'rheum')

# ─── E. Neurology → Cardiorespiratory (cardiac arrhythmias) ─────────────────
print()
print('='*65)
print('E. Neurology → Cardiorespiratory (cardiac notes)')
print('='*65)

cardio_nids_from_neuro = [
    '2_2021',  # Atrioventricular block
    '2_459',   # Wolff-Parkinson White
]
for nid in cardio_nids_from_neuro:
    src = find_note(nid, NEURO_DIR)
    if src:
        move_note(src, 'cardio')

# ─── F. Neurology → Infectious Disease (inflammatory response) ──────────────
print()
print('='*65)
print('F. Neurology → Infectious Disease & Immunology')
print('='*65)

id_nids_from_neuro = [
    '1_2927',  # Normal and abnormal inflammatory response
]
for nid in id_nids_from_neuro:
    src = find_note(nid, NEURO_DIR)
    if src:
        move_note(src, 'id')

print()
print('='*65)
print('ALL PHASE 2 MOVES COMPLETE')
print('='*65)

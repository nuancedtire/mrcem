#!/usr/bin/env python3
"""
Improved related_nids pass:
  1. Extended synonym groups covering drug classes, organisms, and anatomy regions
  2. Subcategory-neighbor fallback for notes that still have 0 keyword matches
     (adds up to 3 adjacent notes from the same subcategory)

Only writes to files where related_nids actually changes.
"""
import json, glob, re, os

BASE = '/home/user/mrcem/data'
MAX_RELATED = 5
FALLBACK_SAME_SUB = 3  # max same-subcat neighbors added via fallback

STOPWORDS = {
    'a','an','the','and','or','in','of','to','from','with','for','at','by',
    'as','on','is','are','was','were','has','have','had','be','been','being',
    'its','it','this','that','these','those','which','who','not','but','if',
    'basic','introduction','overview','summary','features','management',
    'causes','cause','investigation','investigations','diagnosis','treatment',
    'presentations','presentation','clinical','history','complications',
    'complication','classification','definition','aetiology','types','type',
    'pathophysiology','mechanism','action','adverse','effects','side','very',
    'criteria','syndrome','disease','disorder','condition','pathology',
    'versus','comparison','vs','assessment','approach','review','update',
    'acute','chronic','primary','secondary','general','common','rare',
    *[str(i) for i in range(10)],
}

SYNONYM_GROUPS = [
    # Organ systems — original
    ('renal', 'kidney', 'kidne', 'nephro', 'glomer'),
    ('cardiac', 'cardi',  'heart', 'myocar'),
    ('hepat',  'liver',  'biliar', 'cholang'),
    ('pulmo',  'lung',   'bronch', 'respir'),
    ('neuro',  'brain',  'crani',  'cereb', 'spinal'),
    ('gastro', 'bowel',  'intest', 'colon', 'duode', 'jejun', 'ileum'),
    ('diabet', 'insul',  'gluco',  'glycae'),
    ('thyro',  'thyroi'),
    ('adren',  'cortic', 'cushi',  'addis'),
    ('immune', 'immuno', 'antibo', 'antigen', 'lympho'),
    ('haemato', 'blood', 'anaem',  'haemog', 'erythr'),
    ('oncol',  'cancer', 'tumour', 'tumor',  'malig', 'carci', 'sarco'),
    ('infect', 'bacter', 'viral',  'virus',  'micro'),
    ('muscle', 'muscul', 'myopa'),
    ('bone',   'osteo'),
    ('skin',   'derm',   'cutane'),
    ('vascul', 'arteri', 'vein',   'venous'),
    ('thyroid', 'thyroi'),

    # Drug class → indication / reversal agent links (NEW)
    ('fluclox', 'staphy', 'meticil'),          # flucloxacillin ↔ staphylococci
    ('metronid', 'anaero', 'trichomonas'),      # metronidazole ↔ anaerobes/trich
    ('flumazen', 'benzo', 'diazep', 'lorazep'), # flumazenil ↔ benzodiazepines
    ('nalox', 'opioi', 'heroi', 'morph', 'opiat'), # naloxone ↔ opioids
    ('oseltam', 'influenz', 'tamif'),           # oseltamivir ↔ influenza
    ('mannitol', 'osmot', 'intracran', 'oedema'), # mannitol ↔ ICP/oedema
    ('inotrope', 'dobutam', 'adrenalin', 'noradrena'), # inotropes
    ('antiemeti', 'nausea', 'vomit', 'ondansetron'), # antiemetics

    # Organisms → diseases (NEW)
    ('legio', 'legione', 'atypic', 'pontia'),  # Legionella ↔ atypical pneumonia
    ('bordet', 'pertuss', 'whoopi'),            # Bordetella ↔ whooping cough
    ('salmonel', 'typhoi', 'enteric'),          # Salmonella ↔ typhoid/enteric
    ('campylob', 'gastroenter', 'diarrho'),     # Campylobacter ↔ GI infection
    ('neisseri', 'meningoc', 'gonoc'),          # Neisseria ↔ meningococcal/gonococcal
    ('influenz', 'parainflu', 'haemagglu'),     # influenza ↔ parainfluenza
    ('tuberculosis', 'mycobact', 'latent'),     # TB ↔ mycobacteria
    ('streptoc', 'pneumoc', 'rheumat'),         # Streptococcus ↔ pneumococcal/rheumatic

    # Anatomy region expansion (NEW)
    ('lumbricals', 'intrin', 'thenar', 'hypothen', 'palmar'), # hand intrinsics
    ('pelv', 'ovary', 'ovar', 'uterus', 'cervi', 'vulva'),   # female pelvis
    ('pelv', 'prostat', 'testi', 'epididym'),                  # male pelvis
    ('pleur', 'thorax', 'mediastin', 'diaphra'),               # thoracic structures
    ('scalp', 'cranial', 'skull', 'foramen', 'occipit'),       # head/skull
    ('nasal', 'sinus', 'pharynx', 'larynx', 'trachea'),       # upper airway
    ('masseter', 'temporalis', 'pterygoid', 'mastication'),    # muscles of mastication
    ('tongue', 'hypoglossl', 'lingual', 'glossal'),            # tongue/lingual
    ('pons', 'cerebel', 'brainstem', 'midbrain', 'medull'),   # brainstem

    # Additional clinical groupings (NEW)
    ('anaesth', 'sedati', 'analges', 'premed'),  # anaesthesia/sedation
    ('seizure', 'epilep', 'anticonvuls', 'status'), # epilepsy/seizures
    ('depress', 'antidepress', 'SSRI', 'TCA', 'tricycl'), # depression/antidepressants
    ('psychos', 'antipsychot', 'schizoph', 'haloper'),    # psychosis/antipsychotics
]

# Build synonym lookup: 5-char prefix → canonical (first in group)
SYNONYM_MAP = {}
for group in SYNONYM_GROUPS:
    canonical = group[0][:5]
    for token in group:
        stem = token[:5].lower()
        if stem not in SYNONYM_MAP:
            SYNONYM_MAP[stem] = canonical

PREFIX_LEN = 5

def get_keywords(title):
    title = re.sub(r'<[^>]+>', '', title)
    title = title.lower()
    title = re.sub(r"[''']s?\b", '', title)
    words = re.split(r'[^a-z]+', title)
    keywords = set()
    for word in words:
        if len(word) < 3 or word in STOPWORDS:
            continue
        stem = word[:PREFIX_LEN] if len(word) >= PREFIX_LEN else word
        stem = SYNONYM_MAP.get(stem, stem)
        if stem not in STOPWORDS:
            keywords.add(stem)
    return keywords

def get_title_prefix(title):
    title = re.sub(r'<[^>]+>', '', title).strip()
    m = re.match(r'^([^:(]+)', title)
    return m.group(1).strip().lower() if m else title.lower()


# ─── Load all notes ──────────────────────────────────────────────────────────
print('Loading notes...')
notes = []

for fpath in glob.glob(f'{BASE}/**/*.json', recursive=True):
    fname = os.path.basename(fpath)
    if fname.startswith('_'):
        continue
    with open(fpath) as f:
        raw = json.load(f)
    if isinstance(raw, list):
        continue
    nid = raw.get('nid', '')
    if not nid:
        continue
    html = raw.get('body_html', '')

    cat_m = re.search(r'<div id="categorynum">(\d+)</div>', html)
    sub_m = re.search(r'<div id="subcategorynum">(\d+)</div>', html)
    cat_num = int(cat_m.group(1)) if cat_m else 0
    sub_num = int(sub_m.group(1)) if sub_m else 0

    title = raw.get('title', '')
    keywords = get_keywords(title)
    title_prefix = get_title_prefix(title)

    notes.append({
        'nid': nid,
        'title': title,
        'keywords': keywords,
        'title_prefix': title_prefix,
        'cat': cat_num,
        'sub': sub_num,
        'sort': raw.get('sort_order', 0),
        'related_nids': raw.get('related_nids', []),
        'fpath': fpath,
    })

nid_to_note = {n['nid']: n for n in notes}
print(f'Loaded {len(notes)} notes.')

# ─── Build indexes ────────────────────────────────────────────────────────────
print('Building indexes...')
kw_index = {}
for note in notes:
    for kw in note['keywords']:
        kw_index.setdefault(kw, set()).add(note['nid'])

prefix_index = {}
for note in notes:
    if len(note['title_prefix']) >= 4:
        prefix_index.setdefault(note['title_prefix'], set()).add(note['nid'])

# Subcategory index for fallback: (cat, sub) → sorted list of nids by sort_order
subcat_index = {}
for note in notes:
    key = (note['cat'], note['sub'])
    subcat_index.setdefault(key, []).append((note['sort'], note['nid']))
for key in subcat_index:
    subcat_index[key].sort()

# ─── Score and select ────────────────────────────────────────────────────────
print('Computing related notes...')

def score_pair(a, b):
    if a['nid'] == b['nid']:
        return 0
    shared = a['keywords'] & b['keywords']
    if not shared:
        if (len(a['title_prefix']) >= 4 and a['title_prefix'] == b['title_prefix']):
            shared = {'__prefix__'}
        else:
            return 0

    score = len(shared)

    if a['cat'] != b['cat']:
        score *= 2.5
    elif a['sub'] != b['sub']:
        score *= 1.5

    if (len(a['title_prefix']) >= 4 and
            a['title_prefix'] == b['title_prefix'] and
            a['nid'] != b['nid']):
        score += 2

    return score

zero_before = sum(1 for n in notes if not n['related_nids'])

for note in notes:
    candidate_nids = set()
    for kw in note['keywords']:
        candidate_nids |= kw_index.get(kw, set())
    if len(note['title_prefix']) >= 4:
        candidate_nids |= prefix_index.get(note['title_prefix'], set())
    candidate_nids.discard(note['nid'])

    scored = []
    for cnid in candidate_nids:
        b = nid_to_note.get(cnid)
        if not b:
            continue
        s = score_pair(note, b)
        if s > 0:
            scored.append((s, cnid))

    scored.sort(key=lambda x: -x[0])

    chosen = []
    cross_cat = [(s, n) for s, n in scored if nid_to_note[n]['cat'] != note['cat']]
    same_cat_diff_sub = [(s, n) for s, n in scored
                         if nid_to_note[n]['cat'] == note['cat']
                         and nid_to_note[n]['sub'] != note['sub']]
    same_sub = [(s, n) for s, n in scored
                if nid_to_note[n]['sub'] == note['sub']
                and nid_to_note[n]['cat'] == note['cat']]

    for _, nid in cross_cat[:MAX_RELATED]:
        if len(chosen) >= MAX_RELATED:
            break
        chosen.append(nid)
    for _, nid in same_cat_diff_sub:
        if len(chosen) >= MAX_RELATED:
            break
        if nid not in chosen:
            chosen.append(nid)
    for _, nid in same_sub:
        if len(chosen) >= MAX_RELATED:
            break
        if nid not in chosen:
            chosen.append(nid)
        if nid_to_note[nid]['title_prefix'] != note['title_prefix']:
            break

    # ─── Subcategory-neighbor fallback ───────────────────────────────────────
    if not chosen:
        key = (note['cat'], note['sub'])
        neighbors = subcat_index.get(key, [])
        # Find position of this note in the subcat list
        nids_in_sub = [n for _, n in neighbors]
        try:
            idx = nids_in_sub.index(note['nid'])
        except ValueError:
            idx = None

        if idx is not None and len(neighbors) > 1:
            # Pick up to FALLBACK_SAME_SUB nearest neighbors
            candidates = []
            for offset in [1, -1, 2, -2, 3, -3]:
                j = idx + offset
                if 0 <= j < len(neighbors):
                    candidates.append(neighbors[j][1])
                if len(candidates) >= FALLBACK_SAME_SUB:
                    break
            chosen = candidates[:FALLBACK_SAME_SUB]

    note['new_related'] = chosen

# ─── Write back ──────────────────────────────────────────────────────────────
print('Writing related_nids...')
written = 0
for note in notes:
    new_rel = note.get('new_related', [])
    with open(note['fpath']) as f:
        data = json.load(f)
    if isinstance(data, list):
        continue
    old_rel = data.get('related_nids', [])
    # Merge: new first, then any existing valid links, cap at MAX_RELATED
    existing_valid = [n for n in old_rel if n in nid_to_note]
    merged = list(dict.fromkeys(new_rel + existing_valid))[:MAX_RELATED]
    if merged != old_rel:
        data['related_nids'] = merged
        with open(note['fpath'], 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        written += 1

zero_after = sum(1 for n in notes if not n.get('new_related'))
print(f'\nWrote related_nids to {written} notes.')
print(f'Zero-related notes: {zero_before} → {zero_after}')

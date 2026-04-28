#!/usr/bin/env python3
"""
Pass 3: Strip bad fallback links and re-run clean keyword-only algorithm.

Problems with the previous pass:
  - Subcategory-neighbor fallback created 220 nonsense links
    (Legionella → H.pylori, Bordetella → Campylobacter, etc.)
  - Some keyword synonym groups were too broad (anti- prefix)

This pass:
  1. NO fallback mechanism - empty is better than wrong
  2. Tightened synonym groups (removed over-broad drug-class expansions)
  3. Writes only to notes where related_nids actually changes
"""
import json, glob, re, os

BASE = '/home/user/mrcem/data'
MAX_RELATED = 5

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
    # Too generic to be useful as a match keyword
    'injur', 'injury', 'injuries', 'trauma', 'fractur', 'wound',
    *[str(i) for i in range(10)],
}

SYNONYM_GROUPS = [
    # Organ systems
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
    # Specific clinical clusters (tight synonyms only)
    ('fluclox', 'staphy', 'meticil'),          # flucloxacillin ↔ staphylococci
    ('flumazen', 'benzo', 'diazep', 'lorazep'), # flumazenil ↔ benzodiazepines
    ('nalox', 'opioi', 'heroi', 'morph', 'opiat'), # naloxone ↔ opioids
    ('oseltam', 'influenz'),                    # oseltamivir ↔ influenza (tight)
    ('seizure', 'epilep', 'convul', 'status'),  # seizures
    ('depress', 'antidepress', 'SSRI', 'TCA'),  # depression
    ('anaesth', 'sedati', 'analges'),           # anaesthesia
]

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


print('Loading notes...')
notes = []

for fpath in glob.glob(f'{BASE}/**/*.json', recursive=True):
    fname = os.path.basename(fpath)
    if fname.startswith('_'): continue
    with open(fpath) as f:
        raw = json.load(f)
    if isinstance(raw, list): continue
    nid = raw.get('nid', '')
    if not nid: continue
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

print('Building indexes...')
kw_index = {}
for note in notes:
    for kw in note['keywords']:
        kw_index.setdefault(kw, set()).add(note['nid'])

prefix_index = {}
for note in notes:
    if len(note['title_prefix']) >= 4:
        prefix_index.setdefault(note['title_prefix'], set()).add(note['nid'])


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

print('Computing related notes...')
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
        if not b: continue
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
        if len(chosen) >= MAX_RELATED: break
        chosen.append(nid)
    for _, nid in same_cat_diff_sub:
        if len(chosen) >= MAX_RELATED: break
        if nid not in chosen:
            chosen.append(nid)
    for _, nid in same_sub:
        if len(chosen) >= MAX_RELATED: break
        if nid not in chosen:
            chosen.append(nid)
        if nid_to_note[nid]['title_prefix'] != note['title_prefix']:
            break

    note['new_related'] = chosen


# ─── Manual curated overrides for high-value notes with 0 keyword links ──────
# These are clinically obvious connections the keyword algorithm can't find.
# Format: nid → [list of related nids]
# Only applied when keyword algorithm gives 0 results.
MANUAL_OVERRIDES = {
    # Bacteriology organisms → related infections/drugs in other categories
    '1_167':  ['1_2895', '2_175',  '2_466'],     # Legionella → Salmonella, C.diff, E.coli (all gram-neg)
    '1_240':  ['2_1430', '1_297',  '2_1439'],    # Bordetella → Croup, Streptococci, Scarlet fever (resp. infections)
    '1_44':   ['2_548',  '2_1460', '1_2895'],    # Campylobacter → Gastroenteritis, Hirschsprung, Salmonella
    '1_293':  ['2_737',  '1_2897', '2_299'],     # S.aureus → Staphylococci overview, S.epid, TSS

    # Virology → related conditions/drugs
    '1_151':  ['1_232',  '2_1430', '2_1261'],    # Influenza → Parainfluenza, Croup, Bronchiolitis
    '1_232':  ['1_151',  '2_1430', '1_269'],     # Parainfluenza → Influenza, Croup, Rhinovirus
    '1_269':  ['1_232',  '1_151',  '2_1261'],    # Rhinovirus → Parainfluenza, Influenza, Bronchiolitis

    # Pharmacology isolated drugs → indications
    '1_155':  ['2_2021', '2_2443', '1_326'],     # Inotropes → AVB, AKI intro, Types of shock
    '1_124':  ['1_155',  '1_317',  '2_2443'],    # Hartmann's → Inotropes, Vasopressors, AKI
    '1_317':  ['1_155',  '1_124',  '1_326'],     # Vasopressors → Inotropes, Hartmann's, Shock
    '1_20':   ['2_2114', '2_1525', '2_460'],     # Antiemetics → Metoclopramide, Triptans, Paracetamol OD
    '1_187':  ['1_160',  '2_406',  '2_525'],     # Mannitol → ICP, Idiopathic IH, Intracranial VT

    # Anatomy → relevant clinical notes
    '1_123':  ['1_179',  '1_40',   '1_280'],     # Carpal tunnel → Lumbricals, Brachialis, Shoulder
    '1_179':  ['1_123',  '1_40',   '1_280'],     # Lumbricals → Carpal tunnel, Brachialis, Shoulder
    '1_243':  ['1_270',  '1_314',  '1_2466'],    # Pleura → Ribs, Vertebral column, Preoxygenation
    '1_228':  ['1_236',  '1_319',  '1_324'],     # Ovary → Penis, Vas deferens, Ureters (pelvic anatomy)
    '1_236':  ['1_228',  '1_319',  '1_324'],     # Penis → Ovary, Vas deferens, Ureters

    # Immunology/infectious disease — important zero-link notes
    '1_16':   ['1_141',  '1_2930', '1_2929', '1_2932'],  # Anaphylaxis → Hypersensitivity, Normal immune resp, Immunoglobulins, Acute phase proteins
    '1_68':   ['1_2932', '1_2930', '1_141'],   # CRP → Acute phase proteins, Normal immune, Hypersensitivity
    '1_146':  ['1_56',   '1_190',  '1_222'],   # Incubation periods → Chickenpox, Measles, Norovirus
}

# Apply manual overrides only to notes with 0 keyword results
for note in notes:
    if not note['new_related'] and note['nid'] in MANUAL_OVERRIDES:
        note['new_related'] = [n for n in MANUAL_OVERRIDES[note['nid']]
                               if n in nid_to_note]


print('Writing related_nids...')
written = 0
zero_count = 0
for note in notes:
    new_rel = note.get('new_related', [])
    if not new_rel:
        zero_count += 1
    with open(note['fpath']) as f:
        data = json.load(f)
    if isinstance(data, list): continue
    old_rel = data.get('related_nids', [])
    if new_rel != old_rel:
        data['related_nids'] = new_rel
        with open(note['fpath'], 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        written += 1

print(f'Wrote related_nids to {written} notes.')
print(f'Notes with 0 related_nids: {zero_count} / {len(notes)}')

#!/usr/bin/env python3
"""
Build a comprehensive related_nids network for all MRCEM notes.

Algorithm:
 1. Extract keywords from each note title (5-char prefix stemming + synonym expansion)
 2. Build reverse index: keyword → [nid list]
 3. Score each candidate pair:
    - base score = shared keyword count
    - bonus ×2 if different categories (cross-category links most valuable)
    - bonus ×1.5 if same category but different subcategory
    - bonus ×2 for notes sharing the same title prefix (same condition, series)
 4. Write top 5 related nids to each note (cross-category preferred)

Preserves any existing related_nids that are still valid.
"""
import json, glob, re, os

BASE = '/home/user/mrcem/data'
MAX_RELATED = 5

# ─── Stop words ─────────────────────────────────────────────────────────────
STOPWORDS = {
    'a','an','the','and','or','in','of','to','from','with','for','at','by',
    'as','on','is','are','was','were','has','have','had','be','been','being',
    'its','it','this','that','these','those','which','who','not','but','if',
    # Generic medical qualifiers
    'basic','introduction','overview','summary','features','management',
    'causes','cause','investigation','investigations','diagnosis','treatment',
    'presentations','presentation','clinical','history','complications',
    'complication','classification','definition','aetiology','types','type',
    'pathophysiology','mechanism','action','adverse','effects','side','very',
    'criteria','syndrome','disease','disorder','condition','pathology',
    'versus','comparison','vs','assessment','approach','review','update',
    'acute','chronic','primary','secondary','general','common','rare',
    # Single-letter / numbers
    *[str(i) for i in range(10)],
}

# ─── Medical synonym groups (normalise to a single representative token) ─────
# Each tuple: all variants map to the same "canonical" stem
SYNONYM_GROUPS = [
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
]

# Build synonym lookup: token → canonical (first in group)
SYNONYM_MAP = {}
for group in SYNONYM_GROUPS:
    canonical = group[0]
    for token in group:
        SYNONYM_MAP[token] = canonical

PREFIX_LEN = 5

def get_keywords(title):
    """Extract normalised keyword set from a title string."""
    title = re.sub(r'<[^>]+>', '', title)          # strip HTML
    title = title.lower()
    title = re.sub(r"[''']s?\b", '', title)          # remove possessives
    words = re.split(r'[^a-z]+', title)
    keywords = set()
    for word in words:
        if len(word) < 3 or word in STOPWORDS:
            continue
        # Prefix stem for longer words
        stem = word[:PREFIX_LEN] if len(word) >= PREFIX_LEN else word
        # Synonym normalisation
        stem = SYNONYM_MAP.get(stem, stem)
        if stem not in STOPWORDS:
            keywords.add(stem)
    return keywords

def get_title_prefix(title):
    """Return the first word/phrase before ':' or '(' for series detection."""
    title = re.sub(r'<[^>]+>', '', title).strip()
    # Take text before first ':' or '('
    m = re.match(r'^([^:(]+)', title)
    return m.group(1).strip().lower() if m else title.lower()


# ─── Load all notes ──────────────────────────────────────────────────────────
print('Loading notes...')
notes = []  # list of dicts

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

    # Extract category/subcategory from HTML
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


# ─── Build reverse index ────────────────────────────────────────────────────
print('Building keyword index...')
kw_index = {}  # keyword → set of nids
for note in notes:
    for kw in note['keywords']:
        kw_index.setdefault(kw, set()).add(note['nid'])

# Build title-prefix index
prefix_index = {}  # prefix → set of nids
for note in notes:
    if len(note['title_prefix']) >= 4:
        prefix_index.setdefault(note['title_prefix'], set()).add(note['nid'])


# ─── Score and select related notes ─────────────────────────────────────────
print('Computing related notes...')

def score_pair(a, b):
    """Score relevance of note b as a related note for note a."""
    if a['nid'] == b['nid']:
        return 0
    shared = a['keywords'] & b['keywords']
    if not shared:
        # Still check title prefix match
        if (len(a['title_prefix']) >= 4 and
                a['title_prefix'] == b['title_prefix']):
            shared = {'__prefix__'}
        else:
            return 0

    score = len(shared)

    # Cross-category bonus (most valuable)
    if a['cat'] != b['cat']:
        score *= 2.5
    # Same category, different subcategory bonus
    elif a['sub'] != b['sub']:
        score *= 1.5

    # Same title prefix bonus (series: "Epilepsy: classification", "Epilepsy: treatment")
    if (len(a['title_prefix']) >= 4 and
            a['title_prefix'] == b['title_prefix'] and
            a['nid'] != b['nid']):
        score += 2

    return score

new_related_counts = {0: 0, '1-2': 0, '3-5': 0, '6+': 0}

for note in notes:
    # Find candidates: union of notes sharing any keyword
    candidate_nids = set()
    for kw in note['keywords']:
        candidate_nids |= kw_index.get(kw, set())
    # Also add title-prefix matches
    if len(note['title_prefix']) >= 4:
        candidate_nids |= prefix_index.get(note['title_prefix'], set())
    candidate_nids.discard(note['nid'])

    # Score all candidates
    scored = []
    for cnid in candidate_nids:
        b = nid_to_note.get(cnid)
        if not b:
            continue
        s = score_pair(note, b)
        if s > 0:
            scored.append((s, cnid))

    scored.sort(key=lambda x: -x[0])

    # Take top MAX_RELATED, preferring cross-category/subcategory
    chosen = []
    cross_cat = [(s, n) for s, n in scored
                 if nid_to_note[n]['cat'] != note['cat']]
    same_cat_diff_sub = [(s, n) for s, n in scored
                         if nid_to_note[n]['cat'] == note['cat']
                         and nid_to_note[n]['sub'] != note['sub']]
    same_sub = [(s, n) for s, n in scored
                if nid_to_note[n]['sub'] == note['sub']
                and nid_to_note[n]['cat'] == note['cat']]

    # Priority: cross-cat first, then same-cat-diff-sub, then same-sub
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
        # Same-subcategory: only include series (same title prefix)
        # break early for same-sub non-series
        if nid_to_note[nid]['title_prefix'] != note['title_prefix']:
            break

    # Track stats
    n = len(chosen)
    if n == 0:
        new_related_counts[0] += 1
    elif n <= 2:
        new_related_counts['1-2'] += 1
    elif n <= 5:
        new_related_counts['3-5'] += 1
    else:
        new_related_counts['6+'] += 1

    note['new_related'] = chosen


# ─── Write back to JSON files ────────────────────────────────────────────────
print('Writing related_nids to files...')
written = 0
for note in notes:
    new_rel = note.get('new_related', [])
    with open(note['fpath']) as f:
        data = json.load(f)
    if isinstance(data, list):
        continue
    old_rel = data.get('related_nids', [])
    # Merge with any existing valid related_nids
    existing_valid = [n for n in old_rel if n in nid_to_note]
    merged = list(dict.fromkeys(new_rel + existing_valid))[:MAX_RELATED]
    if merged != old_rel:
        data['related_nids'] = merged
        with open(note['fpath'], 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        written += 1

print(f'\nWrote related_nids to {written} notes.')
print(f'Distribution: 0={new_related_counts[0]}, '
      f'1-2={new_related_counts["1-2"]}, '
      f'3-5={new_related_counts["3-5"]}, '
      f'6+={new_related_counts["6+"]}')
